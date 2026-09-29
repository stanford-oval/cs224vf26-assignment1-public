# Running the agent — current state of the code

What actually works today, which knobs are wired, and which parts of the codebase are dead.
Everything here was verified against the source, not the README.

> **The README's quick start is stale and will fail.** It shows `--rho 0.7`, a flag that no longer
> exists (`cli.py: error: unrecognized arguments: --rho 0.7`), and its "Core idea" / "The
> methodology" sections describe an architecture that has been replaced. See
> [§6 What was removed](#6-what-was-removed).

---

## 1. Prerequisites

- The **`codex` CLI** on `PATH`. Every LLM call shells out to `codex exec`.
- A **`.env` at the repo root** with `OPENAI_BASE_URL` and `OPENAI_API_KEY` (the Stanford
  LiteLLM→Azure proxy). `PAPERCLIP_API_KEY` is optional — without it `--sources` degrades to
  codex's own web search.
- Python via `.venv` (`uv sync`, or whatever created it). Production launches use
  `.venv/bin/python`.
- Optional: `make analysis-venv` builds `.analysis-venv` with pandas/numpy/scipy/matplotlib. The
  artifact builder uses it for charts and falls back to plain `python3` if absent.
- Optional: `git` on `PATH`. Without it the per-question workspace still works, just uncommitted.

## 2. Run it

```bash
# offline self-test — no codex, no spend, ~2s. Run this first.
python3 -m src.selftest

# a real run
python3 -m src.cli \
  --question-file question.txt \
  --run-dir runs/my_question \
  --budget 15 -K 5
```

A real production invocation, for reference (from `run-94c3a543`):

```bash
.venv/bin/python -m src.cli \
  --question "…" \
  --run-dir /srv/services/sliders-portal/extracted/steer_runs/run-94c3a543 \
  --steer-inbox <run-dir>/steer_inbox.json \
  --budget 15.0 -K 5 --alloc-ceiling-frac 0.4 --max-rounds 30 \
  --model gpt-5.4-mini --reasoning low \
  --sources pmc,biorxiv,medrxiv,abstracts
```

That run cost **\$10.59 of a \$15 budget over 8 rounds**: 94 hypotheses, 818 evidence items, 216
sources, 5 artifacts. Budget split by phase was `deep \$7.34 · screen \$1.84 · explore \$0.81 ·
artifact \$0.11 · finalize \$0.15 · init \$0.14 · plan \$0.11 · measure \$0.08`. Deep testing
dominates; budget under ~\$10 mostly buys fewer tested hypotheses, not a shallower report.

### Steering a live run

```bash
# terminal 1 — the run, draining an inbox each round
python3 -m src.cli --question-file Q.txt --run-dir OUT --budget 15 \
    --steer-inbox OUT/steer_inbox.json

# terminal 2 — the browser console (stdlib only)
python3 -m src.steer_server --run-dir OUT --inbox OUT/steer_inbox.json --port 8765

# free text works; the agent classifies it into the right channel
echo '[{"nl":"only clinical studies since 2020; also give me a csv of all the benchmarks"}]' \
    > OUT/steer_inbox.json

# resume a paused or finished run (keeps ledger + budget + queued artifact requests)
python3 -m src.cli --run-dir OUT --resume
```

### Your own data

```bash
python3 -m src.cli --question "which of my genes sit in the XYZ pathway?" \
    --data cohorts.csv,expr.tsv --run-dir OUT --budget 8
```

Files are copied read-only into `<run-dir>/workspace/inputs/` and content-addressed
(`name@<digest>`). The agent writes and runs scripts against them; data-derived findings resolve
via `dataset_id` + operation instead of a DOI.

## 3. Outputs (in `--run-dir`)

| path | what |
|---|---|
| `answer.md` | the report |
| `reports/vN.md` + `index.json` | one version per finalize (initial run + each resume) |
| `ledger.json` | full belief state — directions, hypotheses, evidence, provenance |
| `run.json` | budget by phase, checkpoint snapshots, config, resumable runtime state |
| `artifacts.json` | the deliverables index + the workspace's git log |
| `workspace/` | **a git repo**: `data/` (ledger as CSV+JSON), `inputs/`, `artifacts/`, `scripts/` |
| `tasks/NNNN_*/` | every codex call: prompt, schema, output JSON, transcript |
| `orchestrator.log`, `steer.log`, `steer_request.md` | control trace, steer audit, round digest |

`workspace/data/metrics.csv` is long format — one row per number any source reported, with that
source. It is usually what someone actually wants when they ask for "the benchmarks".

## 4. CLI flags (all of them, all wired)

| flag | default | effect |
|---|---|---|
| `--question` / `--question-file` | — | required unless `--resume` |
| `--run-dir` | — | **required** |
| `--budget` | 50.0 | total USD, one pool |
| `-K`, `--batch` | 5 | max directions the planner may fund per round |
| `--alloc-ceiling-frac` | 0.40 | max share of a round's pot to any one direction |
| `--explore-round-frac` | 0.50 | share of remaining budget the planner may hand out per round |
| `--screen-task-usd` | 0.40 | cap per stage-1 screen |
| `--deep-task-usd` | 2.00 | cap per stage-2 deep test |
| `--checkpoint-every` | 0 → `budget/6` | USD between checkpoints |
| `--max-rounds` | 30 | |
| `--concurrency` | 4 | parallel codex tasks |
| `--task-timeout` | 1800 | seconds per task |
| `--model` | `gpt-5.6-terra` | **not** `gpt-5.4-mini` as the README claims |
| `--reasoning` | `low` | `minimal｜low｜medium｜high` |
| `--env` | `<repo>/.env` | secrets file |
| `--sources` | "" (web only) | comma-separated paperclip corpora — see §5 |
| `--steer-inbox` | "" | JSON inbox drained each round |
| `--interactive` | off | block on stdin at every checkpoint |
| `--resume` | off | continue from `--run-dir` |
| `--no-workspace` | off | disable the git workspace and all artifacts |
| `--no-auto-artifacts` | off | only build deliverables explicitly asked for |
| `--artifact-usd` | 1.50 | cap per artifact build |
| `--data` | "" | comma-separated CSV/TSV files to stage as inputs |
| `--data-query-usd` | 1.50 | cap per data-query task |

**`--reference-set` is accepted, parsed, and then ignored.** It writes `Config.reference_set`,
which nothing reads. Don't rely on it.

## 5. Valid `--sources` corpora

`pmc`, `arxiv`, `biorxiv`, `medrxiv`, `abstracts`, `fda`, `fda/jp`, `fda/eu`, `trials`,
`trials/us`, `trials/eu`, `trials/jp`, `trials/cn`. Requires `PAPERCLIP_API_KEY`; any failure
degrades silently to web search only.

## 6. Config-only knobs (no CLI flag — edit `Config` in `src/orchestrator.py`)

All of these are read by the live code:

| field | default | effect |
|---|---|---|
| `explore_default_usd` | 3.5 | allocation for a direction the planner didn't price |
| `explore_min_usd` | 1.0 | below this a direction isn't launched |
| `plan_task_usd` | 1.0 | cap on the rank-and-allocate call |
| `ground_task_usd` / `ground_terms` | 2.0 / 4 | INIT term grounding (`ground_terms=0` skips it) |
| `progress_eps` | 0.02 | new (covered asks + pooled) per \$ below this = stalled |
| `retest_max_attempts` | 2 | bounds the refute → re-investigate → re-test loop |
| `corroborate_enabled` / `_thresh` / `_per_source` | on / 0.88 / 0.04 | pulls hypotheses back out of the bin |
| `unbin_thresh` | 0.60 | corroborated past this, a binned hypothesis is re-tested |
| `prior_probe_enabled` / `prior_probe_k` | on / 5 | test PRIOR's parametric answers during INIT |
| `niche_boost` | 0.15 | promise boost under a thin/contested parent |
| `rerank_direct_max` / `rerank_pool` | 60 / 50 | frontier shortlisting before the planner reads it |
| `artifact_min_usd` | 0.50 | floor below which an artifact request stays queued |
| `judge_query_usd` | 0.40 | cap per data-query script review |

`Config.rubric` exists and is **never read** (it fed the removed evaluator).

## 7. Environment overrides

`RUN_MODEL`, `EMBED_MODEL`, `CLASSIFY_MODEL`, `REASONING`, `GSS_ENV_FILE`, `STEER_PY`,
`ANALYSIS_PYTHON` — each overrides the corresponding default in `src/config.py`.

## 8. What the loop actually does

```
INIT   parse the asks · PRIOR's parametric candidate answers become HYPOTHESES and are
       immediately screened + deep-tested · GROUND key terms
LOOP   PLAN (the agent ranks the frontier AND allocates the round's money)
       → EXPLORE each funded direction → hypotheses
       → SCREEN every hypothesis (stage 1, cheap)
       → DEEP TEST everything that passes (stage 2: evidence AND counter-examples)
       → survivors POOLED, the rest BINNED with a reason (retained, resurfacable)
       → checkpoint · steer · artifacts
FINAL  outline-then-fill report + deterministic bibliography + workspace export
```

One budget pool. The agent allocates it across directions; the harness only clamps per-direction
and per-round shares and enforces them with a USD watchdog. **Testing is never rationed** — it
draws from the same pool but is never traded off against exploration.

## 9. What was removed

The README still documents these. They are **gone from the live path**:

| gone | replaced by |
|---|---|
| **Online calibration** — `src/calibration.py`, the two-map isotonic (PAV) point+width calibrator | nothing. The module still exists on disk with **zero imports from anywhere**. Dead code. |
| **`--rho`, the explore/verify budget split** | one pool + `--explore-round-frac` / `--alloc-ceiling-frac` |
| **Promotion by beam + Thompson sampling** | no promotion gate at all — every hypothesis is screened, everything that passes is deep-tested |
| **Online-FDR / alpha-investing verify budget** | nothing; testing is unrationed |
| **Annealing** (broad-shallow → few-deep across rounds) | nothing |
| **`Claim` + 3-state VERIFY** (`confirmed`/`error`/`refuted`) | `Hypothesis` + the two-stage test; verdicts are `supported`/`conflicted`/`refuted`, and nothing is deleted — failures go to the BIN with a reason |

Also dead but still on disk: `executors.evaluate` + `schemas.EVALUATE`, and
`executors.judge_forward` + `schemas.JUDGE_FORWARD` — both defined, neither ever called.
`Config.rubric` and `Config.reference_set` are the orphaned inputs to those.

Standalone scripts not reachable from `cli.py` (run them directly if you want them):
`build_explore_html.py`, `build_trajectory_html.py`, `fix_authors.py`, `stage_to_portal.py`,
`steer_launcher.py`, `steer_server.py`.

**So: the calibrate-then-allocate design is no longer what the code does.** The current design is
*test everything, ration nothing, keep everything*: confidence is still tracked per hypothesis and
still moved by screening, deep testing and corroboration, but it is never recalibrated against
outcomes, and it no longer gates what gets verified.

## 10. Known gaps

- **Derived claims are penalised.** `apply_deep` pools only on `supported ∧ no contradiction ∧
  grounded()`, and `grounded()` means "has a resolvable citation" (`ledger.py:407`, `:170`). A
  claim *composed* from two sourced mechanisms — a prediction about the user's own experiment —
  has no paper stating it, so it is binned as "supported but no resolvable source was produced".
- **Patterns are decorative.** `executors.patterns` produces genuine composed predictions, but
  `spawn_from_patterns` (`ledger.py:520`) demotes the `hypothesis` field to a Direction's
  rationale string. It never becomes a Hypothesis, is never tested, and rarely reaches the report.
- **Coverage can be vacuous.** On a single-ask question, `fields` parses one required field that
  restates the whole question, so `coverage = 1.0` is uninformative — it cannot detect that a
  given fact went unaddressed.
