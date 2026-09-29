# System overview

This page is the entry point after the [documentation index](../README.md). It explains what methodology_v2 is — a Blackboard architecture in which a plain-Python orchestrator owns all state and control flow and codex is a stateless, schema-constrained executor — and how the three parts (belief ledger, executor tasks, control loop) fit together across a run.

Related: [The belief ledger](./belief-ledger.md) · [The executor roles](./executor-roles.md) · [The orchestration loop](./orchestration-loop.md) · [orchestrator.py](../modules/orchestrator.md) · [Methodology v2 (design rationale)](../design/methodology.md)

## What the system is

methodology_v2 is a budget-bounded literature-research agent. It answers one research question by spending a fixed USD budget on many small LLM calls, accumulating grounded, source-verified claims, and rendering a report. Its design premise (from the baseline study that motivated it — see [design/methodology.md](../design/methodology.md)) is that plain codex already retrieves well but confabulates provenance, under-integrates its own findings, and cannot be forced to keep working. The fix is to take the loop and the state away from the model:

> The orchestrator owns the belief state and the control flow. Every LLM call is a pure function `f(task, context) → structured JSON` against a fixed schema. The model never decides the next step and never holds the belief state.

Concretely, the model is invoked only through `codex exec --output-schema` calls that return validated JSON; all bookkeeping, scheduling, budget accounting, promotion, and stop logic are deterministic Python.

## Blackboard architecture

The system is a classic Blackboard: a shared structured memory, specialist workers that read/write it, and a control shell that schedules them.

```
        ┌──────────────────── CONTROL SHELL — orchestrator.py ─────────────────────┐
        │  init → [ select batch → EXPLORE → ingest → promote → VERIFY →           │
        │           checkpoint(measure, steer) → stop? ] → finalize                 │
        └───────────────┬───────────────────────────────────────────┬──────────────┘
                        │ reads / writes                             │ dispatches f(task,ctx)
                ┌───────▼─────────┐                        ┌─────────▼───────────┐
                │  BELIEF LEDGER   │                       │  EXECUTORS (codex)   │
                │  ledger.py       │◄──── validated ───────│  executors.py        │
                │  Direction (□)   │      JSON results     │  fields prior ground │
                │  Claim  + Source │                       │  explore verify …    │
                └──────────────────┘                       └──────────────────────┘
```

| Blackboard role | Module | Doc |
|---|---|---|
| Shared memory (blackboard) | `ledger.py` | [The belief ledger](./belief-ledger.md), [ledger.py](../modules/ledger.md) |
| Knowledge sources (workers) | `executors.py` | [The executor roles](./executor-roles.md), [executors.py](../modules/executors.md) |
| Control shell (scheduler) | `orchestrator.py` | [The orchestration loop](./orchestration-loop.md), [orchestrator.py](../modules/orchestrator.md) |

The orchestrator class is defined at `orchestrator.py:149`; its `run()` method (`orchestrator.py:319`) is the whole lifecycle.

## Part 1 — the belief ledger (state)

The ledger is a typed graph, not a scratchpad. Two first-class objects plus provenance carry all state; there is deliberately no `Entity` type — grouping is done with free-form `aspects[]` tags so the ledger works for open problems and comparisons as well as entity-ranking tasks.

| Object | Purpose | Key fields |
|---|---|---|
| `Direction` | the frontier (a tree via `parent_id`) | `question_text`, `status`, `promise`, `parent_id`, `produced_claims` |
| `Claim` | an atomic grounded finding | `text`, `stance`, `aspects`, `numbers`, `evidence` (SourceRef), `confidence`, `conf_lo/conf_hi`, `verification`, `direction_id` |
| `SourceRef` | provenance (anti-confabulation) | `title/authors/year/venue`, `doi|pmid|pmc|url`, `verified`, `quote`/`line_range` |

A `Direction` moves through these statuses (imported at `orchestrator.py:31`):

| Direction status | Meaning |
|---|---|
| `OPEN` | on the frontier, not yet expanded (default) |
| `EXPLORING` | selected into the current wave |
| `EXPLORED` | expanded, produced claims |
| `CLOSED` | dead end (or its EXPLORE call failed) |
| `PROMOTED` | produced a claim that entered the verify queue |

A `Claim`'s `verification` field is one of `UNVERIFIED`, `CONFIRMED`, `REFUTED`. A claim cannot graduate to verification or enter the final answer without a resolvable SourceRef (`Claim.graduates()`), which is the provenance gate. See [claim-lifecycle.md](../reference/claim-lifecycle.md) and [schemas-reference.md](../reference/schemas-reference.md) for the full field-by-field reference.

## Part 2 — the executor tasks (codex as a pure function)

Each executor is a stateless call: it takes a task spec plus a *slice* of the ledger and returns schema-validated JSON. The orchestrator wires nine roles into the loop:

| Executor | Called from | Returns (shape) |
|---|---|---|
| `fields` | INIT | `required_fields[]` parsed from the question |
| `prior` | INIT | `{prior_hypothesis, candidate_answers[], key_terms[], open_questions[]}` |
| `ground` | INIT | `{definition, source}` for one key term |
| `explore` | main loop | `{claims[] (w/ SourceRef+numbers), new_directions[], dead_end}` |
| `verify` | prior-probe + verify pool | `{confirmed, corrected_numbers, corrected_source, refutation?, confidence}` |
| `rerank` | frontier selection | LLM promise scores for a shortlist of open directions |
| `judge_coverage` | checkpoint / finalize | per-field covered/uncovered judgement |
| `patterns` | stall handler + finalize | cross-cutting patterns that seed deeper directions / the report |
| `finalize_report` | finalize | outline-then-fill report markdown |

Two executor roles are **defined in `executors.py` but never called** anywhere in the package: `judge_forward` (`executors.py:292`) and `evaluate` (`executors.py:307`). The design doc's EVALUATE checkpoint — self-evaluate the draft against the previous one, emit `corrective_directions`, and `rollback_if(regressions)` — is therefore **not wired**. The real checkpoint (Part 3) uses `judge_coverage` plus deterministic counts and a `patterns` stall-handler instead, and never rolls back. Treat the four-axis EVALUATE / pairwise-temporal machinery in [design/methodology.md](../design/methodology.md) §7 as design intent, not running code. See [The executor roles](./executor-roles.md) for details.

## Part 3 — the control loop (behavior)

The orchestrator drives INIT → main loop → finalize. Budget is split into two pools (Hyperband-style): `B_explore` (breadth) and `B_verify` (depth), default 70/30. Embedding and judge/LLM-instrument spend is charged to the explore pool (`orchestrator.py:191`).

```
INIT  (orchestrator.py:232)
  parse fields ‖ PRIOR              seed frontier from open_questions + hypothesis
  GROUND key terms                  glossary
  prior-probe: VERIFY top candidates → bootstrap the calibrator

MAIN LOOP  (orchestrator.py:319, until converged | max_rounds | explore pool low)
  ┌─ size wave to what the pool can afford at cap
  │  select_batch(k)   embedding promise + niche boost + optional LLM rerank
  │  EXPLORE(d, ctx)    parallel; ingest claims+provenance, spawn child directions
  │  rescore_corroboration   bump backlog claims that fresh independent sources support
  │  promote(batch)     beam (top-k calibrated conf) + Thompson sampling → verify queue
  │  drain_verify_pool  parallel VERIFY, cheapest-first, gated by the online-FDR wealth
  │  every checkpoint_cost $:  measure → steer (dig deeper if stalled) → stop?
  └─ save ledger.json / run.json

FINALIZE  (orchestrator.py:656)
  drain remaining verify queue → patterns → finalize_report (fallback: deterministic
  synthesize of CONFIRMED claims) → answer.md
```

Promotion is **not** the design doc's fixed `PROMOTE_TAU` confidence floor. That knob is retained only for CLI back-compat and is marked deprecated/unused (`orchestrator.py:71`). Actual promotion (`_promote`, `orchestrator.py:504`) gives each wave a beam width `keep = ceil(fresh_claims / eta)` (eta default 3.0), fills most slots by calibrated-confidence rank and a reserved fraction (`promote_explore_frac`, default 0.34) by Thompson sampling each claim's Beta posterior, spread across aspect niches. The verify pool (`_drain_verify_pool`, `orchestrator.py:540`) runs cheapest-first and stops when the alpha-investing FDR wealth (`AlphaInvesting`, `orchestrator.py:120`) can no longer afford even the cheapest test. These are covered in [Promotion and verification](./promotion-and-verification.md) and [Budget, cost, and the FDR brake](./budget-cost-fdr.md).

The checkpoint (`_checkpoint`, `orchestrator.py:623`) measures coverage via `judge_coverage` and counts (no `evaluate` call), and if progress has stalled while coverage is still incomplete it distils `patterns` into deeper directions rather than stopping. Convergence requires all three of: required fields fully covered, verify backlog empty, and per-dollar progress at or below `progress_eps` (`orchestrator.py:648`). See [The orchestration loop](./orchestration-loop.md) and [Frontier selection](./frontier-selection.md).

## Run lifecycle at a glance

| Phase | Entry | What it produces |
|---|---|---|
| INIT | `init()` `:232` | required fields, seed frontier, glossary, calibrator bootstrap labels |
| Main loop | `run()` `:319` | grounded claims, verified/refuted labels, checkpoint snapshots |
| Finalize | `finalize()` `:656` | `answer.md`, final metric snapshot |

Outputs land in `--run-dir`: `answer.md`, `ledger.json`, `run.json` (config + per-checkpoint metric trajectory), `tasks/NNNN_*/` (every codex call's prompt/schema/output/transcript), and `orchestrator.log`.

## Selected config knobs

Full list in [config-reference.md](../reference/config-reference.md); the `Config` dataclass is at `orchestrator.py:66`.

| Knob | Default | Role |
|---|---|---|
| `budget` | 50.0 | total USD |
| `rho` | 0.7 | explore/verify pool split |
| `K` | 5 | best-first batch width |
| `eta` | 3.0 | promotion beam width = ceil(fresh/eta) |
| `promote_explore_frac` | 0.34 | verify slots reserved for Thompson sampling |
| `promote_tau` | 0.6 | **deprecated, unused** (legacy hard floor) |
| `explore_work_frac` | 0.85 | share of explore pool spent on EXPLORE waves |
| `explore_task_usd` / `verify_task_usd` / `ground_task_usd` | 3.5 / 1.5 / 2.0 | per-task target spend |
| `task_cap_mult` | 1.8 | per-task watchdog cap = target × this |
| `fdr_enabled` / `fdr_wealth0` / `fdr_alpha` | True / 0.5 / 0.05 | online-FDR brake on the verify stream |
| `calibrate_enabled` / `calibrate_min_labels` | True / 12 | isotonic confidence recalibration |
| `corroborate_enabled` / `corroborate_thresh` | True / 0.88 | resurface backlog claims on independent corroboration |
| `prior_probe_enabled` / `prior_probe_k` | True / 5 | verify top priors in INIT to seed calibration |
| `rerank_frontier` | True | LLM-rerank the frontier before batch selection |
| `progress_eps` | 0.02 | per-dollar progress floor for convergence |
| `max_rounds` / `concurrency` | 30 / 4 | loop and fan-out limits |
| `model` | gpt-5.4 | codex model id |

## Component map

Every architecture and module doc, and where it sits in the system.

| Concern | Architecture doc | Module doc(s) |
|---|---|---|
| This overview | [System overview](./overview.md) | [orchestrator.py](../modules/orchestrator.md) |
| State / typed graph | [The belief ledger](./belief-ledger.md) | [ledger.py](../modules/ledger.md) |
| Codex as pure function | [The executor roles](./executor-roles.md) | [executors.py](../modules/executors.md), [schemas.py](../modules/schemas.md), [codex_exec.py](../modules/codex_exec.md) |
| Control flow | [The orchestration loop](./orchestration-loop.md) | [orchestrator.py](../modules/orchestrator.md), [cli.py](../modules/cli.md) |
| Promotion / verification | [Promotion and verification](./promotion-and-verification.md) | [ledger.py](../modules/ledger.md) |
| Confidence calibration | [Calibration and uncertainty](./calibration-and-uncertainty.md) | [calibration.py](../modules/calibration.md) |
| Budget / cost / FDR | [Budget, cost, and the FDR brake](./budget-cost-fdr.md) | [codex_exec.py](../modules/codex_exec.md) |
| Frontier scoring | [Frontier selection](./frontier-selection.md) | [embed.py](../modules/embed.md), [measure.py](../modules/measure.md) |
| Metrics / snapshots | (in loop + budget docs) | [metrics.py](../modules/metrics.md) |
| Offline checks / tooling | — | [selftest.py](../modules/selftest.md), [HTML inspectors](../modules/html-inspectors.md), [stage_to_portal.py](../modules/stage_to_portal.md) |

Reference material: [Executor output schemas](../reference/schemas-reference.md) · [Config knobs](../reference/config-reference.md) · [Claim lifecycle](../reference/claim-lifecycle.md).

Design rationale (intent, not all implemented): [Methodology v2](../design/methodology.md) · [Promotion redesign: Components A–G](../design/promotion-redesign.md) · [Formal algorithm spec](../design/algorithm-spec.md).
