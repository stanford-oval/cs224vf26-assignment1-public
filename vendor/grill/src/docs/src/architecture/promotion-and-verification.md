# Promotion and verification

How a claim travels from an EXPLORE hit to an adjudicated verdict: the resurfacing pool it lives in, the beam-search-plus-Thompson lottery that decides which claims spend a VERIFY call, the three-state verdict that VERIFY returns, and the corroboration re-scoring that lets a weak-but-true claim climb back into contention on later evidence.

Related: [The belief ledger](./belief-ledger.md) · [The orchestration loop](./orchestration-loop.md) · [Calibration and uncertainty](./calibration-and-uncertainty.md) · [Budget, cost, and the FDR brake](./budget-cost-fdr.md) · [Claim lifecycle (reference)](../reference/claim-lifecycle.md) · [Promotion redesign: Components A-G](../design/promotion-redesign.md)

---

## What "promotion" means

Promotion is the decision to spend an expensive adversarial VERIFY call on a claim. Un-promoted claims are **not** discarded — they stay in a resurfacing pool and can be promoted in a later wave. Each EXPLORE wave gets a fixed promotion *budget* (`keep = ceil(fresh_claims / eta)`); the machinery below decides *which* claims fill those `keep` slots, never *how many*. Per-round verify load therefore stays tied to fresh EXPLORE throughput (budget-neutral).

This page covers three of the seven components of the promotion redesign:

| Component | This page | Code |
|-----------|-----------|------|
| **A** — Hybrid promotion (beam search + Thompson-sampled tail) | [Beam + Thompson](#the-promotion-lottery-beam--thompson-component-a) | `orchestrator._promote`, `_beta_params` |
| **C** — Quality-Diversity archive (resurfacing) | [The resurfacing pool](#the-resurfacing-pool-component-c) | `orchestrator._promotable_pool`, `_pick_spread`, `_niche` |
| **D** — Three-state verification | [The VERIFY drain](#the-verify-drain-and-the-three-state-verdict-component-d) | `ledger.apply_verification` |

Components B (calibration), E (the FDR brake), F (claim lineage) and G (init prior probe) are adjacent and referenced here but documented in [Calibration and uncertainty](./calibration-and-uncertainty.md) and [Budget, cost, and the FDR brake](./budget-cost-fdr.md). The authoritative design record is [`DESIGN_promotion_v3.md`](../design/promotion-redesign.md).

## The path a claim takes

```
 EXPLORE wave produces claims
        │  ledger.ingest  (claim.confidence, [conf_lo, conf_hi], provenance)
        ▼
 ┌──────────────────────────────────────────────┐
 │  _rescore_corroboration(batch_claims)         │  Component B/C DRIVER
 │  fresh claim ≈ backlog claim (cosine≥0.88)    │  raises a backlog claim's
 │  + independent source → ledger.corroborate    │  confidence so it resurfaces
 └──────────────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │  _promote(batch_claims)          Component A+C │
 │  pool = _promotable_pool()  (fresh + backlog)  │
 │  keep = ceil(fresh / eta)      (beam width)    │
 │   ├─ BEAM   : top-scored, niche-spread         │
 │   └─ TAIL   : Thompson-sampled, niche-spread   │
 │  → append chosen claims to verify_queue        │
 └──────────────────────────────────────────────┘
        │
        ▼
 ┌──────────────────────────────────────────────┐
 │  _drain_verify_pool()          Component D+E   │
 │  FDR gate (alpha-investing) → executors.verify │
 │  → ledger.apply_verification (3-state verdict) │
 │     confirmed → lock                           │
 │     error     → "Correct and resubmit" dir ────┼──┐  new directions
 │     refuted   → "Re-investigate" dir ──────────┼──┤  re-enter the frontier
 └──────────────────────────────────────────────┘  │
        ▲                                           │
        └───────────────────────────────────────────┘
```

The loop body that wires this together is `orchestrator.run` at `orchestrator.py:355`-`371`: ingest, `_rescore_corroboration`, `_promote`, then `_drain_verify_pool`.

## The resurfacing pool (Component C)

The pool replaces the old inert `unverified` backlog. `_promotable_pool` (`orchestrator.py:469`) returns **every gated, still-unverified claim that is not already queued for verification** — this wave's fresh claims *plus* the carried-over backlog:

```python
return [c for c in self.ledger.claims.values()
        if c.verification == UNVERIFIED and id(c) not in queued and c.graduates()]
```

`graduates()` (`ledger.py:81`) is the provenance gate: a claim needs at least one resolvable source (DOI / PMID / PMC / URL) to be promotable at all. A weak claim that lost an earlier wave stays sampleable indefinitely — it is never deterministically pruned.

**Niche-spread diversity (MAP-Elites style).** Both the beam and the sampled tail are drawn with `_pick_spread` (`orchestrator.py:451`), which round-robins one claim per niche in priority order so a single crowded aspect cannot monopolise the `keep` slots. A claim's niche is its **primary aspect** — `_niche` (`orchestrator.py:446`) returns `c.aspects[0]` lowercased, or `"(none)"`. This is the QD behaviour space: a surprising claim in a thin aspect is not crowded out by twenty claims in a popular one.

> **Honest scope note.** The design document (Component C) also describes a per-aspect belief score, `ledger.niche_scores()` (`ledger.py:376`), demoted to a "promotion-diversity tie-breaker." In the shipped code `niche_scores()` is **never called** — `_pick_spread` groups by primary aspect directly via `_niche`, not by `niche_scores()`. The related two-level score `direction_scores()` (`ledger.py:399`) *is* live, but it drives **frontier selection** (a `niche_boost` on directions whose parent came back thin/contested, `orchestrator.py:390`-`395`), not promotion. See [Frontier selection](./frontier-selection.md).

## The promotion lottery: beam + Thompson (Component A)

`_promote` (`orchestrator.py:504`) fills the `keep` verify slots from the whole pool:

```
keep   = ceil(len(batch_claims) / eta)          # beam width  (per-wave verify budget)
n_ex   = round(keep * promote_explore_frac)     # Thompson (exploration) slots, ≥ 1
n_beam = keep - n_ex                             # beam (greedy top-k) slots, ≥ 0
```

**Beam (exploit).** `ranked = sorted(pool, key=_score, desc)` then `_pick_spread(ranked, n_beam)`. This is deterministic best-first over the belief ledger — literally beam search. There is no confidence floor and no percentile threshold: the beam is inherently relative (always the top-k), which sidesteps the overconfident-tie problem that broke the earlier value-threshold design.

**Tail (explore).** The remaining `keep - n_beam` slots are Thompson-sampled from the non-beam claims (`orchestrator.py:524`-`528`): draw one value per claim from its Beta posterior and take the highest draws, again niche-spread. A claim with mean 0.5 and a wide posterior can out-draw a claim with mean 0.55 and a tight one — the surprising-discovery protection. Draws are seeded (`random.Random(promote_seed + len(ledger.claims))`) for reproducibility.

**The Thompson posterior — `_beta_params`** (`orchestrator.py:423`). Mean is the calibrated confidence `_score(c)`; the variance is chosen by priority:

| Priority | Source of variance | Condition |
|----------|--------------------|-----------|
| 1 | Verify-**calibrated** variance for the claim's stated interval width | calibrator's width map is fitted and the claim carries a valid `[conf_lo, conf_hi]` |
| 2 | The LLM's raw ~90% credible interval, moment-matched `((hi−lo)/(2·1.645))²` | a valid interval exists but no width calibration yet |
| 3 | Fixed concentration `promote_kappa` (default 8.0) | no interval at all |

The variance is clamped below `mu·(1−mu)` and converted to Beta `(mu·κ, (1−mu)·κ)` with `κ` in `[1, 200]`. The guiding principle: *calibrate the belief, don't just trust the LLM's stated uncertainty.*

**`_score`** (`orchestrator.py:416`) is the single scoring hook shared by the beam, the FDR gate and the verify-queue sort: it returns the isotonic-calibrated confidence once the calibrator is fitted (`≥ calibrate_min_labels` labels), and the raw `c.confidence` otherwise. Calibration itself is [Component B](./calibration-and-uncertainty.md).

### Promotion knobs

| Config field | Default | Meaning |
|--------------|---------|---------|
| `eta` | 3.0 | beam width divisor: `keep = ceil(fresh / eta)` |
| `promote_explore_frac` | 0.34 | fraction of `keep` reserved for the Thompson tail |
| `promote_kappa` | 8.0 | fallback Beta concentration when a claim has no credible interval |
| `promote_seed` | 0 | base seed for reproducible Thompson draws |
| `promote_tau` | 0.6 | **DEPRECATED / unused** — the legacy hard confidence floor, kept only for CLI back-compat (`orchestrator.py:71`) |

Retired entirely (present in older design text, absent from code): `promote_tau_high`, `promote_z`, `promote_elite_pctl`, `_elite_cut`, `_conf_lower`.

## The corroboration driver (Component B/C)

Component C only guarantees a weak claim *stays* sampleable. The thing that actually *raises* a weak-but-true claim's confidence so it resurfaces is corroboration re-scoring, run once per wave **before** `_promote`.

`_rescore_corroboration` (`orchestrator.py:477`) takes the fresh batch, and for each fresh claim uses the embedder to find backlog claims it is a near-duplicate of (`embedder.rank`, cosine `≥ corroborate_thresh` = 0.88). For each match it calls `ledger.corroborate` (`ledger.py:304`), which bumps the backlog claim's confidence only when the corroborator brings a **source the claim does not already cite**:

- `+corroborate_per_source` (0.04) per independent source, diminishing;
- capped at 0.95;
- same-source corroboration contributes 0; the bump **never lowers** confidence.

So a backlog claim whose independent evidence just grew gets a higher posterior mean and re-enters the beam/tail next wave. This closes the "driver" gap that Component C alone leaves open.

> **Honest scope note.** The ledger also exposes `find_corroborators` / `same_assertion` / `lineage` (`ledger.py:289`, `277`, `261`) as the intended matching hooks. On the live path `_rescore_corroboration` calls `ledger.corroborate` directly via `embedder.rank`; `find_corroborators` and `lineage` are exercised only in `selftest.py`, not by the orchestration loop. The `(mean, var)` k-sample posterior described in Component B.1 is also not built — the scalar `confidence` plus the LLM-stated interval is what actually flows through `_beta_params`.

| Config field | Default | Meaning |
|--------------|---------|---------|
| `corroborate_enabled` | True | run the re-scoring pass each wave |
| `corroborate_thresh` | 0.88 | cosine to count a fresh claim as the same assertion |
| `corroborate_per_source` | 0.04 | confidence bump per independent corroborating source |

## The VERIFY drain and the three-state verdict (Component D)

`_drain_verify_pool` (`orchestrator.py:540`) sorts the queue by calibrated `_score` (highest confidence = cheapest FDR test first), then drains in affordable waves. Each claim runs through `executors.verify`, which performs a **literature search** (not a single-source fetch) to confirm or refute the claim, using any cited source only as an anchor. VERIFY is therefore a real cost line, comparable to EXPLORE per call.

Two gates govern the drain:

1. **Budget floor** — stop when `verify_remaining()` drops below `verify_task_usd * 0.5`.
2. **FDR brake** (Component E) — before each test check `self.fdr.can_afford(_score(cheapest))`. Because the queue is confidence-sorted, if even the cheapest test is unaffordable the alpha-wealth is spent and the round halts (`orchestrator.py:551`, `564`). See [Budget, cost, and the FDR brake](./budget-cost-fdr.md).

Each returned result is routed by `ledger.apply_verification` (`ledger.py:332`). The verdict is three-state via `_verdict` (`ledger.py:324`), which reads a `verdict` enum and falls back to the legacy boolean `confirmed` for old payloads. The claim states are defined at `ledger.py:21`-`22` (`UNVERIFIED, CONFIRMED, REFUTED, ERROR`).

| Verdict | Meaning | Ledger effect | Routing |
|---------|---------|---------------|---------|
| **confirmed** | literature supports the claim (via anchor and/or independently found sources) | `verification = CONFIRMED`; locked; enters the report body | none — terminal |
| **error** | core assertion holds but the claim as written has a fixable defect (wrong numbers / attribution / over-scoped / mis-cited anchor) | `verification = ERROR`; `defect` set; `correction_attempts += 1` | spawns a bounded **"Correct and resubmit"** direction (promise 0.70) carrying the defect, `corrects_claim_id` = this claim |
| **refuted** | literature gives no support or contradicts the claim | `verification = REFUTED` | spawns a **"Re-investigate (refuted)"** direction (promise 0.65) |

**Correction, re-investigation, and the peeking guard.** The `error → correct → re-verify` loop is itself an optional-stopping risk, so it is bounded by `correction_max_attempts` (default 2, `orchestrator.py:101`). `apply_verification` increments `correction_attempts`; once the budget is spent the claim is **downgraded to REFUTED** instead of spawning another correction (`ledger.py:360`-`369`). The corrective/re-investigation directions re-enter the frontier and, when EXPLORE regenerates a refined claim from one, `ledger.ingest` propagates `parent_claim_id` and **inherits the ancestor's `correction_attempts`** (`ledger.py:247`-`251`) so the fix budget also bounds regenerated refinements, not just re-verifications of the same claim id (Component F).

**Verdict-time side effects on the claim.** Before routing, `apply_verification` overwrites `confidence` (and `conf_lo/conf_hi` if VERIFY re-stated them), folds in any `corrected_numbers`, and swaps in a `corrected_source` when VERIFY found the right citation (`ledger.py:336`-`349`). The pre-overwrite raw confidence is captured by the caller first (`orchestrator.py:575`) because it is the calibration *label*.

**Calibration and FDR settlement** happen back in `_drain_verify_pool` after each verdict (`orchestrator.py:580`-`585`): a `confirmed`/`refuted` outcome logs a `(raw_confidence, stated_width → outcome)` label for the isotonic calibrator, and `fdr.settle(promo_score, confirmed)` debits the alpha-wealth (a confirmation pays `fdr_payout` back). **ERROR is transient** — it produces no calibration label and remains in flight through its correction. The calibrator refits every `calibrate_refit_every` (6) new labels once past `calibrate_min_labels` (12).

### VERIFY / verdict knobs

| Config field | Default | Meaning |
|--------------|---------|---------|
| `verify_task_usd` | 1.5 | target spend per VERIFY call |
| `correction_max_attempts` | 2 | max `error → correct` attempts before a claim is downgraded to REFUTED |
| `fdr_enabled` | True | apply the alpha-investing brake to the drain |
| `fdr_wealth0` / `fdr_alpha` / `fdr_payout` / `fdr_alpha_min` | 0.5 / 0.05 / 0.05 / 0.005 | alpha-investing pool: cost `= alpha_min + alpha·(1−conf)`, confirmation refunds `payout` (`orchestrator.py:120`-`146`) |
| `calibrate_min_labels` / `calibrate_refit_every` | 12 / 6 | when the isotonic calibrator starts and how often it refits |

## Where the confirmed claims go

Confirmed, source-verified claims are the headline answer: `ledger.synthesize` (`ledger.py:484`) renders them clustered by aspect with a deduped reference list. Graduated-but-unverified claims that survived to the end of the budget are reported in a separate, explicitly-labelled "pending verification" section (`ledger.unverified_graduated`, `ledger.py:472`) so nothing unverified is passed off as confirmed. See [Claim lifecycle (reference)](../reference/claim-lifecycle.md) for the full state table.
