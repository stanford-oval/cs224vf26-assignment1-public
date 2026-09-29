# cli.py

The command-line entry point. This page walks `cli.py` top to bottom: the argument parser, how each flag maps onto a field of the `Config` dataclass, and how the question, reference set, and `Orchestrator` are constructed and launched.

Related: [orchestrator.py](./orchestrator.md) · [Config knobs (reference)](../reference/config-reference.md) · [codex_exec.py](./codex_exec.md) · [The orchestration loop](../architecture/orchestration-loop.md) · [documentation index](../README.md)

## What the module is

The whole file is one function, `main()` (`cli.py:20`), plus a `raise SystemExit(main())` guard (`cli.py:63`). It has no classes and no helpers. Its job is narrow: parse `argv`, resolve the question text and optional reference set, pack the flags into a `Config`, then hand off to the `Orchestrator`, which owns the belief ledger and the run loop.

Two imports supply everything it delegates to (`cli.py:16-17`):

| Import | From | Used for |
|---|---|---|
| `DEFAULT_ENV` | `codex_exec.py:53` | default value for `--env` (path to the `.env` codex reads) |
| `Config`, `Orchestrator` | `orchestrator.py:67`, `orchestrator.py:149` | the run configuration and the run driver |

## Control flow

```
main()  (cli.py:20)
  ├─ build ArgumentParser + args            cli.py:21-38
  ├─ parse_args()                           cli.py:39
  ├─ resolve question text                  cli.py:41
  │     --question-file → read file  |  --question → literal
  ├─ resolve reference set (optional)       cli.py:42-46
  │     read JSON; unwrap {findings|items} if it's a dict
  ├─ Config(...)  ← flags mapped in         cli.py:48-53
  ├─ Orchestrator(question, run_dir, cfg)   cli.py:54
  ├─ orch.run()                             cli.py:55  ← the entire run happens here
  └─ print answer/ledger/run paths; return 0  cli.py:56-59
```

## Arguments

The parser is created at `cli.py:21`. The two question flags are added to a mutually-exclusive group with `required=True` (`cli.py:22-24`), so exactly one of `--question` / `--question-file` must be given. Every other flag is a plain `add_argument` on the parser.

| Flag | Type / action | Default | argparse dest | Config field it feeds |
|---|---|---|---|---|
| `--question` | str | — | `question` | (read into `question` local, `cli.py:41`) |
| `--question-file` | str | — | `question_file` | (read into `question` local, `cli.py:41`) |
| `--run-dir` (required) | str | — | `run_dir` | positional arg to `Orchestrator` (`cli.py:54`) |
| `--budget` | float | `50.0` | `budget` | `Config.budget` |
| `--rho` | float | `0.7` | `rho` | `Config.rho` (explore/verify budget split) |
| `-K`, `--batch` | int | `5` | `batch` | `Config.K` (best-first batch width) |
| `--promote-tau` | float | `0.6` | `promote_tau` | `Config.promote_tau` — **deprecated / unused** (see below) |
| `--checkpoint-every` | float | `0.0` | `checkpoint_every` | `Config.checkpoint_every` (`0` → `budget/6`) |
| `--max-rounds` | int | `30` | `max_rounds` | `Config.max_rounds` |
| `--concurrency` | int | `4` | `concurrency` | `Config.concurrency` |
| `--task-timeout` | int | `1800` | `task_timeout` | `Config.task_timeout` (seconds) |
| `--model` | str | `"gpt-5.4"` | `model` | `Config.model` |
| `--env` | str | `DEFAULT_ENV` | `env` | `Config.env_file` |
| `--reference-set` | str | — | `reference_set` | parsed JSON → `Config.reference_set` |

Note the argparse dest names differ from the Config field names in two places: `-K/--batch` → `Config.K` and `--env` → `Config.env_file`. The mapping is done explicitly in the `Config(...)` call at `cli.py:48-53`.

### `--promote-tau` is dead

The flag is still parsed (`cli.py:29`) and passed into `Config` (`cli.py:49`), but `Config.promote_tau` is annotated `DEPRECATED: legacy hard floor (unused; kept for cli back-compat)` (`orchestrator.py:71`). Promotion is now beam search plus Thompson sampling (Component A, driven by `eta` / `promote_explore_frac`), so setting `--promote-tau` has no effect on a run. It is retained only so old invocation scripts do not error.

## Resolving the question

```
question = read_text(question_file)  if --question-file  else  --question
```

At `cli.py:41`, if `--question-file` was given its contents are read as UTF-8; otherwise the literal `--question` string is used. The resulting `question` string is passed positionally to `Orchestrator` (`cli.py:54`), which strips it (`orchestrator.py:151`).

## Resolving the reference set

`--reference-set` points at a JSON file of "grounded findings" used for §7c recall scoring. Resolution (`cli.py:42-46`):

1. `ref` starts as an empty list (`cli.py:42`).
2. If the flag is set, the file is read and `json.loads`-ed (`cli.py:44`).
3. If the parsed value is a `dict`, it is unwrapped: `ref = ref.get("findings") or ref.get("items") or []` (`cli.py:46`). So the file may be either a bare JSON list, or an object with a `findings` (preferred) or `items` key.

The final list is passed as `Config.reference_set` (`cli.py:52`). If the top-level JSON is neither a list nor a dict (e.g. a bare string or number), `ref` keeps whatever `json.loads` returned and is passed through unchanged — there is no type validation beyond the dict-unwrap.

## Building the Config

The `Config` constructed at `cli.py:48-53` sets only the 12 fields listed in the table above. `Config` (`orchestrator.py:67-117`) defines roughly 40 fields; every field not in the table keeps its dataclass default and **cannot** be set from the command line. Notable knobs that are default-only from the CLI include:

| Config field (default) | Governs |
|---|---|
| `eta` (`3.0`) | divisor controlling beam size per promotion wave (`keep = ceil(fresh_claims / eta)`, so larger `eta` → smaller beam) |
| `promote_explore_frac` (`0.34`) | Thompson exploration share of the beam |
| `explore_task_usd` (`3.5`), `verify_task_usd` (`1.5`), `ground_task_usd` (`2.0`) | per-task target spend |
| `ground_terms` (`4`) | key terms grounded during INIT |
| `fdr_enabled` (`True`), `fdr_wealth0` (`0.5`), `fdr_alpha` (`0.05`) | online-FDR / alpha-investing brake |
| `calibrate_enabled` (`True`), `calibrate_min_labels` (`12`) | confidence recalibration |
| `corroborate_enabled` (`True`), `corroborate_thresh` (`0.88`) | corroboration re-scoring |
| `prior_probe_enabled` (`True`), `prior_probe_k` (`5`) | INIT prior-answer probing |
| `rerank_frontier` (`True`), `rerank_pool` (`50`) | LLM frontier reranking |
| `rubric` (Correctness/Completeness/…) | judge rubric text |

To change any of these you must edit `Config` defaults or construct the orchestrator programmatically; the CLI exposes none of them. See [Config knobs (reference)](../reference/config-reference.md) for the full field list.

## Launching the run

```
orch = Orchestrator(question, Path(run_dir), cfg)   cli.py:54
orch.run()                                          cli.py:55
```

`Orchestrator.__init__` (`orchestrator.py:150-176`) creates the run directory, and instantiates the `Ledger`, `Budget(cfg.budget, cfg.rho)` (`orchestrator.py:156`; the `Budget` class and its `__init__` are defined at `orchestrator.py:37`, `41`), `Embedder`, `AlphaInvesting` FDR brake, and `Calibrator`. `run()` (`orchestrator.py:319`) then executes the entire orchestration loop synchronously — `main()` does no looping of its own. See [orchestrator.py](./orchestrator.md) and [The orchestration loop](../architecture/orchestration-loop.md).

## Output and exit

After `run()` returns, `main()` prints three artifact paths under the run directory (`cli.py:56-58`) and returns `0` (`cli.py:59`):

| Printed path | File |
|---|---|
| `answer  →` | `<run-dir>/answer.md` |
| `ledger  →` | `<run-dir>/ledger.json` |
| `run     →` | `<run-dir>/run.json` |

These strings are informational; `main()` does not itself write those files (the `Orchestrator` does). The module-level guard `raise SystemExit(main())` (`cli.py:62-63`) turns the return code into the process exit status.

## Invocation

From the module docstring (`cli.py:1-9`):

```
python3 -m src.cli --question-file Q.txt --run-dir OUT --budget 50
python3 -m src.cli --question "What ..." --run-dir OUT --budget 50 -K 5
```

The docstring notes run directories may live anywhere: each codex task runs with `--cd <its own task dir>` (an empty leaf) and the repo root has no `AGENTS.md`, so there is no skills/agents auto-load concern from the run location.
