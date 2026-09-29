# Budget, cost, and the FDR brake

This page describes the resource-control subsystem: the two-pool USD budget, how real
per-model cost is metered from codex's own rollout, how each wave is sized so it can
never overrun its pool, and the online-FDR "error wealth" that throttles speculative
verifies. It also explains why the budget — not a convergence test — is the signal that
actually stops the run.

Related: [The orchestration loop](./orchestration-loop.md) · [Promotion and verification](./promotion-and-verification.md) · [The executor roles](./executor-roles.md) · [Config knobs (reference)](../reference/config-reference.md) · [codex_exec.py](../modules/codex_exec.md) · [orchestrator.py](../modules/orchestrator.md)

---

## The shape of the problem

The agent has a fixed dollar budget and must spend it on two competing activities:
breadth (EXPLORE, which discovers claims and new directions) and depth (VERIFY, which
checks promoted claims against real sources). Every LLM call costs real, variable money
that is only known *after* the call returns. The subsystem therefore has three jobs:

1. **Partition** the budget so depth cannot starve breadth or vice versa — the two-pool
   `Budget`.
2. **Meter** each call in real USD at the correct per-model input/output rate, and charge
   it to the right pool — `codex_exec.spent_usd` plus `Orchestrator._take`.
3. **Ration** speculative verifies so the run does not burn depth budget confirming
   long-shot claims — the `AlphaInvesting` error-wealth brake (Component E).

```
                 total budget (Config.budget, default $50)
                              │  split by rho (default 0.7)
             ┌────────────────┴─────────────────┐
        B_explore (70%)                     B_verify (30%)
   ┌─────────┴──────────┐                        │
 EXPLORE waves     judges / embeddings       VERIFY waves
 (explore_work_frac  (the uncapped 0.15       gated by the
  = 0.85 of pool)    reserve)                 FDR error-wealth
                                              (AlphaInvesting)
```

The frontier reranker and the INIT prior-probe are *capped* calls that also charge to
the explore pool, but they are **not** part of the 0.15 uncapped cushion: each is gated on
`explore_remaining()` and bounded by its own per-task USD cap (see below).

---

## The two pools: `Budget`

`Budget` (orchestrator.py:37-63) holds one number per pool and never blocks a spend — it
records cost and exposes remaining headroom that the loop reads before deciding what to
do next.

| Field / method | Meaning |
| --- | --- |
| `total` | The full budget (`Config.budget`, default `50.0`). |
| `explore_cap` | `total * rho` — breadth pool (default 70%). |
| `verify_cap` | `total * (1 - rho)` — depth pool (default 30%). |
| `spent_explore`, `spent_verify` | Running USD charged to each pool. |
| `spend(pool, usd)` | Adds `usd` to `spent_verify` if `pool == "verify"`, else to `spent_explore`. |
| `explore_remaining()`, `verify_remaining()` | Cap minus spent. |
| `spent` (property) | `spent_explore + spent_verify`. |

`rho` is `Config.rho` (default `0.7`, orchestrator.py:69), so the default split is 70/30.
Instrument cost — embeddings, the frontier reranker, the coverage/pattern judges, and the
INIT prior-probe verifies — is all charged to the **explore** pool. The verify pool is
reserved for actual VERIFY executor calls. Notably the INIT prior probe runs VERIFY-style
calls but charges them to explore (orchestrator.py:290), because it is calibration
bootstrapping, not depth work.

### The explore reserve

Not all of the explore pool is spendable on EXPLORE waves. `_explore_work_remaining`
(orchestrator.py:313-316) holds back a fraction for the uncapped judge/embedding
measurement calls (judge_coverage, patterns, and embeddings):

```
explore_work_remaining = explore_cap * explore_work_frac − spent_explore
                                        └ default 0.85 ┘
```

So EXPLORE waves may consume at most 85% of the explore pool; the remaining ~15% is a
cushion for the judges and embeddings, which have no per-call USD cap. The frontier
reranker is **not** in this uncapped set: it is capped at `ground_task_usd * task_cap_mult`
(~$3.6) and only runs when `explore_remaining()` exceeds that cap (orchestrator.py:403-407);
its cost still charges to the explore pool. The verify pool has no analogous reserve — it is
spent entirely on VERIFY.

### Charging a result to a pool

Executor results arrive as `(data, usd)` tuples. `_take` (orchestrator.py:197-206) calls
`Budget.spend` and returns just `data`. A task killed at its USD cap returns
`(None, usd>0)`; it is **still charged** — the money was really spent. Embedding cost is
tracked separately by the `Embedder` and swept into the explore pool by `_charge_embed`
(orchestrator.py:191-195), which charges only the delta since the last sweep.

---

## Real-USD cost metering (`codex_exec`)

Cost is not estimated from a token budget — it is read back as the real dollar figure
codex billed for the task, keyed on the model that actually ran.

### Per-model input/output rates

`codex_exec.py:33-39` holds a rate table in **$ per 1M tokens**, priced input and output
**separately** because output (reasoning) tokens dominate and cost ~6× input:

| Model | Input $/1M | Output $/1M |
| --- | --- | --- |
| `gpt-5`, `gpt-5.4`, `gpt-5.5` | 2.50 | 15.0 |
| `gpt-5.2-codex`, `gpt-5.3-codex` | 2.50 | 15.0 |
| `gpt-5-mini`, `gpt-5.4-mini` | 0.75 | 4.50 |
| `gpt-5-nano`, `gpt-5.4-nano` | 0.20 | 1.25 |
| (unknown model) | 2.50 | 15.0 (`_DEFAULT_RATES_M`) |

`rates_for(model)` returns the `(input, output)` per-token pair. `rate_for(model)`
(codex_exec.py:48-51) is a single blended `$/token` (`0.3·input + 0.7·output`) used **only**
on the transcript-only fallback path. The default model is `gpt-5.4` (`Config.model`,
orchestrator.py:89).

### Reading the bill: `spent_usd`

`spent_usd(run_dir)` (codex_exec.py:100-131) finds the codex rollout JSONL whose session
`cwd` matches this task's directory, takes the most recent one, and reads the **cumulative**
`total_token_usage` (keeping the last record). Billable input excludes cached tokens:

```
billable_input = input_tokens − cached_input_tokens
billed_usd     = billable_input * rate_in(model) + output_tokens * rate_out(model)
```

If no matching rollout is found (`usd <= 0`), it falls back to scraping a
`tokens used` count from the transcript and pricing it at the blended `rate_for`
(codex_exec.py:302-305).

### Retries and soft failures

`run_task` (codex_exec.py:204-214) retries a task up to `retries` (default 2) times on a
soft failure (`data is None`), **accumulating** the (usually ~0) cost of each failed attempt
so the charge reflects total spend. Hard `CodexError` (misconfiguration) propagates without
retry. A task that produces no parseable schema output returns `(None, usd)`
(codex_exec.py:309-316) — again, charged but yielding no data.

### The per-task watchdog

`usd_cap` installs a backstop. A daemon thread (codex_exec.py:277-291) polls `spent_usd`
every 5 seconds and, once spend crosses the cap, SIGTERM/SIGKILLs the process group. This
bounds a single runaway task; it does **not** protect the pool, which is the wave-sizing
job below. Per-task caps are set as `target * task_cap_mult` (default `1.8`), i.e. ~$6.3
for EXPLORE, ~$2.7 for VERIFY, ~$3.6 for GROUND.

---

## Wave sizing: never overrun a pool

The watchdog caps one task; wave sizing caps a whole parallel wave so that even if every
task in it hits its cap, the wave still fits the pool.

**EXPLORE waves** (orchestrator.py:322-334):

```
rem = explore_work_remaining()
cap = explore_task_usd * task_cap_mult          # worst-case per task
if rem < cap:        k = 1;  cap = rem           # only room for one, shrink its cap
else:                k = max(1, min(K, rem // cap))   # as many as fit, capped at K
```

So `k * cap <= rem` always holds: the wave's worst case fits the remaining explore work
budget. `K` (default 5) is the hard ceiling on wave width; `concurrency` (default 4) is the
thread-pool width.

**VERIFY waves** (orchestrator.py:548-566) size the same way against `verify_remaining()`
with `cap0 = verify_task_usd * task_cap_mult`, but width is capped at `concurrency` (not
`K`) and each wave is additionally gated by the FDR brake below.

Each EXPLORE/VERIFY/GROUND task also receives a `budget_hint` (the *target* spend, e.g.
`explore_task_usd = 3.5`) so codex self-limits toward the target, while the cap is the hard
kill line above it. (The judge/reason calls — coverage, patterns, fields/prior, rerank,
finalize — carry no `budget_hint`.)

---

## The FDR brake: `AlphaInvesting` (Component E)

The hazard: claims resurface and get re-verified, and the same belief can be tested many
times. Under naive repeated testing the false-confirmation rate over the stream is
uncontrolled (a multiple-testing / optional-stopping problem). `AlphaInvesting`
(orchestrator.py:120-146) is an online-FDR "error wealth" account (Foster & Stine style)
that makes speculative verifies *cost* wealth and confirmations *pay* it back.

| Field | Config source | Default | Role |
| --- | --- | --- | --- |
| `wealth` | `fdr_wealth0` | `0.5` | Current error-wealth headroom. |
| `alpha` | `fdr_alpha` | `0.05` | Investment scale; a fully-speculative test costs this. |
| `payout` | `fdr_payout` | `0.05` | Reward added back on a confirmation. |
| `alpha_min` | `fdr_alpha_min` | `0.005` | Floor so even a near-certain test costs a little. |

The cost of a test scales with how *speculative* it is (low confidence = expensive):

```
cost(c)  = alpha_min + alpha * (1 − c)        # c = calibrated confidence, clamped [0,1]
                                              # cheapest (c=1):  0.005
                                              # dearest  (c=0):  0.055
can_afford(c) = wealth >= cost(c)
settle(c, confirmed):
    wealth -= cost(c)
    if confirmed: wealth += payout
    wealth  = max(0, wealth)
```

### How it gates the verify pool

`_drain_verify_pool` (orchestrator.py:540-604) sorts the queue by **calibrated confidence
descending**, so `verify_queue[0]` is the *cheapest* possible test under the FDR cost curve.

```
   drain loop (per round)
   ─────────────────────────────────────────────
   while verify_remaining() >= verify_task_usd*0.5:
       if fdr_enabled and not fdr.can_afford(score(queue[0])):
              ── can't afford even the cheapest → HALT this round
       size a wave (dollar-bounded); fill it cheapest-first,
              stopping early if the next claim is unaffordable
       run wave; for each result:
              apply_verification(...)
              fdr.settle(promo_score, confirmed?)   ← wealth moves here
```

The dynamics: a run that keeps confirming claims earns `payout` back and stays solvent, so
verification continues. A run that mostly refutes (or tests long-shots) drains wealth until
only high-confidence tests are affordable, and eventually nothing is — the round halts with
claims still queued (logged as "VERIFY halted by FDR budget"). This bounds how many
speculative or repeated verifies can run before the ledger has *earned* the right to spend
more error budget.

Two honest caveats:

- The FDR account is consulted **only** in `_drain_verify_pool`. The INIT prior probe
  (orchestrator.py:268-297) runs its own VERIFY calls but does **not** call `fdr.settle` or
  `can_afford` — it is outside the brake.
- The whole mechanism is behind `fdr_enabled` (default `True`); with it off, verification is
  bounded only by the dollar pool.

---

## Why the budget is the stop signal

There are two ways the run can end, and in practice the dollar budget is the dominant one.

**The main loop condition** (orchestrator.py:322-324) keeps iterating only while *all* of:

```
not converged
and round < max_rounds                                  (default 30)
and ledger.open_directions()                            (frontier not empty)
and explore_work_remaining() >= explore_task_usd * 0.5  (explore pool not drained)
```

The last clause is the usual terminator: once the explore work budget falls below half a
task's target spend, the loop exits regardless of coverage. Depth then gets a final
`_drain_verify_pool` in `finalize` (orchestrator.py:657), which itself stops when the verify
pool (or FDR wealth) is spent.

**Explicit convergence** (`_checkpoint`, orchestrator.py:648-650) sets `converged` only when
*every* condition holds:

| Condition | Meaning |
| --- | --- |
| `ledger.required_fields` non-empty | never "converge" if field-parsing failed (0 asks). |
| `coverage >= 0.999` | every required field is answered. |
| `backlog == 0` | the verify queue is fully drained. |
| `progress <= progress_eps` (default `0.02`) | no new covered-asks/confirmations per dollar. |

This is a strict "fully answered, fully checked, nothing new arriving" test; a stalled but
incomplete run does **not** converge — instead the checkpoint distils cross-cutting patterns
to dig deeper (orchestrator.py:635-644). Checkpoints fire every `checkpoint_cost` dollars of
total spend, which defaults to `budget / 6` when `checkpoint_every` is `0.0`
(orchestrator.py:172).

Because convergence is so strict, most runs terminate by exhausting the explore pool (or
hitting `max_rounds` / running out of open directions), not by declaring victory. The budget
is therefore the real convergence controller: it decides both how wide each wave is and when
the search ends.

```
   spend explore pool ──▶ waves shrink as rem falls ──▶ rem < 0.5·task ──▶ loop exits
   spend verify pool ──▶ FDR wealth + pool both gate ──▶ final drain ──▶ verify ends
```

---

## Config knobs at a glance

All defined on `Config` (orchestrator.py:66-118). Costs are in USD.

| Knob | Default | Effect |
| --- | --- | --- |
| `budget` | `50.0` | Total spend ceiling. |
| `rho` | `0.7` | Explore/verify split (0.7 → 70/30). |
| `explore_work_frac` | `0.85` | Share of explore pool spendable on EXPLORE waves. |
| `explore_task_usd` | `3.5` | Target spend / EXPLORE (sizes waves + hint). |
| `verify_task_usd` | `1.5` | Target spend / VERIFY. |
| `ground_task_usd` | `2.0` | Target spend / GROUND (and rerank cap basis). |
| `task_cap_mult` | `1.8` | Hard per-task cap = target × this. |
| `K` | `5` | Max EXPLORE wave width. |
| `concurrency` | `4` | Thread-pool width (and max VERIFY wave width). |
| `checkpoint_every` | `0.0` | Checkpoint cadence in $ (0 → `budget/6`). |
| `progress_eps` | `0.02` | Below this progress/$ counts as stalled / no-progress. |
| `max_rounds` | `30` | Hard round ceiling. |
| `fdr_enabled` | `True` | Turn the error-wealth brake on/off. |
| `fdr_wealth0` | `0.5` | Initial FDR wealth. |
| `fdr_alpha` | `0.05` | FDR investment scale. |
| `fdr_payout` | `0.05` | FDR reward per confirmation. |
| `fdr_alpha_min` | `0.005` | FDR cost floor. |

`promote_tau` (orchestrator.py:71) is **deprecated and unused** — a legacy hard confidence
floor kept only for CLI back-compat; promotion is now beam-search + Thompson sampling
(see [Promotion and verification](./promotion-and-verification.md)).
