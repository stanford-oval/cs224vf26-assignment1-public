"""The single LLM primitive: ``f(task, context) -> validated JSON`` (Methodology §3).

Every executor call is one ephemeral ``codex exec`` against the docuset Azure
provider (gpt-5.4), with ``--output-schema`` forcing the FINAL message to schema-
conformant JSON. The orchestrator owns control flow; codex never decides the next
step and never holds the belief state.

Two execution modes:
  * ``reason``   — read-only sandbox, no web. For PRIOR / EVALUATE (pure reasoning).
  * ``research`` — workspace-write + network + codex's native web_search. For
                   GROUND / EXPLORE / VERIFY (must touch real sources).

Cost is read back as REAL USD from codex's own rollout for the per-task cwd
(the baseline.py method), with a ``tokens used`` transcript fallback.

Self-contained: no repo imports, mirrors baseline.py so it can run standalone.
"""
from __future__ import annotations

import glob
import json
import os
import re
import signal
import subprocess
import threading
import time
from pathlib import Path

from . import config

# Price table + secrets-file path live in config.py (single source of truth). Kept as module-level
# aliases so existing references (and `from .codex_exec import DEFAULT_ENV`) keep working.
_MODEL_RATES_M = config.MODEL_RATES_M
_DEFAULT_RATES_M = config.DEFAULT_RATES_M


def rates_for(model: str | None) -> tuple[float, float]:
    """(input, output) USD per token for `model`."""
    ri, ro = _MODEL_RATES_M.get(model or "", _DEFAULT_RATES_M)
    return ri / 1_000_000, ro / 1_000_000


def rate_for(model: str | None) -> float:
    """Blended $/token fallback (~30% input / 70% output) for the transcript-only path."""
    ri, ro = rates_for(model)
    return 0.3 * ri + 0.7 * ro
DEFAULT_ENV = config.ENV_FILE

PROVIDER_KEY = "OPENAI_API_KEY"     # env var the provider reads for auth
# Stanford LiteLLM proxy (OpenAI-compatible), same endpoint as ~/.codex/config.toml's `stanford`
# provider. Serves gpt-5.x (+ -codex) and text-embedding-3-large; wire_api "responses" is supported.
PROVIDER = [
    "model_provider=stanford",
    'model_providers.stanford.name="Stanford Azure OpenAI"',
    'model_providers.stanford.base_url="https://azureopenai.genie.stanford.edu/v1"',
    f'model_providers.stanford.env_key="{PROVIDER_KEY}"',
    'model_providers.stanford.wire_api="responses"',
]

_TOKENS_RE = re.compile(r"tokens\s+used\s*\n\s*([\d,]+)", re.IGNORECASE)


def load_env(path: str, env: dict) -> None:
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            # .env is authoritative — override any (possibly stale) ambient value so the codex
            # subprocess gets the key from .env, not a budget-exhausted one exported in the shell.
            env[k.strip()] = v.strip().strip('"').strip("'")


def _session_cwd(f: str):
    try:
        obj = json.loads(open(f).readline())
        if obj.get("type") == "session_meta":
            return (obj.get("payload") or {}).get("cwd")
    except Exception:
        return None


def spent_usd(run_dir, since: float = 0.0) -> float:
    """Real USD billed for the codex session whose cwd == ``run_dir`` (baseline.py).

    ``since`` (an epoch seconds floor on the rollout's mtime) matters only when several tasks share
    one cwd — the artifact executor runs every task in the same workspace, so without it a task that
    produced no rollout of its own would be charged the PREVIOUS task's bill. Task dirs are unique
    per task, so the default (0.0) is exactly the old behaviour."""
    target = str(Path(run_dir).resolve())
    files = glob.glob(os.path.expanduser("~/.codex/sessions/**/rollout-*.jsonl"), recursive=True)
    ours = [f for f in files
            if (not since or os.path.getmtime(f) >= since)
            and (c := _session_cwd(f)) and str(Path(c).resolve()) == target]
    if not ours:
        return 0.0
    roll = max(ours, key=os.path.getmtime)
    billed_in = billed_out = 0
    model = None
    try:
        for line in open(roll):
            if model is None and '"model"' in line:
                m = re.search(r'"model"\s*:\s*"([^"]+)"', line)
                if m:
                    model = m.group(1)
            if '"token_count"' not in line:
                continue
            try:
                info = (json.loads(line).get("payload") or {}).get("info") or {}
                tu = info.get("total_token_usage")
            except ValueError:
                tu = None
            if isinstance(tu, dict):        # total_token_usage is cumulative — keep the last
                inp = tu.get("input_tokens", 0) - tu.get("cached_input_tokens", 0)
                out = tu.get("output_tokens", 0)
                if (inp + out) > 0:
                    billed_in, billed_out = max(0, inp), out
    except OSError:
        return 0.0
    ri, ro = rates_for(model)              # real per-model input/output rates
    return billed_in * ri + billed_out * ro


def _tokens_from_transcript(text: str) -> int:
    m = _TOKENS_RE.findall(text or "")
    if not m:
        return 0
    try:
        return int(m[-1].replace(",", ""))
    except ValueError:
        return 0


class CodexError(RuntimeError):
    pass


def run_task(task_dir, prompt, schema, *, retries: int = 2, **kw) -> tuple[dict, float]:
    """Run a codex task with retries on transient failure — the proxy occasionally drops a call (fast
    5xx / empty output). A soft failure returns (None, usd); retry up to `retries` times, accumulating
    the (usually ~0) cost of failed attempts. Hard config errors (CodexError) propagate, not retried."""
    total = 0.0
    for _ in range(retries + 1):
        data, usd = _run_task_once(task_dir, prompt, schema, **kw)
        total += (usd or 0.0)
        if data is not None:
            return data, total
    return None, total


def _run_task_once(task_dir: Path, prompt: str, schema: dict, *, mode: str = "research",
             model: str = config.RUN_MODEL, env_file: str = DEFAULT_ENV,
             reasoning: str = config.REASONING, timeout: int = 1800,
             usd_cap: float | None = None, cwd=None) -> tuple[dict, float]:
    """Run one schema-constrained codex task. Returns (validated_json, usd_spent).

    ``usd_cap`` (if set) installs a watchdog that hard-kills the task once its own
    rollout spend crosses the cap — the per-task budget backstop (baseline.py pattern).

    ``cwd`` (default: the task dir) is where codex actually RUNS — in workspace-write mode this is
    the only directory it may write to. The artifact executor points it at the run's git workspace
    so the agent can build files that persist; control files (prompt / schema / transcript / the
    JSON result) still live in the task dir, written by the codex CLI itself and therefore outside
    the sandbox. Raises CodexError if codex produced no parseable schema output.
    """
    task_dir = Path(task_dir).resolve()       # codex --cd MUST be absolute (PROJECT_NOTES gotcha)
    task_dir.mkdir(parents=True, exist_ok=True)
    work = Path(cwd).resolve() if cwd else task_dir
    work.mkdir(parents=True, exist_ok=True)
    # Only meaningful when the cwd is SHARED across tasks (the workspace); see spent_usd.
    since = (time.time() - 5.0) if cwd else 0.0
    schema_f = task_dir / "schema.json"
    out_f = task_dir / "out.json"
    schema_f.write_text(json.dumps(schema), encoding="utf-8")
    (task_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    load_env(env_file, env)
    if PROVIDER_KEY not in env:
        raise CodexError(f"{PROVIDER_KEY} not in env or {env_file}; codex will fail auth.")

    cmd = ["codex", "exec", "--skip-git-repo-check", "--cd", str(work)]
    for ov in PROVIDER:
        cmd += ["-c", ov]
    # web_search is INCOMPATIBLE with reasoning.effort=minimal (Azure 400) — research tasks always
    # use web_search, so floor them at 'low'. reason-mode tasks may still run 'minimal'.
    eff = reasoning
    if mode == "research" and eff == "minimal":
        eff = "low"
    if eff:
        cmd += ["-c", f"model_reasoning_effort={eff}"]   # default 'low' (cheaper/faster)
    if mode == "research":
        cmd += ["-c", "sandbox_workspace_write.network_access=true",
                "-c", "tools.web_search=true",
                "-c", "shell_environment_policy.inherit=all",
                "--sandbox", "workspace-write"]
    else:  # reason
        cmd += ["--sandbox", "read-only"]
    # Feed the prompt via STDIN ("-"), not as an argv element — large prompts (full
    # draft / many-claim digests) overflow the ~128KB argv limit → "Argument list too
    # long" (baseline.py pattern).
    cmd += ["-m", model, "--color", "never",
            "--output-schema", str(schema_f),
            "--output-last-message", str(out_f), "-"]

    transcript = task_dir / "transcript.log"
    killed_for_budget = {"v": False}
    with open(task_dir / "prompt.txt", encoding="utf-8") as stdin, \
            open(transcript, "w", encoding="utf-8") as tf:
        proc = subprocess.Popen(cmd, stdin=stdin, stdout=tf,
                                stderr=subprocess.STDOUT, cwd=str(work), env=env,
                                start_new_session=True)
        stop = threading.Event()

        def watch():
            while usd_cap and not stop.wait(5.0):
                if spent_usd(work, since) >= usd_cap:
                    killed_for_budget["v"] = True
                    try:
                        pg = os.getpgid(proc.pid)
                        os.killpg(pg, signal.SIGTERM)
                        time.sleep(3)
                        os.killpg(pg, signal.SIGKILL)
                    except (ProcessLookupError, OSError):
                        pass
                    return

        if usd_cap:
            threading.Thread(target=watch, daemon=True).start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            proc.wait()
        stop.set()

    usd = spent_usd(work, since)
    if usd <= 0.0:                      # rollout-by-cwd missed; fall back to transcript
        usd = _tokens_from_transcript(transcript.read_text(encoding="utf-8", errors="replace")) \
            * rate_for(model)           # price the fallback at the model that actually ran

    # Soft failures return (None, usd) so the orchestrator still CHARGES the spend —
    # a task killed at its usd_cap cost real money even though it produced no JSON.
    if not out_f.exists():
        return None, usd
    try:
        return json.loads(out_f.read_text(encoding="utf-8")), usd
    except json.JSONDecodeError:
        return None, usd
