# Config knobs (reference)

Field-by-field reference of every `Config` knob and the `Budget` split that drive the orchestrator. Each knob lists its default, its meaning, and the exact `orchestrator.py` site(s) that read it (file:line relative to `src/`). Deprecated and unwired knobs are marked as such.

Related: [orchestrator.py](../modules/orchestrator.md) · [The orchestration loop](../architecture/orchestration-loop.md) · [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md) · [Executor output schemas (reference)](./schemas-reference.md) · [Claim lifecycle (reference)](./claim-lifecycle.md) · [documentation index](../README.md)

The `Config` dataclass is defined at `orchestrator.py:66-117`. It is constructed by the CLI (`cli.py`) and passed once to `Orchestrator.__init__` (`orchestrator.py:150`). The whole dataclass is serialized verbatim into `run.json` at `orchestrator.py:705`.

## Core loop / budget

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `budget` | `50.0` | Total USD budget for the run. Split into two pools by `rho`. Also sets the default checkpoint interval (`budget/6`) when `checkpoint_every` is 0. | `Budget(cfg.budget, cfg.rho)` `:156`; `checkpoint_cost` `:172` |
| `rho` | `0.7` | Explore/verify pool split. `explore_cap = budget*rho`, `verify_cap = budget*(1-rho)`. Default 70/30. | `Budget.__init__` `:41-44` (via `:156`) |
| `K` | `5` | Maximum EXPLORE directions per wave (wave size is further clamped by remaining explore-work budget). | wave sizing `:333` |
| `eta` | `3.0` | Beam width divisor. Per-wave verify budget `keep = ceil(fresh_claims / eta)` — roughly a 1/eta graduation rate. | `_promote` `:515` |
| `max_rounds` | `30` | Hard cap on EXPLORE rounds; the main `while` loop stops when reached. | loop guard `:322` |
| `concurrency` | `4` | Thread-pool worker count for parallel task fan-out; also caps the verify sub-wave size. | `_run_parallel` `:212`; verify wave `:558` |
| `task_timeout` | `1800` | Per-codex-task wall-clock timeout (seconds), passed to every executor via `_kw`. | `_kw` `:226` |
| `model` | `"gpt-5.4"` | Model id passed to every codex executor via `_kw`. | `_kw` `:225` |
| `env_file` | `DEFAULT_ENV` | Path to the env/credentials file; passed to the embedder and every executor. | Embedder `:157`; `_kw` `:225` |

## Per-task spend targets and caps

The orchestrator sizes each wave so that even if every task hits its watchdog cap the pool is not overrun (`orchestrator.py:329-333`). Every task also carries a `budget_hint` (the target) so codex self-limits, and a hard `usd_cap = target * task_cap_mult` watchdog. Killed tasks are still charged.

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `explore_task_usd` | `3.5` | Target USD per EXPLORE task; drives wave size and the `budget_hint`. Also the loop's minimum-affordable threshold (`* 0.5`) and the stall dig-deeper guard. | loop guard `:324`; wave target `:326`; stall guard `:635`; avg seed `:702` |
| `verify_task_usd` | `1.5` | Target USD per VERIFY task; drives the verify wave `budget_hint` and prior-probe cap. | prior probe `:277,288`; verify `:544`; avg seed `:703` |
| `ground_task_usd` | `2.0` | Target USD per GROUND task in INIT. Its cap (`* task_cap_mult`) is **also reused** as the affordability gate for the LLM frontier rerank call. | GROUND `:252,254,256`; rerank cap `:403` |
| `ground_terms` | `4` | How many key terms from PRIOR to GROUND during INIT (0 = skip; cheap-budget escape hatch). | key-term slice `:247` |
| `task_cap_mult` | `1.8` | Watchdog multiplier: per-task hard cap = target × this. Applied to ground, verify, explore, prior-probe, and rerank caps. | `:252,277,327,403,545` |

## Checkpoint / convergence

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `checkpoint_every` | `0.0` | USD spent between checkpoints. `0.0` falls back to `budget / 6.0` (≈6 checkpoints per run). | `checkpoint_cost` `:172`; trigger `:373` |
| `progress_eps` | `0.02` | Progress floor in (covered asks + confirmed) per USD. Below it a snapshot is flagged `stalled`; convergence also requires `progress <= progress_eps`. | snapshot build `:617`; converge test `:650` |

Convergence (`orchestrator.py:648-650`) requires **all** of: non-empty `required_fields`, `coverage >= 0.999`, `backlog == 0`, and `progress <= progress_eps`. A stall (progress≈0 with coverage&nbsp;<&nbsp;1) does **not** converge — it triggers the pattern-distillation dig-deeper branch (`:635-644`).

## Promotion (Component A + C)

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `promote_explore_frac` | `0.34` | Fraction of each wave's beam budget (`keep`) reserved for Thompson-sampling exploration slots; the rest is greedy beam. | `_promote` `n_ex` `:516` |
| `promote_kappa` | `8.0` | **Fallback** Beta concentration for Thompson sampling when a claim has neither a calibrated width nor a usable LLM credible interval. | `_beta_params` fallback `:439` |
| `promote_seed` | `0` | Base seed for reproducible Thompson draws. Actual RNG seed is `promote_seed + len(ledger.claims)`. | `_promote` RNG `:525` |
| `niche_boost` | `0.15` | Promise boost added to an open direction whose parent direction came back thin (nothing confirmed) or contested (confirmed≈refuted). `0` disables the boost. | `_select_batch` `:390,395` |

## Frontier rerank (LLM reranker)

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `rerank_frontier` | `True` | Opt-in LLM rerank of the frontier before batch selection. Runs only when > 1 open direction and explore budget exceeds the ground cap. | `_select_batch` gate `:404` |
| `rerank_direct_max` | `60` | If open directions ≤ this, LLM-ranks them all directly. | `_select_batch` `:405` |
| `rerank_pool` | `50` | Otherwise embedding-promise pre-filters to this top-N, then LLM-reranks that shortlist. | `_select_batch` `:405` |

## Online-FDR brake (Component E)

Passed into the `AlphaInvesting` pool at `orchestrator.py:159-160`. See the `AlphaInvesting` dataclass at `orchestrator.py:120-146` for the cost/settle math.

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `fdr_enabled` | `True` | Master switch for the alpha-investing verification gate. When off, the verify pool drains purely on budget. | `_drain_verify_pool` `:551,564,580` |
| `fdr_wealth0` | `0.5` | Initial alpha-wealth (error headroom) at run start. | `AlphaInvesting(wealth=...)` `:159` |
| `fdr_alpha` | `0.05` | Investment scale: a test costs `alpha_min + alpha*(1 - confidence)`, so speculative low-confidence tests cost more. | `:159` (→ `cost` `:135`) |
| `fdr_payout` | `0.05` | Reward added back to wealth on each confirmation. | `:160` (→ `settle` `:144`) |
| `fdr_alpha_min` | `0.005` | Floor cost so even a near-certain claim spends a little wealth to test. | `:160` (→ `cost` `:135`) |
| `correction_max_attempts` | `2` | Bound on the error→correct→re-verify loop inside `apply_verification` (optional-stopping / peeking guard). | prior-probe `:302`; verify `:579` |

The verify queue is sorted by calibrated score descending, so index `[0]` is the cheapest FDR test; if even that is unaffordable the round halts (`orchestrator.py:551-553`).

## Calibration (Component B)

The `Calibrator` is constructed with `min_labels` at `orchestrator.py:161`. Labels are `(raw_confidence, stated_interval_width, outcome)` tuples accrued from VERIFY confirm/refute verdicts.

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `calibrate_enabled` | `True` | Master switch. When off, the promotion score is raw self-reported confidence (`_score` `:419-421`) and no refit runs. | `:293,419,434,589` |
| `calibrate_min_labels` | `12` | Stay identity map until this many confirm/refute labels accrue. | `Calibrator(min_labels=...)` `:161`; prior-probe fit `:293`; refit gate `:590` |
| `calibrate_refit_every` | `6` | Refit the isotonic map every N new labels past the minimum. The cadence advances only when a fit actually lands. | refit gate `:591` |

## Corroboration re-scoring (Component B/C)

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `corroborate_enabled` | `True` | Master switch for raising a backlog claim's confidence when a fresh claim restates it with an independent source. | `_rescore_corroboration` `:482` |
| `corroborate_thresh` | `0.88` | Text-embedding cosine above which a fresh claim counts as the same assertion as a backlog claim. `rank()` is sorted desc, so the scan breaks at the first miss. | `:495` |
| `corroborate_per_source` | `0.04` | Confidence bump per independent corroborating source (diminishing; applied in `ledger.corroborate`). | `:498` |

## Prior probe (Component G)

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `prior_probe_enabled` | `True` | Verify top prior candidate answers during INIT to bootstrap the calibrator. Skips if disabled, no prior candidates, or budget is tight. | `_prior_probe` `:273` |
| `prior_probe_k` | `5` | How many top-confidence candidate answers to probe (charged to the explore pool). | `_prior_probe` `:276` |

## Deprecated / unwired knobs

| Knob | Default | Status | Detail |
|---|---|---|---|
| `promote_tau` | `0.6` | **Deprecated, unused.** | Legacy hard promotion floor. Defined at `:71` and comment-marked DEPRECATED. Not read anywhere in `orchestrator.py`. Only kept for CLI back-compat (`cli.py:49`) and displayed in the trajectory HTML config table (`build_trajectory_html.py:261`). Promotion is now beam + Thompson, not a threshold. |
| `reference_set` | `[]` | **Not consumed by the orchestrator.** | Populated from a JSON file by the CLI (`cli.py:43-52`) and stored on `Config`, but no code path in `orchestrator.py` reads it. It is serialized into `run.json` only. |
| `rubric` | (default axes string, `:93-94`) | **Not consumed by the orchestration loop.** | The rubric feeds `executors.evaluate` (`executors.py:307,315`) and is shown by `stage_to_portal.py:138`. But the orchestrator **never calls `executors.evaluate`** (see below), so within a normal run the rubric only affects portal display, not steering. |

## Executor roles the loop actually calls

For context on which knobs matter: the live loop invokes only these executors — `fields`, `prior`, `ground`, `verify`, `explore`, `rerank`, `judge_coverage`, `patterns`, `finalize_report` (`orchestrator.py:235,236,255,287,350,406,569,607,637,663,670`). Notably `executors.evaluate` and any `judge_forward`-style checkpoint judge are **never called** by the orchestrator — the §7 checkpoint was collapsed to a single coverage judge plus counts (`_measure` `:606-620`). This is why `rubric` has no steering effect in a normal run, and why `self.last_draft` (`:171`) is set once and never updated.

## `Budget` — the two-pool split

`class Budget` at `orchestrator.py:37-63`. Constructed as `Budget(cfg.budget, cfg.rho)` (`:156`).

| Field / method | Meaning |
|---|---|
| `total` | `cfg.budget` — total USD. |
| `explore_cap` | `total * rho` — breadth pool cap (`:43`). |
| `verify_cap` | `total * (1 - rho)` — depth pool cap (`:44`). |
| `spent_explore` / `spent_verify` | Running spend per pool; `spend(pool, usd)` routes to verify only when `pool == "verify"`, else explore (`:48-53`). |
| `explore_remaining()` / `verify_remaining()` | `cap - spent` for the pool (`:55-59`). |
| `spent` (property) | `spent_explore + spent_verify` (`:61-63`). |

Charging notes grounded in the code:

- Embedding/measurement instrument cost is charged to the **explore** pool via `_charge_embed` (`:191-195`).
- The EXPLORE-work reserve is `explore_cap * explore_work_frac - spent_explore` (`_explore_work_remaining` `:313-316`); the remaining `1 - explore_work_frac` is held back for uncapped judge/evaluate/embedding calls.
- The prior probe is charged to the **explore** pool even though it runs VERIFY tasks (`:290`).
- Killed tasks (returned as `(None, usd>0)`) are still charged (`_take` `:197-206`).

### `explore_work_frac`

| Knob | Default | Meaning | Consumed at |
|---|---|---|---|
| `explore_work_frac` | `0.85` | Fraction of the explore pool spendable on EXPLORE waves; the rest is reserved for the uncapped judge/evaluate/embedding measurement calls so total stays within the pool. | `_explore_work_remaining` `:316` |

```
budget = 50.0
  ├── explore_cap = budget * rho            = 35.0   (rho = 0.7)
  │     ├── EXPLORE-work reserve            = explore_cap * explore_work_frac = 29.75
  │     └── held back (judges/embeds/probe) = explore_cap * (1 - explore_work_frac) = 5.25
  └── verify_cap  = budget * (1 - rho)      = 15.0
        └── gated additionally by the online-FDR alpha-wealth pool
```
