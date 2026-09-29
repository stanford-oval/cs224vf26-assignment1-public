# The orchestration loop

This page describes the control shell in `orchestrator.py`: the single-threaded loop that owns run state and the belief ledger, and drives all work by calling stateless `codex` executors in parallel waves. It covers INIT, the best-first round loop, stall-driven deepening, termination, and finalize.

Related: [Frontier selection](./frontier-selection.md) · [Promotion and verification](./promotion-and-verification.md) · [Calibration and uncertainty](./calibration-and-uncertainty.md) · [Budget, cost, and the FDR brake](./budget-cost-fdr.md) · [The belief ledger](./belief-ledger.md) · [The executor roles](./executor-roles.md) · module notes: [orchestrator.py](../modules/orchestrator.md) · index: [docs](../README.md)

## The shape of the loop

The `Orchestrator` is a plain object (`orchestrator.py:149`). It holds the ledger, a two-pool budget, an embedder, a verify queue, an FDR wealth account, and a calibrator; it never runs LLM work itself. Every semantic step is a call into `executors.*`, which run `codex` as a pure function `(inputs) -> (data, usd)`. The orchestrator charges the returned `usd` to a budget pool and folds the `data` into the ledger. Concurrency comes from `_run_parallel`, a `ThreadPoolExecutor` sized by `cfg.concurrency` (`orchestrator.py:208`).

```
                 ┌──────────────────────────────────────────────────────────┐
   run()  ──────►│ INIT  (orchestrator.py:232)                              │
                 │   fields ‖ prior   → seed ledger                          │
                 │   GROUND key terms → glossary                            │
                 │   prior-probe      → bootstrap calibrator (Component G)   │
                 └──────────────────────────────────────────────────────────┘
                            │
                            ▼
   ┌───────────────── best-first ROUND loop (run(), orchestrator.py:322) ────────────────┐
   │ while not converged and round<max_rounds and open_directions and explore-work left: │
   │                                                                                      │
   │   1. size wave k from remaining explore-work budget           (orchestrator.py:326) │
   │   2. _select_batch(k)   embed-score → niche-boost → LLM rerank (orchestrator.py:380) │
   │   3. EXPLORE wave (parallel codex)                            (orchestrator.py:343) │
   │   4. ingest claims + new_directions into ledger              (orchestrator.py:356) │
   │   5. _rescore_corroboration  bump backlog on fresh evidence   (orchestrator.py:366) │
   │   6. _promote  beam + Thompson → verify_queue                (orchestrator.py:367) │
   │   7. _drain_verify_pool  FDR-gated verify wave (verify pool)  (orchestrator.py:371) │
   │   8. every checkpoint_cost $: _checkpoint → may set converged (orchestrator.py:373) │
   │   9. _save                                                                          │
   └──────────────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                 ┌──────────────────────────────────────────────────────────┐
                 │ FINALIZE (orchestrator.py:656)                            │
                 │   drain remaining verify → patterns → finalize_report     │
                 │   (deterministic synthesis fallback) → final _measure     │
                 └──────────────────────────────────────────────────────────┘
```

The public entry point is `run()` (`orchestrator.py:319`): it calls `init()`, spins the round loop, then calls `finalize(converged)`.

## Executor roles the loop actually calls

`executors.py` defines eleven functions. The loop wires **nine** of them. The other two are dead: `judge_forward` (`executors.py:292`) and `evaluate` (`executors.py:307`) are defined but never invoked anywhere in `orchestrator.py`. The `self.last_draft` field (`orchestrator.py:171`) is the vestige of the unwired evaluate path — it is assigned `""` in `__init__` and never read again. See [executor roles](./executor-roles.md) for the full catalogue.

| Executor | Called from | Phase | Pool charged |
|---|---|---|---|
| `fields` | `init` (`:234`) | INIT | explore |
| `prior` | `init` (`:234`) | INIT | explore |
| `ground` | `init` (`:255`) | INIT | explore |
| `verify` | `_prior_probe` (`:287`), `_drain_verify_pool` (`:569`) | INIT probe / VERIFY | explore (probe), verify (loop) |
| `rerank` | `_select_batch` (`:406`) | frontier selection | explore |
| `explore` | `run` (`:350`) | EXPLORE wave | explore |
| `patterns` | `_checkpoint` (`:637`), `finalize` (`:663`) | stall / finalize | explore |
| `judge_coverage` | `_measure` (`:607`) | checkpoint | explore |
| `finalize_report` | `finalize` (`:670`) | FINALIZE | explore |
| `judge_forward` | — | **dead** | — |
| `evaluate` | — | **dead** | — |

## INIT

`init()` (`orchestrator.py:232`) seeds the ledger before the loop begins, in three steps.

1. **Fields + prior, in parallel.** `executors.fields` extracts the required-answer fields (the "asks"); `executors.prior` returns open questions, a prior hypothesis, candidate answers, and key terms. `ledger.seed(...)` turns the prior into the initial OPEN directions; `uncovered_fields` is initialised to the full field list (`:248`).
2. **Ground key terms.** Up to `cfg.ground_terms` key terms (default 4) are defined by parallel `executors.ground` calls, writing into `ledger.glossary` (`:255`–`:262`). Skipped when `ground_terms=0` or the explore pool is empty.
3. **Prior probe (Component G).** `_prior_probe` (`:268`) verifies the top `cfg.prior_probe_k` candidate answers by confidence, using real `executors.verify` calls, to bootstrap the calibrator with genuine (prior-confidence → outcome) labels and to confirm cheap well-known priors early. Each verdict is applied by `_probe_apply` (`:298`), which appends a calibration label on terminal CONFIRMED/REFUTED and, on a confirmed claim that graduates, adds it as an early grounded claim. Probe verifies are charged to the **explore** pool (`:290`), not verify. If enough labels accrue, the calibrator is fit immediately (`:293`).

INIT's LLM and probe spend is entirely on the explore side of the budget.

## The round loop

Each round is a single best-first frontier expansion. The loop condition (`orchestrator.py:322`) requires all four to hold:

| Guard | Meaning |
|---|---|
| `not converged` | last checkpoint did not declare convergence |
| `round < cfg.max_rounds` | round cap (default 30) |
| `ledger.open_directions()` | at least one OPEN direction remains |
| `_explore_work_remaining() >= explore_task_usd * 0.5` | enough explore-work budget for at least a half-size task |

### 1. Wave sizing

`_explore_work_remaining()` (`orchestrator.py:313`) is `explore_cap * explore_work_frac - spent_explore` — the explore pool minus a reserve held back for the uncapped judge/rerank/embedding calls (`explore_work_frac` default 0.85). The wave size `k` is chosen so that even the worst case, every task hitting its watchdog cap, still fits the remaining budget (`:326`–`:333`):

```
target = explore_task_usd            # ~$3.5/task, also the budget_hint sent to codex
cap    = target * task_cap_mult      # per-task USD watchdog (~$6.3)
rem    = explore_work_remaining()
if rem < cap:  k, cap = 1, rem       # can't afford a full task → one shrunk task
else:          k = clamp(rem // cap, 1..K)
```

`K` caps the batch at 5 by default. See [Budget, cost, and the FDR brake](./budget-cost-fdr.md) for the pool mechanics and the killed-but-charged rule.

### 2. Select the batch

`_select_batch(k)` (`orchestrator.py:380`) ranks the OPEN frontier and returns the top `k`:

1. `measure.score_frontier` scores every OPEN direction by embedding promise.
2. **Niche boost (Component C):** an OPEN direction whose parent came back *thin* (nothing confirmed) or *contested* (confirmed≈refuted) gets `+cfg.niche_boost` (default 0.15), steering deeper where the parent was inconclusive (`:390`–`:395`).
3. **LLM rerank (opt-in, `cfg.rerank_frontier`):** if the frontier is small (`<= rerank_direct_max`, 60) the whole thing is LLM-ranked; otherwise the embedding promise shortlists the top `rerank_pool` (50) and only those are reranked (`:404`–`:412`). One `executors.rerank` call, charged to explore.

The mechanics live in [Frontier selection](./frontier-selection.md).

### 3. Explore wave

For each selected direction the loop builds a context set with `measure.select_context` and fires `executors.explore` in parallel (`orchestrator.py:343`–`:353`). Each task carries the USD `cap` as a watchdog plus `budget_hint=target` so codex self-limits. Embedding cost is flushed to the budget via `_charge_embed()` before the wave.

### 4. Ingest

For each returned result (`:356`–`:365`): a `None` (killed/failed task) closes the direction; otherwise `ledger.ingest` adds the claims with provenance and `ledger.add_directions` grafts child directions onto the frontier. The direction moves to CLOSED if it self-reported a dead end, else EXPLORED.

### 5. Corroboration re-scoring

`_rescore_corroboration` (`orchestrator.py:477`) is the resurfacing driver (Component B/C). For each fresh claim it uses the embedder to find still-unverified backlog claims stating the same assertion (cosine ≥ `corroborate_thresh`, default 0.88); `ledger.corroborate` applies the independent-source filter and a capped `+corroborate_per_source` (0.04) confidence bump, so a backlog claim that just gained independent support can climb back into promotion.

### 6. Promote

`_promote` (`orchestrator.py:504`) is beam search + Thompson sampling over the *resurfacing pool* — every gated, still-unverified claim not already queued (`_promotable_pool`, `:469`), i.e. this wave's fresh claims plus carried-over backlog. Per wave it allocates a verify budget (the beam width):

```
keep   = ceil(fresh_claims / eta)          # eta default 3.0
n_ex   = round(keep * promote_explore_frac)   # Thompson slots, frac default 0.34
n_beam = keep - n_ex                        # greedy top-k slots
```

The beam takes the top claims by **calibrated** confidence (`_score`, `:416`); the Thompson slots draw one sample per remaining claim from its Beta posterior (`_beta_params`, `:423`), so a weak claim with a wide interval can still be sampled. Both are niche-spread across aspects by `_pick_spread` (`:451`) so one crowded aspect cannot monopolise the verify budget. Promoted claims are appended to `verify_queue`. The scoring and posterior details are in [Promotion and verification](./promotion-and-verification.md) and [Calibration and uncertainty](./calibration-and-uncertainty.md).

### 7. Drain the verify pool

`_drain_verify_pool` (`orchestrator.py:540`) empties `verify_queue`, sorted by calibrated score (cheapest-to-test first), against the **verify** pool. It is gated by the online-FDR wealth account (`AlphaInvesting`, `:120`): each verify costs `alpha_min + alpha*(1-confidence)`, a confirmation pays `payout` back, and when wealth can't afford even the cheapest queued test the round's verifying halts (`:551`, `:597`). Verdicts are applied by `ledger.apply_verification` (bounded corrections via `correction_max_attempts`); terminal CONFIRMED/REFUTED outcomes append calibration labels, and the calibrator refits on cadence (`:589`). Details in [Budget, cost, and the FDR brake](./budget-cost-fdr.md).

Note the queue **persists across rounds** — claims not drained (FDR halt or exhausted verify budget) stay queued for the next round and for finalize.

### 8. Checkpoint

When cumulative spend since the last checkpoint reaches `checkpoint_cost` (default `budget/6`), `_checkpoint()` runs (`orchestrator.py:373`, `:623`). It calls `_measure` (`:606`), which runs one `executors.judge_coverage`, updates `uncovered_fields`, and builds a `metrics.Snapshot` (coverage, quality, backlog, progress-per-dollar, answeredness).

## Stall-driven deepening

A checkpoint that finds **progress stalled but coverage incomplete** does not stop — it digs deeper (`orchestrator.py:635`). When `snap.stalled` and the explore pool can afford it, `executors.patterns` distils cross-cutting abstract patterns; `ledger.spawn_from_patterns` turns their `direction`/`hypothesis` fields into genuinely new frontier directions, each nudged `+0.1` promise (`:637`–`:644`). This is the mechanism that keeps a shallow-saturated run productive instead of terminating prematurely.

## Termination

There are two ways the loop ends.

| Condition | Where | Effect |
|---|---|---|
| **Convergence** | `_checkpoint` (`:648`) | Only when `required_fields` is non-empty AND `coverage >= 0.999` AND `backlog == 0` AND `progress <= progress_eps`. Sets `converged=True`. |
| **Budget/round/frontier exhaustion** | `run` loop guard (`:322`) | round cap hit, no OPEN directions, or explore-work budget below half a task. |

Progress ≈ 0 **alone is not convergence** — that path triggers deepening (above), not a stop. Convergence requires the question fully answered, the verify backlog fully drained, and no new progress simultaneously.

## Finalize

`finalize(converged)` (`orchestrator.py:656`) produces the deliverable:

1. **Drain** any verify claims still queued (`:657`).
2. **Patterns** — if the loop never stalled into pattern distillation, run `executors.patterns` once for the synthesis section (`:662`).
3. **Report** — `executors.finalize_report` writes an outline-then-fill Markdown report; the outline is saved and a references block appended if missing (`:670`–`:681`). If the LLM report fails, fall back to `ledger.synthesize(only_confirmed=True)` — deterministic synthesis over confirmed claims only (`:682`–`:684`).
4. Write `answer.md`, run a final `_measure`, and `_save` (`:685`–`:692`).

## Key config knobs

Selected `Config` fields (`orchestrator.py:66`); the full list is in the [config reference](../reference/config-reference.md).

| Knob | Default | Role in the loop |
|---|---|---|
| `budget` | 50.0 | total USD |
| `rho` | 0.7 | explore/verify pool split |
| `K` | 5 | max explore batch size per round |
| `eta` | 3.0 | beam width = `ceil(fresh/eta)` |
| `promote_explore_frac` | 0.34 | fraction of beam width for Thompson slots |
| `explore_work_frac` | 0.85 | share of explore pool spent on EXPLORE (rest reserved for judges/embeddings) |
| `explore_task_usd` | 3.5 | target per EXPLORE task (drives wave size + hint) |
| `verify_task_usd` | 1.5 | target per VERIFY task |
| `task_cap_mult` | 1.8 | per-task watchdog cap = target × this |
| `max_rounds` | 30 | round cap |
| `progress_eps` | 0.02 | stall / convergence progress threshold |
| `checkpoint_every` | 0.0 | checkpoint spacing in USD (0 → `budget/6`) |
| `prior_probe_k` | 5 | candidate answers probed in INIT |
| `niche_boost` | 0.15 | promise boost for thin/contested-parent directions |
| `rerank_frontier` | True | LLM-rerank the frontier before batch selection |
| `promote_tau` | 0.6 | **DEPRECATED / unused** — kept only for CLI back-compat |

`promote_tau` (`orchestrator.py:71`) is a legacy hard floor that the current promotion path never reads.
