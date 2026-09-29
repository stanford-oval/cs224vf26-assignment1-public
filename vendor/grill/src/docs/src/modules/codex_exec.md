# codex_exec.py

This page is a low-level walkthrough of `codex_exec.py`, the single LLM primitive of methodology_v2: `run_task(task_dir, prompt, schema) -> (validated_json, usd)`, implemented as one ephemeral `codex exec --output-schema` subprocess per call. It covers the two execution modes, the Stanford proxy provider wiring, retry logic, per-model USD pricing and real-spend metering, and `.env` loading.

Related: [executors.py](./executors.md), [orchestrator.py](./orchestrator.md), [schemas.py](./schemas.md), [The executor roles](../architecture/executor-roles.md), [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md).

## What this module is

`codex_exec.py` is the only place the system shells out to an LLM. The orchestrator owns all control flow and the belief ledger; codex is invoked here as a pure, stateless function `f(task, context) -> validated JSON` and never decides the next step (module docstring, `codex_exec.py:1-17`). Every executor role in [executors.py](./executors.md) is a thin prompt-builder that ends in a call to `run_task` (`executors.py:45,61,75,90,144,185,235,271,289,304,323`).

The file is deliberately self-contained: it has no repo-internal imports and mirrors the project's `baseline.py` conventions so it can run standalone (`codex_exec.py:16-28`). Only three names are imported elsewhere: `run_task` (by executors), and `CodexError` / `DEFAULT_ENV` (by the orchestrator and CLI, `orchestrator.py:29`, `cli.py:16`).

## Module-level constants

| Constant | Value | Purpose | Line |
|---|---|---|---|
| `_MODEL_RATES_M` | dict of `model -> (in$/1M, out$/1M)` | Per-model input/output USD rates (LiteLLM proxy) | `33-38` |
| `_DEFAULT_RATES_M` | `(2.50, 15.0)` | Fallback rate for unknown models (full-model pricing) | `39` |
| `DEFAULT_ENV` | `/data/oval/report_formation/graph-search-sliders-2/.env` | Default `.env` sourced for each task | `52` |
| `PROVIDER_KEY` | `"OPENAI_API_KEY"` | Env var the provider reads for auth | `54` |
| `PROVIDER` | 5 `-c` override strings | Stanford proxy provider config (see below) | `67-73` |
| `_TOKENS_RE` | regex `tokens used\n<n>` | Extracts token count from the transcript fallback | `75` |

### Pricing note (input vs output priced separately)

Rates are stored as `($/1M input, $/1M output)` because on this proxy output (reasoning) tokens run ~6x input and dominate cost, so a single blended rate would misprice (`codex_exec.py:30-32`). Full models (`gpt-5`, `gpt-5.4`, `gpt-5.5`, the `-codex` variants) price at `(2.50, 15.0)`; `-mini` at `(0.75, 4.50)`; `-nano` at `(0.20, 1.25)` (`33-38`).

- `rates_for(model)` returns `(input_$per_token, output_$per_token)` — the `$/1M` entries divided by 1e6, defaulting to `_DEFAULT_RATES_M` for an unknown/`None` model (`42-45`). This is the rate used by the real-spend path.
- `rate_for(model)` returns a single blended `$/token` = `0.3*input + 0.7*output`, used only by the transcript-only fallback where the input/output split is unknown (`48-51`).

## Provider wiring: the Stanford proxy

`PROVIDER` is a list of five `-c` config overrides injected into every `codex exec` call (`67-73`):

```
model_provider=stanford
model_providers.stanford.name="Stanford Azure OpenAI"
model_providers.stanford.base_url="https://azureopenai.genie.stanford.edu/v1"
model_providers.stanford.env_key="OPENAI_API_KEY"
model_providers.stanford.wire_api="responses"
```

This is an OpenAI-compatible LiteLLM proxy that serves the `gpt-5.x` (and `-codex`) models plus `text-embedding-3-large`, using the `responses` wire API (`64-73`). Auth is read from `OPENAI_API_KEY` (`PROVIDER_KEY`); `_run_task_once` raises `CodexError` if that key is absent after `.env` load (`240-241`).

Naming caveat to be honest about: the module docstring calls this "the docuset Azure provider (gpt-5.4)" (`codex_exec.py:3`), but the wired provider id is `stanford` and the codex auth key is `OPENAI_API_KEY`.

## Environment loading — `load_env` (`78-88`)

`load_env(path, env)` mutates the `env` dict in place from a `.env` file. Blank lines, comments (`#`), and lines without `=` are skipped; values are stripped of surrounding single/double quotes (`82-88`).

Key behavior: `.env` is authoritative and **overrides** any ambient value already in `env` (`env[k] = v`, `88`). The comment explains why (`86-87`): a budget-exhausted key exported in the shell must not shadow the fresh key from `.env`, so the file wins. This matches the MEMORY note that `.env` override is intentional. If the file does not exist, the function returns silently (`80-81`).

## Real-spend metering

Cost is read back as **real USD** from codex's own session rollout, not estimated from the prompt.

### `spent_usd(run_dir)` (`100-131`)

The core meter. It finds the codex rollout whose recorded session cwd equals `run_dir`, then prices its cumulative token usage.

```
~/.codex/sessions/**/rollout-*.jsonl   (glob, recursive)   103
        │  filter: _session_cwd(f) == resolve(run_dir)      104
        ▼
   pick newest by mtime                                     107
        │  scan lines:
        │    • first "model" match  -> model                112-115
        │    • each "token_count" line -> total_token_usage 116-127
        │      (cumulative; keep the LAST non-zero)
        ▼
 billed_in = input_tokens - cached_input_tokens             124
             then clamped to >=0 (max(0, inp))              127
 billed_out = output_tokens                                 125
        ▼
 rates_for(model) -> (ri, ro)                               130
 return billed_in*ri + billed_out*ro                        131
```

Details worth noting:
- `_session_cwd(f)` reads only the first line of a rollout and returns `payload.cwd` iff `type == "session_meta"`, else `None` (`91-97`).
- `total_token_usage` is cumulative across the session, so the loop keeps overwriting `billed_in/billed_out` with the last non-zero reading rather than summing (`123-127`).
- Cached input tokens are subtracted from input so cache hits are not double-billed (`124`).
- Returns `0.0` on no matching rollout (`105-106`) or on `OSError` (`128-129`). If no usage line is found it falls through with `billed_in/out = 0` and returns `0*ri + 0*ro = 0.0` at `131` (not an early return).
- The model actually used is read from the rollout itself (`112-115`), so pricing keys on what ran, not on the requested `model` argument.

### `_tokens_from_transcript(text)` (`134-141`)

Fallback token count: applies `_TOKENS_RE` to the transcript, takes the **last** match, strips commas, returns an int (0 on no match / parse error). Used only when the rollout-by-cwd lookup returns 0.

## The public primitive: `run_task` (`204-214`)

```python
def run_task(task_dir, prompt, schema, *, retries: int = 2, **kw) -> tuple[dict, float]
```

A thin retry wrapper over `_run_task_once`. It loops up to `retries + 1` times (default 3 attempts), accumulating the USD of every attempt into `total`. On the first attempt whose `data is not None`, it returns `(data, total)`. If all attempts soft-fail it returns `(None, total)` (`208-214`).

- Soft failures (proxy dropped the call: fast 5xx / empty output) return `(None, usd)` from the inner call and are retried; their cost — usually ~0 — is still charged (`204-207`).
- Hard config errors surface as `CodexError` from `_run_task_once` and propagate out of the loop; they are **not** retried (`206-207`, raised at `241`).

`CodexError` is a bare `RuntimeError` subclass (`144-145`).

## The engine: `_run_task_once` (`217-316`)

Signature and defaults:

| Param | Default | Meaning | Line |
|---|---|---|---|
| `task_dir` | — | Per-task working dir; resolved to absolute | `217`, `230` |
| `prompt` | — | Prompt text (fed via STDIN) | `217` |
| `schema` | — | JSON Schema forced onto the final message | `217` |
| `mode` | `"research"` | `research` or `reason` (see below) | `217` |
| `model` | `"gpt-5.4"` | Model id passed as `-m` | `218` |
| `env_file` | `DEFAULT_ENV` | `.env` sourced into the subprocess env | `218` |
| `timeout` | `1800` | Wall-clock seconds before SIGKILL | `219` |
| `usd_cap` | `None` | Per-task spend watchdog (hard kill) | `219` |

### Step 1 — materialize task files (`230-235`)

`task_dir` is resolved to an absolute path (codex `--cd` requires absolute) and created. Three files are written into it: `schema.json` (the JSON Schema), `prompt.txt` (the prompt), and later `out.json` / `transcript.log`.

### Step 2 — build the env (`237-241`)

Copies `os.environ`, drops `VIRTUAL_ENV` (`238`), then applies `load_env(env_file, env)` (`.env` overrides ambient). If `OPENAI_API_KEY` is still absent it raises `CodexError` before spending anything (`240-241`).

### Step 3 — assemble the codex command (`243-266`)

Base command (`243`): `codex exec --skip-git-repo-check --cd <task_dir>`, then each of the five `PROVIDER` overrides as `-c` (`244-245`).

Mode branch:

| Mode | Sandbox | Network / tools | Callers | Lines |
|---|---|---|---|---|
| `research` | `workspace-write` | `network_access=true`, `tools.web_search=true`, `shell_environment_policy.inherit=all` | GROUND, EXPLORE, VERIFY | `246-258` |
| `reason` (else) | `read-only` | none | PRIOR, FIELDS, RERANK, PATTERNS, FINALIZE, JUDGE_COVERAGE (JUDGE_FORWARD, EVALUATE are defined but unwired) | `259-260` |

(Role→mode mapping cross-checked against `executors.py` — the genuinely wired reason-mode roles are PRIOR, FIELDS, RERANK, PATTERNS, FINALIZE, JUDGE_COVERAGE. `judge_forward` (`executors.py:292`) and `evaluate` (`executors.py:307`) are also written with `mode="reason"` but the orchestration loop never invokes them, so they are defined-but-unwired. Note the module docstring at `codex_exec.py:9-11` names only PRIOR/EVALUATE for `reason` and GROUND/EXPLORE/VERIFY for `research`; it is illustrative, not exhaustive.)

The command tail (`264-266`) adds `-m <model> --color never --output-schema schema.json --output-last-message out.json -`. The trailing `-` makes codex read the prompt from **STDIN** rather than argv; the comment explains large prompts would otherwise overflow the ~128KB argv limit ("Argument list too long", `261-263`).

`--output-schema` forces the final assistant message to schema-conformant JSON; `--output-last-message out.json` is where that JSON lands.

### Step 4 — run with the budget watchdog (`268-300`)

```
Popen(cmd, stdin=prompt.txt, stdout=stderr=transcript.log,          272-274
      start_new_session=True)     # own process group, killable
        │
        ├─ if usd_cap:  daemon thread watch()                        277-291
        │     every 5s: if spent_usd(task_dir) >= usd_cap            278-279
        │        -> killpg(SIGTERM), sleep 3, killpg(SIGKILL)        281-288
        │           killed_for_budget = True
        │
        └─ proc.wait(timeout)                                        293
              on TimeoutExpired -> killpg(SIGKILL), wait()           294-299
        stop.set()   # stop the watchdog                             300
```

The subprocess is started in its own session (`start_new_session=True`, `274`) so the whole process group can be killed. The `watch()` thread polls `spent_usd(task_dir)` every 5s and hard-kills once real spend crosses `usd_cap` — the per-task budget backstop (`222-224`, `277-288`). Both stdout and stderr are redirected into `transcript.log` (`272-273`).

Note: `killed_for_budget` is recorded (`280`) but never read after the run — it does not alter the return value.

### Step 5 — meter the spend (`302-307`)

1. `usd = spent_usd(task_dir)` — the real per-model rollout cost (`302`).
2. If that is `<= 0.0` (rollout-by-cwd missed), fall back to `_tokens_from_transcript(...) * rate_for(model)` — the blended-rate transcript estimate (`303-305`).

### Step 6 — parse the schema output (`309-316`)

- If `out.json` does not exist → return `(None, usd)`. The spend is still returned so the orchestrator charges it even though no JSON was produced (a task killed at its `usd_cap` cost real money) (`309-312`).
- If `out.json` exists, parse it: on success return `(parsed_dict, usd)`; on `JSONDecodeError` return `(None, usd)` (`313-316`).

So a soft failure is always `(None, usd)` — never an exception — which is exactly what `run_task`'s retry loop tests for (`212`).

## End-to-end data flow

```
executors.<role>(…)                      executors.py
   builds prompt + picks schema + mode
   └─► run_task(task_dir, prompt, schema, retries=2, **kw)     204
          └─► _run_task_once  (up to 3x)                       217
                 write schema.json / prompt.txt                232-235
                 env = os.environ + .env (override)            237-239
                 assert OPENAI_API_KEY  ─(else)─► CodexError    240-241
                 build `codex exec` argv (+PROVIDER, +mode)   243-266
                 Popen  ──stdin──►  prompt.txt                 272
                        watchdog: spent_usd >= usd_cap ► kill  277-291
                 usd = spent_usd(rollout)                      302-307
                 out.json ──json.loads──► data                313-314
          returns (data|None, usd_total)
```

## Honesty notes / dead-or-unwired paths

- `killed_for_budget` (defined `269`, written `280`) is written but never consumed; it has no effect on control flow or the returned value.
- The transcript fallback (`303-305`) only fires when `spent_usd` returns 0; in the normal path the rollout meter provides the cost and the transcript token count is unused.
- Codex auth is strictly `OPENAI_API_KEY` (`54`, `240`).
