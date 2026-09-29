# Calibration and uncertainty

How the agent represents belief confidence, and how it corrects that confidence
against its own verification outcomes. This is Component B of the promotion
redesign: an isotonic recalibrator that turns the LLM's self-reported numbers
into verification-grounded means and variances, which then feed promotion.

Related: [Promotion and verification](./promotion-and-verification.md) · [The belief ledger](./belief-ledger.md) · [Budget, cost, and the FDR brake](./budget-cost-fdr.md) · [calibration.py](../modules/calibration.md) · [Config knobs (reference)](../reference/config-reference.md) · [Promotion redesign: Components A-G](../design/promotion-redesign.md)

## What confidence looks like on a claim

Every claim carries three self-reported numbers, not one. EXPLORE emits a point
belief plus a `~90%` credible interval; VERIFY refreshes them after a
literature check.

| Field | Meaning | Range / sentinel | Source |
|-------|---------|------------------|--------|
| `confidence` | posterior mean, the LLM's point `P(true)` | `[0,1]` | `ledger.py:70` |
| `conf_lo` | lower end of the stated `~90%` interval | `[0,1]`, `-1.0` = absent | `ledger.py:71` |
| `conf_hi` | upper end of the stated interval | `[0,1]`, `-1.0` = absent | `ledger.py:72` |

The interval is the model's *stated uncertainty*: few or weak sources should
give a wide `[conf_lo, conf_hi]`, many strong sources a narrow one. Both the
EXPLORE and VERIFY output schemas require `conf_low`/`conf_high`
(`schemas.py:60-63`, `schemas.py:164-168`); `ledger.ingest` copies them onto the
claim (`ledger.py:240-241`) and `apply_verification` overwrites all three with
VERIFY's post-check numbers (`ledger.py:336-338`).

Raw verbalized confidence is systematically overconfident, so these numbers are
not trusted as-is. Calibration corrects them.

## The two maps

The `Calibrator` (`calibration.py:52-58`) holds **two** independent isotonic
step functions, both fit by Pool-Adjacent-Violators (`_pav`,
`calibration.py:24-35`) with no numpy/sklearn dependency:

| Map | Learns | Corrects | Fitted flag | Applied by |
|-----|--------|----------|-------------|-----------|
| POINT (`steps`) | `raw confidence -> P(true)` | the *level* of the belief | `fitted` (`calibration.py:60-62`) | `apply` (`calibration.py:86-89`) |
| WIDTH (`width_steps`) | `stated interval width -> outcome variance` | the *spread* driving Thompson | `width_fitted` (`calibration.py:64-66`) | `variance` (`calibration.py:91-95`) |

The width target is a variance *proxy*: the squared error of the already
point-calibrated belief, `(apply(r) - y)^2`, regressed on the stated width
`hi - lo` (`calibration.py:81`). PAV forces both maps to be non-decreasing —
higher raw confidence maps to higher `P(true)`; wider stated interval maps to
more outcome variance.

Why two maps and why width matters more here: promotion's beam ranks claims by
*order*, and a monotone point map barely disturbs a rank order — so the point
map's leverage is mostly on the FDR cost and on honest reporting, not on which
claims get picked. The width map is what feeds Thompson exploration: if the
LLM's stated widths track real error, wide-stated claims get genuinely wide
posteriors and can out-draw narrow ones; if the widths are uninformative, PAV
flattens the map and everyone collapses to the base-rate spread. See
`calibration.py:1-18` for this rationale in the module docstring.

`variance()` clamps its output to `[1e-4, 0.2499]` (`calibration.py:95`) so a
degenerate fit can never produce a zero or out-of-range Beta.

## Where labels come from

A label is a `(raw_confidence, stated_width, outcome)` triple. Outcomes come
only from VERIFY's terminal confirm/refute stream — the same three-state
verdict machinery described in
[Promotion and verification](./promotion-and-verification.md).

```
 EXPLORE ── confidence, conf_lo, conf_hi ──► claim in ledger
                                               │
                                     promotion picks it
                                               │
                                               ▼
 VERIFY ──► verdict ∈ {confirmed, error, refuted}
                 │            │           │
            outcome=1     NO LABEL     outcome=0
                 │       (transient)      │
                 └──────────┬─────────────┘
                            ▼
        calib_pairs.append((raw_conf, raw_width, outcome))
```

Two things to note:

- **ERROR is not a label.** Only `CONFIRMED` and `REFUTED` append to
  `calib_pairs` (`orchestrator.py:584-585`); an ERROR claim is mid-correction
  and is expected to come back around.
- **The label is captured pre-overwrite.** `apply_verification` mutates
  `claim.confidence` in place, so the drain loop snapshots `raw_conf` and
  `raw_w` *before* calling it (`orchestrator.py:575-579`). The label records
  what the model believed at promotion time, matched to what verification
  found.

Labels accrue in two places, both into the single `calib_pairs` list
(`orchestrator.py:162`):

1. **INIT prior probe (Component G).** `_probe_apply` verifies the top prior
   candidate answers and logs `(prior self-confidence -> outcome)` labels
   (`orchestrator.py:298-305`), giving the map a warm start before the main
   loop. See [Promotion and verification](./promotion-and-verification.md) for
   the probe.
2. **The main VERIFY drain.** Every terminal confirm/refute in
   `_drain_verify_pool` appends a label (`orchestrator.py:582-585`).

## Refit cadence

The map is refit lazily, not on every label.

| Knob | Default | Meaning | Defined |
|------|---------|---------|---------|
| `calibrate_enabled` | `True` | master switch for Component B | `orchestrator.py:103` |
| `calibrate_min_labels` | `12` | identity no-op below this many labels | `orchestrator.py:104` |
| `calibrate_refit_every` | `6` | refit only after this many new labels | `orchestrator.py:105` |
| `promote_kappa` | `8.0` | fallback Beta concentration, no interval | `orchestrator.py:75` |

After each drain wave, the orchestrator refits only if enabled, at least
`calibrate_min_labels` are held, and at least `calibrate_refit_every` new labels
have arrived since the last successful fit (`orchestrator.py:589-596`). The
`_calib_last_fit` watermark advances *only when a fit actually lands*
(`orchestrator.py:593-594`), so a below-threshold no-op does not silently
consume the refit window. The prior probe does its own one-shot fit at the end
of INIT if enough labels accrued (`orchestrator.py:293-296`).

`fit()` itself re-derives both maps from scratch on the full label set each time
(`calibration.py:68-84`); there is no incremental update. It also guards the
width map separately: it is only fit if at least `min_labels` claims carried a
real interval (`0.0 <= w <= 1.0`), otherwise `width_steps` stays empty
(`calibration.py:83`).

## How the calibrated numbers feed promotion

Two functions consume the calibrator, both in the promotion path:

**`_score(c)`** (`orchestrator.py:416-421`) returns the calibrated mean. If the
point map is fitted it returns `calibrator.apply(c.confidence)`, else the raw
`c.confidence`. This score drives the beam ranking (`orchestrator.py:519`), the
verify-queue ordering (`orchestrator.py:543`), and the FDR cost/settle
(`orchestrator.py:577,581`).

**`_beta_params(c)`** (`orchestrator.py:423-443`) builds the `(alpha, beta)` for
each Thompson draw (`orchestrator.py:527`). The mean is `_score(c)`; the
variance is chosen by a three-tier priority:

```
mu = clamp(_score(c))                         # calibrated mean
var_max = mu*(1-mu)                            # max Beta variance at this mean

if width_fitted and has_interval:
    var = calibrator.variance(hi - lo)        # (1) VERIFY-calibrated variance
elif has_interval:
    var = ((hi - lo) / (2*1.645))**2          # (2) raw LLM interval, moment-matched
else:
    return mu*kappa, (1-mu)*kappa             # (3) fixed promote_kappa fallback

kappa_c = clamp(var_max/var - 1, 1, 200)      # Var = mu(1-mu)/(kappa+1), solved
return mu*kappa_c, (1-mu)*kappa_c
```

Tier (1) is the only path that uses verification-grounded uncertainty; (2)
trusts the LLM's stated interval directly (treating `hi - lo` as a `~90%`,
hence `2 x 1.645` sigma) width; (3) is the un-calibrated, no-interval floor.
The variance is capped at `0.999 * var_max` before solving so the Beta stays
proper (`orchestrator.py:441`).

## Honest status: what is and is not built

- **Calibration is an identity no-op until `calibrate_min_labels` (12).**
  Below the threshold `fit()` clears both maps (`calibration.py:73-76`),
  `apply()` returns its input unchanged (`calibration.py:88-89`), `variance()`
  returns `None`, and `_score`/`_beta_params` fall back to raw confidence and
  `promote_kappa`. On a small run the point map may not fit at all. Because
  `prior_probe_k` defaults to `5` (`orchestrator.py:112`), the INIT probe alone
  usually cannot reach 12 labels — the first real fit typically waits for the
  first VERIFY waves.

- **The true k-sample posterior is unbuilt; `kappa` is a fallback.** The design
  (`DESIGN_promotion_v3.md:141-162`, Component B.1) calls for replacing the
  scalar `confidence` with a real `(mean, var)` posterior obtained by sampling
  one fixed scorer `k` times. That does not exist. The code uses the single
  scalar plus the LLM's one stated interval, and where there is no interval it
  falls back to the fixed `promote_kappa` concentration. The width map is a
  regression proxy for outcome variance, not a sampled posterior.

- **The width map is a proxy, and early ECE is optimistic.** `ece()`
  (`calibration.py:97-111`) is computed in-sample on the same labels the map was
  fit on, so an early `ECE ~0.00` logged at `orchestrator.py:595-596` is
  overfit, not an out-of-sample number.

- **Several Component B designs are not wired.** The LLM Bayesian relative-odds
  update for resurfacing (`DESIGN_promotion_v3.md:148-151`), cross-family
  disagreement as a separate uncertainty flag (`DESIGN_promotion_v3.md:163-164`),
  and cross-run cold-start seeding of the map (`DESIGN_promotion_v3.md:158-159`)
  are described in the design but have no implementation in `calibration.py` or
  `orchestrator.py`. What runs today is: two isotonic maps, fit from the local
  run's confirm/refute labels, feeding `_score` and `_beta_params`.
