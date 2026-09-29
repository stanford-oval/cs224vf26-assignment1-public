"""Driving and dissecting GRILL, the belief-ledger literature agent.

GRILL lives at ``report_formation/graph-search-sliders``. Its control loop is
deterministic Python; only the executors call a model. That split is what makes
it teachable: you can run the *entire* state machine -- provenance gate, screen,
deep test, binning, corrective directions, synthesis -- at zero cost, and then
spend money only on the part that actually reads the literature.

Three ways to use it here, cheapest first:

``Ledger`` directly        drive the state machine by hand. No model, no cost.
``run_grill(..., mock=)``  the real orchestrator with a stubbed executor. $0.
``run_grill(...)``         a real run. Costs real USD, needs the codex CLI.

Vocabulary, because the docs and the code disagree: a *Direction* is an open
question on the frontier, a *Hypothesis* is a candidate claim (the write-ups
call these "claims"), and *Evidence* is a sourced observation attached to one.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

def _vendored(name: str, fallback: str) -> Path:
    """The in-repo copy if it is there, else the original checkout."""
    here = Path(__file__).resolve().parents[2] / "vendor" / name
    return here if here.exists() else Path(fallback)


GRILL_ROOT = Path(
    os.environ.get(
        "GRILL_ROOT",
        _vendored("grill", "/mnt/data/oval/report_formation/graph-search-sliders"),
    )
)

#: The model every executor runs on, routed through the Stanford LiteLLM proxy,
#: which the codex CLI reaches over the `responses` wire API.
#:
#: **Not the same model SLIDERS uses, and the difference is measured.** GRILL
#: does not make a single structured call -- it drives `codex`, an agentic CLI
#: with shell and web-search tools, and the model has to decide when to stop
#: using them. On the identical INIT prompt, schema and endpoint:
#:
#:     gpt-5.6-terra       5s,   0 shell calls, 13,648 tokens, valid output
#:     gemini-3.8-flash    timed out at 300s, 163 shell calls, no output
#:
#: Gemini Flash never terminates the loop. Given a directory with something in
#: it, it explores; given an empty one, it issued `/bin/bash -lc true` 160
#: times. SLIDERS runs happily on Gemini because it makes one structured call
#: per chunk and never hands the model a tool.
#:
#: The course nevertheless runs both systems on gemini-3.8-flash, so that the
#: comparison between them is on one model. If a live GRILL run stalls in
#: INIT with a growing count of shell calls and no ledger, that is this
#: failure; set GRILL_MODEL=gpt-5.6-terra and rerun.
DEFAULT_MODEL = os.environ.get("GRILL_MODEL", "gemini-3.8-flash")

#: Where run directories go. **Outside the project tree, deliberately.**
#:
#: GRILL gives every codex task a shell, rooted at that task's directory. If the
#: run directory sits inside your repository, the task can walk up out of it and
#: read the whole checkout -- and it will. Measured on a run placed inside this
#: project, the INIT task whose entire job is to list the question's required
#: output fields instead ran 54 shell commands: a ``find`` over the repo, an
#: ``rg`` for its own schema key, and a read of all 20 canned outputs from an
#: earlier stubbed run that happened to be on disk. It burned 345,704 tokens and
#: its answer was contaminated by the fixture it found.
#:
#: Keeping runs outside the tree is not tidiness. It is what stops the agent
#: from reading its own answer key.
RUNS_ROOT = Path(os.environ.get("GRILL_RUNS", str(Path.home() / ".grill-runs")))


def run_dir_for(name: str, root: Path | str = RUNS_ROOT) -> Path:
    """A run directory outside any source tree. See ``RUNS_ROOT``."""
    p = Path(root) / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _warn_if_inside_repo(run_dir: Path) -> str | None:
    """Return a warning if ``run_dir`` sits under a directory holding source."""
    skip = {Path("/"), Path("/tmp"), Path("/var"), Path("/var/tmp"), Path.home()}
    for parent in run_dir.resolve().parents:
        if parent in skip:
            continue
        markers = [m for m in (".git", "pyproject.toml", "setup.py", "src")
                   if (parent / m).exists()]
        if markers:
            return (
                f"run_dir is inside {parent} (has {markers[0]}), which holds source. "
                "Codex tasks get a shell and will read it. Use run_dir_for(name)."
            )
    return None


def add_grill_to_path(root: Path | str = GRILL_ROOT) -> Path:
    """Make ``import src.ledger`` work. GRILL is not a pip-installable package."""
    root = Path(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def grill_available(root: Path | str = GRILL_ROOT) -> dict[str, Any]:
    """What can actually run here -- report it honestly before spending."""
    root = Path(root)
    # GRILL reads whatever GSS_ENV_FILE names, falling back to its own root.
    # setup_credentials() points that at the file it writes under runs/.
    env_file = Path(os.environ.get("GSS_ENV_FILE") or (root / ".env"))
    env_keys: set[str] = set()
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                env_keys.add(line.split("=", 1)[0].strip())

    codex = subprocess.run(
        ["which", "codex"], capture_output=True, text=True
    ).stdout.strip()

    return {
        "root_exists": root.exists(),
        "importable": (root / "src" / "ledger.py").exists(),
        "codex_cli": codex or None,
        "env_file": str(env_file) if env_file.exists() else None,
        "env_keys": sorted(env_keys),
        "can_run_offline": (root / "src" / "ledger.py").exists(),
        "can_run_live": bool(codex) and "OPENAI_API_KEY" in env_keys,
        "model": DEFAULT_MODEL,
    }


# --------------------------------------------------------------------------
# Live runs
# --------------------------------------------------------------------------


def run_grill(
    question: str,
    run_dir: str | Path,
    *,
    budget: float = 25.0,
    k: int = 3,
    max_rounds: int = 4,
    concurrency: int = 4,
    model: str | None = DEFAULT_MODEL,
    extra_args: Sequence[str] = (),
    steer: str | None = None,
    root: Path | str = GRILL_ROOT,
    timeout: int = 5400,
    echo: bool = True,
) -> "GrillRun":
    """Shell out to ``python3 -m src.cli``. This spends real money.

    ``steer`` is free text for the researcher-side steering channel. It is
    written to the run's inbox before launch, and GRILL drains it at the
    first round boundary, translating it into directions, constraints and
    assumptions with its own classifier (see :func:`steer_from_text`). More
    can be appended while the run is going with :func:`send_steer`.

    Two things about ``budget`` that the flag's name does not tell you, both
    measured on this corpus rather than inferred:

    **It is not a hard cap.** The orchestrator debits a phase after its tasks
    return, and INIT launches GROUND for every key term in parallel at
    ``ground_task_usd`` (default $2.00) each. With four terms that is $8 of
    intent committed before a single dollar is checked. A run capped at $3.00
    was observed to bill $6.06, all of it in INIT, and then stop with nothing
    screened. Size the budget so INIT alone fits: roughly
    ``2 * ground_task_usd * n_key_terms`` before any research happens.

    **The figures are inflated for Gemini.** GRILL prices a model missing from
    its rate table at the full GPT-5 rate. Gemini Flash is roughly an order of
    magnitude cheaper, so the accounting runs about 10x high. The two effects
    push opposite ways and do not cancel: the cap is soft, and the number it is
    compared against is too big. For ``gemini-3.8-flash`` a nominal ``budget``
    of $20-25 buys a few real dollars of work and is enough to get past INIT
    into EXPLORE. $5 is not.
    """
    root = Path(root)
    run_dir = Path(run_dir).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    warning = _warn_if_inside_repo(run_dir)
    if warning and echo:
        print(f"WARNING: {warning}", flush=True)

    qfile = run_dir / "question.txt"
    qfile.write_text(question)

    cmd = [
        sys.executable,
        "-m",
        "src.cli",
        "--question-file",
        str(qfile),
        "--run-dir",
        str(run_dir),
        "--budget",
        str(budget),
        "-K",
        str(k),
        "--max-rounds",
        str(max_rounds),
        "--concurrency",
        str(concurrency),
    ]
    if model:
        cmd += ["--model", model]
    inbox = steer_inbox_path(run_dir)
    cmd += ["--steer-inbox", str(inbox)]
    if steer:
        send_steer(steer, run_dir)
    cmd += list(extra_args)

    if echo:
        print("$", " ".join(cmd), flush=True)
    proc = subprocess.run(
        cmd, cwd=str(root), capture_output=True, text=True, timeout=timeout
    )
    (run_dir / "cli_stdout.log").write_text(proc.stdout)
    (run_dir / "cli_stderr.log").write_text(proc.stderr)
    if echo:
        print(proc.stdout[-4000:])
        if proc.returncode != 0:
            print("--- stderr tail ---")
            print(proc.stderr[-3000:])
    return GrillRun(run_dir)


# --------------------------------------------------------------------------
# Steering in plain language
# --------------------------------------------------------------------------
#
# GRILL is steered by a human writing sentences, not by editing prompts. A
# message goes into a JSON inbox next to the run; at the next round boundary
# the orchestrator reads it, asks a model to translate it into the fields the
# ledger understands -- new directions, scope constraints, assumptions to take
# as given, directions to drop or boost, verdicts on named hypotheses -- and
# applies those. The translation is an ordinary chat call, so it can be run on
# its own, which is what `steer_from_text` does: it shows what GRILL would make
# of a sentence before anything is spent on it.
#
# Two properties worth knowing. Steering is context, not evidence: nothing a
# human writes can pass the provenance gate or become a claim. And a message
# that is a question ("did you find anything on X?") is answered from the
# ledger rather than turned into a research direction; that split exists
# because before it did, questions cost budget.


def steer_inbox_path(run_dir: str | Path) -> Path:
    return Path(run_dir) / "steer_inbox.json"


def send_steer(text: str, run_dir: str | Path) -> Path:
    """Append one free-text message to a run's inbox. Safe while the run is live."""
    import json  # noqa: PLC0415

    path = steer_inbox_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    events: list = []
    if path.exists():
        try:
            data = json.loads(path.read_text() or "[]")
            events = data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            events = []
    events.append({"nl": text.strip()})
    path.write_text(json.dumps(events, indent=2) + "\n")
    return path


def steer_from_text(
    text: str,
    run: "GrillRun | None" = None,
    *,
    model: str | None = None,
    env_file: str | None = None,
) -> dict:
    """GRILL's own reading of a steering message, without launching a run.

    Uses the same prompt and context the orchestrator hands to
    ``classify.nl_to_steer``: the open directions and recent hypotheses of
    ``run``, so "drop the variant-position direction" can resolve to an id.
    Returns the structured steer event as a dict.

    GRILL's own function swallows every error and returns ``{}``, which a live
    run then treats as "add the whole message as one direction". That is the
    right behaviour mid-run and the wrong one in a notebook, so this version
    makes the call itself and raises with the actual cause: no credentials,
    a rejected key, or a reply that was not JSON. An empty dict from here
    means the model read the message and found nothing to act on.
    """
    import json  # noqa: PLC0415
    import re  # noqa: PLC0415

    add_grill_to_path()
    from src import classify, config  # noqa: PLC0415
    from src.codex_exec import load_env  # noqa: PLC0415

    env_file = env_file or os.environ.get("GSS_ENV_FILE") or str(Path(GRILL_ROOT) / ".env")
    env: dict = {}
    load_env(env_file, env)
    base = config.openai_base(env.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_BASE_URL"))
    key = env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not base or not key:
        raise RuntimeError(
            f"no credentials for the steer classifier: {env_file} has no "
            f"OPENAI_BASE_URL/OPENAI_API_KEY. Run the credentials cell first."
        )

    dirs: list = []
    hyps: list = []
    if run is not None:
        try:
            dirs = [(d["id"], d["question"]) for d in run.directions_table()
                    if str(d.get("status", "open")).lower() == "open"][:40]
            hyps = [(h["id"], h["text"]) for h in run.hypotheses_table()][-25:]
        except Exception:  # noqa: BLE001 - context is optional
            dirs, hyps = [], []

    from openai import OpenAI  # noqa: PLC0415

    client = OpenAI(base_url=base, api_key=key)
    resp = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[{"role": "system", "content": classify._SYS},
                  {"role": "user", "content": f"{classify._ctx(dirs, hyps)}\n\nMESSAGE:\n{text}\n\n"
                                              "Return the JSON steer event."}],
    )
    raw = (resp.choices[0].message.content or "").strip()
    cleaned = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"the classifier ({model or DEFAULT_MODEL}) did not return JSON; a live run "
            f"would fall back to one direction. Reply began: {raw[:200]!r}"
        ) from e
    if not isinstance(obj, dict):
        raise RuntimeError(f"the classifier returned {type(obj).__name__}, not an object: {raw[:200]!r}")
    return obj


def steer_intent(text: str, *, model: str | None = None, env_file: str | None = None) -> dict:
    """Instruction or question? The first thing GRILL decides about a message."""
    add_grill_to_path()
    from src import classify  # noqa: PLC0415

    env_file = env_file or os.environ.get("GSS_ENV_FILE") or str(Path(GRILL_ROOT) / ".env")
    return classify.classify_intent(text, env_file, model or DEFAULT_MODEL)


def apply_steer_offline(text: str, run: "GrillRun", *, model: str | None = None,
                        top: int = 6, show: bool = True) -> dict:
    """What a steer does to the belief state, without spending a round.

    Translates ``text`` with GRILL's classifier, applies the event to a *copy*
    of the run's ledger with the same ``SteerEvent.apply_to`` the orchestrator
    uses, and shows the frontier before and after, ranked the way the
    allocator ranks it. Two things this shows that the translation alone does
    not: which existing directions were dropped or boosted, and where the new
    human direction lands in the queue. The allocator pins a human direction
    to promise 0.99 so it is funded in the next round, and the ranking here
    applies the same rule.

    What it cannot show is what the round would then *find*. That takes a live
    run. In ``"stub"`` mode the executors return canned output, so the ledger
    changes but the research does not.
    """
    import copy  # noqa: PLC0415

    add_grill_to_path()
    from src.ledger import Ledger  # noqa: PLC0415
    from src.steer import SteerEvent  # noqa: PLC0415

    def frontier(L):
        opens = list(L.open_directions())
        rows = []
        for d in opens:
            promise = 0.99 if getattr(d, "origin", "") == "human" else d.promise
            rows.append({"id": d.id, "promise": round(promise, 2),
                         "origin": getattr(d, "origin", "") or "agent",
                         "question": d.question_text})
        return sorted(rows, key=lambda r: -r["promise"])

    L = Ledger.from_json(copy.deepcopy(run.ledger_json))
    before = frontier(L)
    event = steer_from_text(text, run, model=model)
    applied = SteerEvent.from_dict(event).apply_to(L)
    after = frontier(L)
    out = {"event": event, "changes": list(applied.changes),
           "frontier_before": before, "frontier_after": after,
           "constraints": list(getattr(L, "constraints", []) or []),
           "assumptions": list(getattr(L, "assumptions", []) or [])}
    if show:
        print("GRILL's translation:")
        print(explain_steer(event))
        print("\napplied to the ledger:")
        for c in applied.changes or ["(no change)"]:
            print(f"  {c}")
        ids_before = {r["id"] for r in before}
        print(f"\nfrontier: {len(before)} open directions before, {len(after)} after. "
              f"Top {top}, as the allocator would rank them next round:")
        for r in after[:top]:
            tag = "NEW " if r["id"] not in ids_before else "    "
            print(f"  {tag}{r['id']:<5} {r['promise']:.2f} {r['origin']:<10} {r['question'][:70]}")
    return out


def explain_steer(event: dict) -> str:
    """The translated event, one line per thing GRILL would do."""
    if not event:
        return "  (nothing actionable: the model found no instruction in the message)"
    lines = []
    for d in event.get("directions_add") or []:
        lines.append(f"  + direction  (promise {d.get('promise', '?')})  {d.get('question_text', '')}")
        if d.get("rationale"):
            lines.append(f"               because: {d['rationale']}")
    for c in event.get("constraints") or []:
        lines.append(f"  | constraint {c}")
    for a in event.get("assumptions") or []:
        lines.append(f"  = assume     {a}")
    for i in event.get("directions_drop") or []:
        lines.append(f"  - drop       {i}")
    for i, pr in (event.get("directions_boost") or {}).items():
        lines.append(f"  ^ boost      {i} -> promise {pr}")
    for v in event.get("hypotheses_verdict") or []:
        lines.append(f"  ! verdict    {v.get('hypothesis_id')}: {v.get('verdict')}  {v.get('note', '')}")
    for i in event.get("hypotheses_unbin") or []:
        lines.append(f"  ~ unbin      {i}")
    for a in event.get("artifacts_request") or []:
        lines.append(f"  # artifact   [{a.get('kind')}] {a.get('spec')}")
    if event.get("budget_delta"):
        lines.append(f"  $ budget     {event['budget_delta']:+}")
    if event.get("control") and event["control"] != "continue":
        lines.append(f"  * control    {event['control']}")
    return "\n".join(lines) or "  (nothing actionable)"


# --------------------------------------------------------------------------
# A stub executor, so the control loop can be watched for free
# --------------------------------------------------------------------------


def install_stub_executor(
    responses: Callable[[str, str], dict] | dict[str, dict],
    root: Path | str = GRILL_ROOT,
) -> Callable[[], None]:
    """Replace GRILL's one LLM primitive with canned JSON. Returns an undo.

    Every executor funnels through ``codex_exec.run_task(task_dir, prompt,
    schema) -> (dict, usd)``. Patching that single function makes the whole
    orchestrator -- planning, allocation, screening, deep testing, convergence
    -- run offline at exactly $0, which is the only way to watch the control
    flow without a credit card.

    ``responses`` is either a dict keyed by task label, or a callable
    ``(label, prompt) -> dict``.
    """
    add_grill_to_path(root)
    import src.codex_exec as codex_exec  # noqa: PLC0415
    import src.executors as executors  # noqa: PLC0415

    original = executors.run_task

    def stub(task_dir, prompt, schema, **kw):
        label = re.sub(r"^\d+_", "", Path(task_dir).name)
        if callable(responses):
            out = responses(label, prompt)
        else:
            out = responses.get(label)
            if out is None:
                for key, val in responses.items():
                    if label.startswith(key):
                        out = val
                        break
        Path(task_dir).mkdir(parents=True, exist_ok=True)
        (Path(task_dir) / "prompt.txt").write_text(prompt)
        (Path(task_dir) / "out.json").write_text(json.dumps(out or {}, indent=2))
        return (out, 0.0)

    executors.run_task = stub
    codex_exec_run = codex_exec.run_task

    def undo() -> None:
        executors.run_task = original
        codex_exec.run_task = codex_exec_run

    return undo


# --------------------------------------------------------------------------
# Reading a finished run
# --------------------------------------------------------------------------


@dataclass
class GrillTask:
    """One LLM call, as it was written to disk."""

    n: int
    label: str
    path: Path
    subject: str = ""

    @property
    def prompt(self) -> str:
        p = self.path / "prompt.txt"
        return p.read_text() if p.exists() else ""

    @property
    def output(self) -> Any:
        p = self.path / "out.json"
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None

    @property
    def schema(self) -> Any:
        p = self.path / "schema.json"
        return json.loads(p.read_text()) if p.exists() else None


class GrillRun:
    """A completed (or in-progress) ``--run-dir``, opened for inspection."""

    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)

    # -- raw artifacts -----------------------------------------------------

    def _json(self, name: str) -> Any:
        p = self.run_dir / name
        return json.loads(p.read_text()) if p.exists() else None

    @property
    def ledger_json(self) -> dict | None:
        return self._json("ledger.json")

    @property
    def run_json(self) -> dict | None:
        return self._json("run.json")

    @property
    def answer(self) -> str:
        p = self.run_dir / "answer.md"
        return p.read_text() if p.exists() else ""

    @property
    def log(self) -> str:
        p = self.run_dir / "orchestrator.log"
        return p.read_text() if p.exists() else ""

    def ledger(self):
        """Rehydrate the real ``Ledger`` object, with all its methods."""
        add_grill_to_path()
        from src.ledger import Ledger  # noqa: PLC0415

        d = self.ledger_json
        if d is None:
            raise FileNotFoundError(f"no ledger.json in {self.run_dir}")
        return Ledger.from_json(d)

    @property
    def tasks(self) -> list[GrillTask]:
        out = []
        for p in sorted((self.run_dir / "tasks").glob("*")):
            if not p.is_dir():
                continue
            m = re.match(r"(\d+)_(.+)", p.name)
            n, label = (int(m.group(1)), m.group(2)) if m else (0, p.name)
            subj = (p / "subject.txt").read_text().strip() if (p / "subject.txt").exists() else ""
            out.append(GrillTask(n=n, label=label, path=p, subject=subj))
        return out

    # -- tabular views -----------------------------------------------------

    def hypotheses_table(self) -> list[dict]:
        d = self.ledger_json or {}
        rows = []
        for h in (d.get("hypotheses") or {}).values():
            ev = [
                (d.get("evidence") or {}).get(e)
                for e in h.get("evidence_ids", [])
            ]
            ev = [e for e in ev if e]
            rows.append(
                {
                    "id": h["id"],
                    "status": h.get("status"),
                    "verdict": h.get("verdict"),
                    "confidence": h.get("confidence"),
                    "origin": h.get("origin"),
                    "attempts": h.get("test_attempts", 0),
                    "n_evidence": len(ev),
                    "n_support": sum(1 for e in ev if e.get("stance") == "supports"),
                    "n_against": sum(1 for e in ev if e.get("stance") == "contradicts"),
                    "direction": h.get("direction_id"),
                    "text": h.get("text", ""),
                    "bin_reason": h.get("bin_reason", ""),
                }
            )
        return sorted(rows, key=lambda r: r["id"])

    def evidence_table(self) -> list[dict]:
        d = self.ledger_json or {}
        rows = []
        for e in (d.get("evidence") or {}).values():
            s = e.get("source") or {}
            rows.append(
                {
                    "id": e["id"],
                    "hypothesis": e.get("hypothesis_id"),
                    "stance": e.get("stance"),
                    "phase": e.get("phase"),
                    "year": s.get("year"),
                    "pmid": s.get("pmid"),
                    "doi": s.get("doi"),
                    "url": s.get("url"),
                    "title": s.get("title", ""),
                    "verified": s.get("verified", False),
                    "text": e.get("text", ""),
                }
            )
        return sorted(rows, key=lambda r: r["id"])

    def directions_table(self) -> list[dict]:
        d = self.ledger_json or {}
        return [
            {
                "id": x["id"],
                "status": x.get("status"),
                "promise": x.get("promise"),
                "allocated": x.get("allocated_usd"),
                "spent": x.get("spent_usd"),
                "origin": x.get("origin"),
                "parent": x.get("parent_id"),
                "tests": x.get("tests_hypothesis_id"),
                "n_hypotheses": len(x.get("produced_hypotheses", [])),
                "question": x.get("question_text", ""),
            }
            for x in (d.get("directions") or {}).values()
        ]

    def cost_by_phase(self) -> dict[str, float]:
        r = self.run_json or {}
        return dict((r.get("budget") or {}).get("by_phase") or {})

    def snapshots(self) -> list[dict]:
        return list((self.run_json or {}).get("snapshots") or [])

    # -- what the assignment grades ---------------------------------------

    def cited_sources(self) -> list[dict]:
        """Every distinct source the ledger holds, with its locators."""
        seen: dict[str, dict] = {}
        for e in self.evidence_table():
            key = e["pmid"] or e["doi"] or e["url"] or e["title"]
            if not key:
                continue
            rec = seen.setdefault(
                key,
                {
                    "key": key,
                    "pmid": e["pmid"],
                    "doi": e["doi"],
                    "url": e["url"],
                    "title": e["title"],
                    "year": e["year"],
                    "n_evidence": 0,
                    "pooled_support": 0,
                },
            )
            rec["n_evidence"] += 1
        return sorted(seen.values(), key=lambda r: -r["n_evidence"])

    def __repr__(self) -> str:  # pragma: no cover - display only
        d = self.ledger_json
        if d is None:
            return f"<GrillRun {self.run_dir} (no ledger yet)>"
        h = d.get("hypotheses") or {}
        pooled = sum(1 for x in h.values() if x.get("status") == "pooled")
        spend = (self.run_json or {}).get("budget", {}).get("spent", 0.0)
        return (
            f"<GrillRun {self.run_dir.name}: {len(d.get('directions') or {})} directions, "
            f"{len(h)} hypotheses ({pooled} pooled), "
            f"{len(d.get('evidence') or {})} evidence, ${spend:.2f}>"
        )


# --------------------------------------------------------------------------
# Retrieval evaluation
# --------------------------------------------------------------------------


_PMID = re.compile(r"\b(\d{7,8})\b")


def extract_pmids(obj: Any) -> set[str]:
    """Every PMID anywhere in a nested structure or a blob of text."""
    if isinstance(obj, str):
        return set(_PMID.findall(obj))
    if isinstance(obj, dict):
        out: set[str] = set()
        for k, v in obj.items():
            if k == "pmid" and isinstance(v, (str, int)) and v:
                out.add(str(v))
            else:
                out |= extract_pmids(v)
        return out
    if isinstance(obj, (list, tuple)):
        return set().union(*(extract_pmids(x) for x in obj)) if obj else set()
    return set()


@dataclass
class RetrievalReport:
    found: set[str]
    gold: set[str]
    hits: set[str]
    recall: float
    n_found: int
    precision_vs_gold: float

    def as_dict(self) -> dict:
        return {
            "n_found": self.n_found,
            "n_gold": len(self.gold),
            "n_hits": len(self.hits),
            "recall": round(self.recall, 3),
            "precision_vs_gold": round(self.precision_vs_gold, 3),
            "missed": sorted(self.gold - self.hits),
        }


def evaluate_retrieval(found_pmids: Iterable[str], gold_pmids: Iterable[str]) -> RetrievalReport:
    """Did the search find the papers the curators actually used?

    ``precision_vs_gold`` is not precision in the usual sense -- a paper outside
    the gold set is not necessarily irrelevant, it may simply be one the HPO
    curators did not annotate from. Read it as concentration, and judge
    precision by reading the sources.
    """
    found = {str(p) for p in found_pmids}
    gold = {str(p) for p in gold_pmids}
    hits = found & gold
    return RetrievalReport(
        found=found,
        gold=gold,
        hits=hits,
        recall=len(hits) / len(gold) if gold else 0.0,
        n_found=len(found),
        precision_vs_gold=len(hits) / len(found) if found else 0.0,
    )
