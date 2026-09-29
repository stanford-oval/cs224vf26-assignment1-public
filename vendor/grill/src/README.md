# Methodology v2 — orchestrator-driven research agent

The `src` package: a budget-bounded, self-correcting literature-research agent that implements
[`METHODOLOGY_v2.md`](../METHODOLOGY_v2.md). It is the repository's agent — self-contained, with no
dependency on any other in-repo package (it shells out to the `codex` CLI and an embeddings endpoint).

> **Core principle.** The orchestrator owns the belief state and the control flow. Every LLM call is
> a pure function `f(task, context) → structured JSON` against a fixed schema. The model never
> decides the next step and never holds the belief state.

## Architecture (Blackboard)

```
CONTROL SHELL  orchestrator.py   loop: select → EXPLORE → ingest → promote → VERIFY → checkpoint → stop
BLACKBOARD     ledger.py         typed graph: Direction (frontier) + Claim (grounded) + SourceRef
EXECUTORS      executors.py      PRIOR · GROUND · EXPLORE · VERIFY · judges · patterns · finalize
PRIMITIVE      codex_exec.py     one `codex exec --output-schema` call → validated JSON + real USD
CALIBRATION    calibration.py    two-map isotonic calibrator (point + width) from verify outcomes
METRICS        metrics.py        checkpoint metrics: coverage / quality / progress / answeredness
SCHEMAS        schemas.py        Azure-strict JSON schemas for every executor
STEERING       steer.py          human-in-the-loop: SteerEvent + SteerSource, drained at the loop seams
CONSOLE        steer_server.py   stdlib HTTP backend + ui/steer.html browser console over the inbox
```

## Interactive steering

A human can steer a live run (new directions, scope, assumptions, reprioritization, budget, rare
verdicts) and runs are resumable — the orchestrator serializes full state every round. Flags:
`--steer-inbox PATH` (async), `--interactive` (blocking checkpoints), `--resume`. See
[`DESIGN_interactive.md`](DESIGN_interactive.md).

## The calibrate-then-allocate loop

1. **INIT** — parse the question's required fields, generate PRIOR candidate answers, and
   *prior-probe* them (verify first) to seed the calibrator.
2. **EXPLORE** — codex reads real sources via native web search and emits atomic claims, each with a
   resolvable `SourceRef` and an LLM-derived posterior (`confidence` + `[conf_low, conf_high]`).
3. **PROMOTE** — beam (top-k by calibrated confidence, exploit) + Thompson sampling from calibrated
   Beta posteriors over a resurfacing pool (explore) selects which claims to verify.
4. **VERIFY** — an adversarial literature check returns `confirmed` / `error` / `refuted`; outcomes
   recalibrate the point and width maps and feed the online-FDR budget. `error`/`refuted` spawn
   corrective directions.
5. **CHECKPOINT / CONVERGE** — stop only when the question is complete, no evidence is unresolved,
   and the frontier is exhausted; otherwise anneal (broad→deep) and continue.
6. **FINALIZE** — deterministic synthesis + a citation-verify sweep.

## Why it exists — the four baseline failures it fixes

| Failure | Mechanism |
|---|---|
| Codex confabulates authors/numbers | provenance gate (no claim graduates without a *resolvable* SourceRef) + adversarial `VERIFY` that re-fetches the source and checks author/venue/numbers + a final sweep |
| Surfaced hits left unranked | the frontier is explicit ledger state; the promotion gate pulls calibrated, sourced claims into the VERIFY pool |
| Stop-judge can't force work | the harness owns the loop; it runs to budget or to a **measured** convergence (complete ∧ no unresolved evidence ∧ frontier exhausted) |
| Plain codex competitive on coverage | codex *is* the `EXPLORE` executor — we keep its coverage and add structure, calibration, and verification |

## Run

```bash
cd graph-search-sliders-2       # repo root (holds the .env)

python3 -m src.cli \
  --question-file artifacts/genomics/pancreatic/question.txt \
  --run-dir v2_runs/genomic_pancreatic \
  --budget 50 -K 5 --rho 0.7
```

Optional reference-set recall — pass a JSON list of grounded findings to score against:

```bash
python3 -m src.cli ... --reference-set ref/genomic_pancreatic.json
```

### Outputs (in `--run-dir`)
- `answer.md` — deterministic synthesis: confirmed, sourced claims clustered by aspect, numbered refs (`✓` = source-verified).
- `ledger.json` — the full belief ledger (directions, claims, provenance, verification state).
- `run.json` — budget split, per-checkpoint snapshots, config.
- `tasks/NNNN_*/` — every codex call's prompt, schema, raw JSON output, transcript.
- `orchestrator.log` — the control trace.

## Knobs

`--budget` (total USD), `--rho` (explore/verify split, default 0.7), `-K` (best-first batch width),
`--max-rounds`, `--concurrency`, `--model` (default `gpt-5.4-mini`), `--env`. The calibration, FDR,
promotion (beam + Thompson), annealing, and convergence parameters live in the `Config` dataclass in
`orchestrator.py`.

## Notes / limitations

- Cost is **real USD**, read back from codex's own rollout per task dir (with a `tokens used`
  transcript fallback), priced at real per-model LiteLLM input/output rates.
- **No lexical proxies.** Every semantic judgment is a real model call: the `cos(emb(·), emb(·))`
  terms (context selection, frontier relevance/novelty, reference recall) use `text-embedding-3-large`
  (`embed.py` / `measure.py`); the discrete `covered(f)` / `q(d)` terms use codex LLM judges
  (`executors.judge_coverage` / `judge_forward`). `metrics.py` only does exact-count arithmetic over
  ledger state. Embedding spend is metered and charged to the explore pool.
- `GROUND` / `EXPLORE` / `VERIFY` run codex in `research` mode (native `web_search` + a network
  shell); `PRIOR` / judges run in read-only `reason` mode.

## Offline self-test (no codex / no spend)

```bash
python3 -m src.selftest
```
