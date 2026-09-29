# Promotion redesign: Components A-G (design)

This page renders the promotion/verification redesign (`DESIGN_promotion_v3.md`): the three
defects of the old hard-floor successive-halving promotion and the seven components (A-G) that
replace it, each with the implemented/deferred status recorded in the source design doc.

Related: [Promotion and verification](../architecture/promotion-and-verification.md) · [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) · [Claim lifecycle](../reference/claim-lifecycle.md) · [orchestrator.py](../modules/orchestrator.md) · [ledger.py](../modules/ledger.md) · [Coherence audit](../_coherence.md)

> **Design + status record, not a runtime spec.** This page preserves the *intended* design and
> the author's own status annotations. Some parts are shipped, some are deferred ("live tail")
> and run only on a paid run, and a few are described from principle and not yet built. Each
> component below states its status verbatim from the source. For the shipped, currently-running
> behavior of promotion and verification, follow the architecture links — this page is the
> rationale and the map of what is / is not built.

Related: [Promotion and verification](../architecture/promotion-and-verification.md) ·
[Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) ·
[Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md) ·
[Methodology v2 (design rationale)](./methodology.md) ·
[Formal algorithm spec](./algorithm-spec.md) ·
[orchestrator.py](../modules/orchestrator.md) · [ledger.py](../modules/ledger.md)

Source: `DESIGN_promotion_v3.md` (status: *proposed (design)*, 2026-07-08). It replaces the
promotion / verification core of `methodology_v2`, superseding `orchestrator._promote`,
`orchestrator.init`, `ledger.apply_verification`, `schemas.VERIFY`, and `schemas.PRIOR`.

---

## 1. Problem

The old design promoted claims to the (expensive) VERIFY stage using **Hyperband-style
successive halving plus a hard confidence floor**: a claim was eligible only if
`c.graduates() and c.confidence >= promote_tau (0.6)`, then the top `ceil(n/eta)` (`eta=3`) by
confidence were kept and everything else landed in an inert `unverified` backlog (114 of 158
claims in `v2_runs/genomic_pancreatic_200b`).

Three defects motivate the redesign:

| # | Defect | Why it hurts |
|---|--------|--------------|
| 1 | **Premature pruning of true-but-weak claims** | A hard floor on a *point estimate* deterministically excludes surprising / low-confidence-but-true claims. Documented failure mode of successive-halving/Hyperband: fixed-schedule pruning ignores each candidate's trajectory and kills slow-starters (the "n vs B/n" problem). A point-estimate objective can *actively* misdirect search (Lehman & Stanley, *Abandoning Objectives*). |
| 2 | **No resurfacing** | A low-confidence claim sits in the backlog forever; nothing re-scores it when later evidence corroborates it. The only feedback path was VERIFY *refuting* a claim and spawning a corrective direction (`ledger.apply_verification`). |
| 3 | **Confidence is an uncalibrated point estimate** | `Claim.confidence` is a single self-reported number from one EXPLORE call (`ledger.ingest`). LLM verbalized confidence is systematically overconfident; greedy point-estimate selection underperforms uncertainty-aware policies for LLM agents. |

## 2. Design overview — the seven components

Seven components, all mapping onto existing symbols:

| # | Component | Replaces / extends | Recorded status |
|---|-----------|--------------------|-----------------|
| A | Hybrid promotion: elitism + Thompson-sampled tail (later reframed as **beam search + Thompson**) | `_promote` | IMPLEMENTED |
| B | Calibrated uncertainty (k-sample posterior + LLM Bayesian update + isotonic recalibration) | `Claim.confidence`, `ingest`, `apply_verification` | CORE IMPLEMENTED, live tail deferred |
| C | Hierarchical Quality-Diversity archive (resurfacing) | the `unverified` backlog | IMPLEMENTED (driver implemented; k-sample posterior deferred) |
| D | Three-state verification (confirmed / error / refuted) + defect feedback | `apply_verification`, `schemas.VERIFY`, `executors.verify` | IMPLEMENTED (cross-regen bound deferred to F, done) |
| E | Online-FDR resurfacing budget (optional-stopping guard) | new | IMPLEMENTED (knobs uncalibrated) |
| F | Claim identity: lineage + embedding (same vs refined) | `embed.py`, `_source_index`, `Direction.parent_id` | IMPLEMENTED (embedding wiring deferred to B) |
| G | Init-phase prior verification (calibration bootstrap) | `orchestrator.init`, `schemas.PRIOR` | IMPLEMENTED (probe VERIFY calls exercised only live) |

The redesign also ships a related but separately-numbered piece, **§9b the LLM frontier
reranker**, covered at the end.

---

## 3. Component A — Hybrid promotion

**Status (source): IMPLEMENTED** (2026-07-08), in `orchestrator._promote`
(`orchestrator.py:504`) plus `_beta_params` (`orchestrator.py:423`). Since Component B's real
posteriors did not exist yet, the scalar `confidence` is turned into a
`Beta(conf·κ, (1−conf)·κ)` via the concentration `κ`, and the exploration slots draw from that
Beta (`random.betavariate`, seeded by `promote_seed + len(ledger.claims)` for reproducibility;
the seed is set at `orchestrator.py:525` and the draw is `orchestrator.py:527`).

**Config knobs (as shipped)** — the source lists an earlier knob set; the code retired several.
The *currently present* knobs:

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `eta` | `3.0` | `orchestrator.py:72` | beam width per wave: `keep = ceil(fresh_claims / eta)` |
| `promote_explore_frac` | `0.34` | `orchestrator.py:74` | fraction of each wave's beam budget reserved for Thompson exploration |
| `promote_kappa` | `8.0` | `orchestrator.py:75` | **fallback** Beta concentration when a claim has no LLM credible interval |
| `promote_seed` | `0` | `orchestrator.py:76` | base seed for reproducible Thompson draws |
| `promote_tau` | `0.6` | `orchestrator.py:71` | **DEPRECATED** legacy hard floor; unused, kept for CLI back-compat |

Knobs named in the source but **retired in code** (not present in `Config`): `promote_tau_high`,
`promote_z`, `promote_elite_pctl`; the helper `_conf_lower` and `_elite_cut` are likewise gone.
The original design pseudocode (below) framed A as "elitism + Thompson tail" with a `TAU_HIGH`
lower-bound gate; the **shipped** version reframes the deterministic half as beam search and
drops the threshold knob entirely.

**What "promote" means:** move a claim from the candidate pool into the VERIFY queue — spend an
(expensive) adversarial literature-check on it (→ confirmed / error / refuted). Un-promoted
claims are **not** discarded; they stay in the pool (Component C) and can be promoted in a later
wave. `keep = ceil(fresh/eta)` is the per-wave promotion *budget*; percentile+Thompson decide
*which* claims fill those slots, not how many.

**Shipped algorithm — beam search + Thompson sampling** (`orchestrator.py:504-537`). The
deterministic part *is* beam search: keep the top-scored claims (best-first over the belief
ledger). Each wave's budget is `keep = ceil(fresh/eta)` (the **beam width**,
`orchestrator.py:515`); of those, `n_beam = keep − n_ex` go to the beam (top claims by calibrated
confidence, niche-spread) and `n_ex = round(keep · promote_explore_frac)` are Thompson-sampled
from the remaining pool (`orchestrator.py:516-517`). No percentile/threshold knob — beam is
inherently relative (always the top-k), sidestepping the overconfident-tie problem that broke
the earlier value-threshold (`_elite_cut`, which logged `41 certain` on a 41-claim pool).

```
_promote(batch_claims):                              orchestrator.py:504
  pool  = _promotable_pool()          # whole pending set (fresh + backlog)
  keep  = ceil(len(batch) / eta)      # beam width = per-wave verify budget
  n_ex  = round(keep * promote_explore_frac)   # Thompson slots
  n_beam= keep - n_ex                            # beam (greedy) slots

  ranked   = sort(pool, key=_score, desc)        # _score = calibrated confidence
  promoted = _pick_spread(ranked, n_beam)        # BEAM: niche-spread top-k
  tail     = pool - promoted
  tail.sort(key=lambda c: rng.betavariate(*_beta_params(c)), desc)  # THOMPSON
  promoted += _pick_spread(tail, keep - len(promoted))

  for c in promoted: verify_queue.append(c); mark direction PROMOTED
```

`_beta_params` variance priority (`orchestrator.py:423-439`): (1) calibrated variance for the
claim's stated interval width, else (2) the raw LLM interval, else (3) fixed `promote_kappa`.
Mean = calibrated confidence; spread = verify-calibrated uncertainty — *"calibrate the belief,
don't just trust the LLM's stated uncertainty."*

**Calibrating the interval, not just the point (source, 2026-07-10).** EXPLORE and VERIFY emit,
per claim, a point belief `confidence` (posterior mean) and a ~90% credible interval
`[conf_low, conf_high]`. Both are calibrated against VERIFY's confirm/refute stream (Component B):

| Map | Direction | Role |
|-----|-----------|------|
| **Point map** (existing) | `raw confidence → P(true)` | corrects the level; used for FDR cost and the honesty of the reported belief |
| **Width map** (new) | `stated interval width → actual outcome variance` | drives Thompson exploration; if widths track real error, wide-stated claims get a wide posterior; if uninformative, the map flattens to the base-rate spread |

*Source verification note:* offline, informative widths gave variance 0.12→0.25 monotone;
uninformative widths gave a flat map.

Behaviour recorded in the source (200-trial sim, batch of 9, keep=3): total promoted stays = 3
(budget-neutral); the two certain claims promote 100%; weak claims (conf 0.15–0.35, pruned to 0%
by the old 0.6 floor) now promote 2–8% scaling with confidence; the 0.60 mid claim promotes 73%.

**Original design pseudocode (superseded framing, kept for rationale):**

```
def _promote(batch):
    ranked  = sort(batch, key=posterior_mean, desc)
    # ELITISM — only genuinely-certain claims skip the lottery.
    #   Bar is an uncertainty-aware LOWER bound, NOT the old 0.6 point estimate.
    certain = [c for c in ranked if c.conf_lower_bound >= TAU_HIGH]   # e.g. 0.8
    # EXPLORATION — Thompson-sample the remaining n - topk by full posterior.
    tail    = [c for c in ranked if c not in certain]
    sampled = thompson_sample(tail, k=EXPLORE_SLOTS)
    promote(certain + sampled)
```

The design intent (unchanged): no claim with nonzero posterior mass is ever *deterministically*
excluded (the surprising-discovery protection; TS beats UCB under delayed/batched feedback — our
regime), and a nonzero exploration reserve is kept even when many claims are certain (Hyperband's
no-early-stop hedge).

## 4. Component B — Calibrated uncertainty

**Status (source): CORE IMPLEMENTED** (2026-07-09), live tail deferred.

Done offline: `calibration.py` — a pure isotonic (Pool-Adjacent-Violators) `Calibrator`
(`calibration.py:53`) that learns `raw_confidence → P(true)` from VERIFY's own confirm/refute
labels, with `fit` (`calibration.py:68`), `apply` (`calibration.py:86`), `ece`
(`calibration.py:97`), and an identity no-op below `calibrate_min_labels`. Wired into the
orchestrator: `_drain_verify_pool` (`orchestrator.py:540`) logs a
`(promotion-time confidence → outcome)` label per terminal confirm/refute (ERROR is not a label)
and refits every `calibrate_refit_every` labels; promotion scores on `_score(c)`
(`orchestrator.py:416`) = calibrated confidence; the FDR cost/settle uses the promotion-time
confidence too.

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `calibrate_min_labels` | `12` | `orchestrator.py:104` | stay identity until this many confirm/refute labels accrue |
| `calibrate_refit_every` | `6` | `orchestrator.py:105` | refit the isotonic map every N new labels |

*Source verification note:* offline, isotonic cut ECE 0.163→~0.00 on synthetic overconfident
data, is monotone, stays identity below the label threshold, and leaves promotion/selftest
unchanged until fitted.

**Bootstrap timing (observed live, mini run 2026-07-10):** the calibrator fits from the init
prior-probe labels **plus** the first round's verify labels (a run fit at 7 labels = 3 probe +
4 round-1, refined to 23 by the end). Caveats recorded: the probe alone rarely reaches
`calibrate_min_labels` (set `prior_probe_k ≥ calibrate_min_labels` to fit from init alone); an
early fit on ~7 points is rough, so a reported `ECE 0.000` is in-sample/overfit, not out-of-sample.

**Status of the pieces the source filed under "live tail":**

1. **Not yet built:** replace the scalar with a true k-sample `(mean, var)` posterior so `kappa` is no longer a hack — needs repeated codex scoring at temperature > 0.
2. **Built and wired (2026-07-09); only its Azure embedder call is exercised live.** The embeddings-in-loop + posterior-bump-on-corroboration driver — the actual mechanism that resurfaces a weak-but-true backlog claim — is implemented as `_rescore_corroboration` (`orchestrator.py:477-502`), called every explore wave before promotion (`orchestrator.py:366`). It ranks backlog claims by cosine via `embedder.rank` (`orchestrator.py:494`) and applies the bump via `ledger.corroborate` (`orchestrator.py:497`). See §5's "DRIVER IMPLEMENTED." Note: the live loop does **not** go through `ledger.find_corroborators` (`ledger.py:289`, Component F's hook) — that helper is currently exercised only by `selftest`; the running driver is `_rescore_corroboration` + `corroborate` directly. What remains "live" is that the embedder call is real (Azure) and only hits the wire on a paid run.
3. Confirm the calibration map genuinely improves a real run (needs a paid run).

**Designed mechanism (posterior, not point estimate):** replace scalar `Claim.confidence` with
`(mean, var)` (or Beta `(alpha, beta)`). Base signal = one fixed scorer sampled k times (spread =
posterior); LLM Bayesian *update* on new evidence (relative odds-ratio judgments, not absolute
scalars); recalibration against our own verified outcomes with a **fixed estimator**
(`(scorer_model, prompt, k)` pinned; single model family; multi-family scores must not be
averaged into the calibrated scalar). Cold-start seed from prior runs' labels
(`genomic_pancreatic_200/200b`), shrinking toward that prior. Cross-family disagreement is a
*separate* uncertainty flag routing to more exploration, never folded into the calibrated scalar.
TS is the default acquisition; Predictive Entropy Search is noted as a heavier alternative;
Expected Improvement is explicitly *not* recommended (under-explores high-uncertainty regions).

## 5. Component C — Hierarchical Quality-Diversity archive (resurfacing)

**Status (source): IMPLEMENTED** (2026-07-09) in `_promotable_pool` (`orchestrator.py:469`),
`_niche` (`orchestrator.py:447`), `_pick_spread` (`orchestrator.py:451`), and the `_promote`
rewrite. Promotion fills its `keep = ceil(fresh_batch/eta)` slots from the **whole pending pool**
(every gated, still-unverified, not-currently-queued claim = this wave's fresh claims + the
carried-over backlog), not just the current wave. Niche descriptor = a claim's primary `aspect`;
beam and Thompson tail are both drawn niche-spread (round-robin per niche) so one crowded aspect
can't monopolise the budget. Per-round verify load stays tied to fresh throughput (budget-neutral).

*Source verification note (offline):* (A) an un-promoted weak claim persists instead of rotting;
(B) when new evidence bumps its confidence it resurfaces as a beam claim next wave; (C) a
*static* weak claim (conf 0.22) is promoted ~8% of trials vs exactly 0% under the old hard floor;
(D) a 30-claim wave spans all 5 niches; per-round total stays = keep.

**The C/B boundary (important):** C provides only the *mechanism* — the claim stays sampleable and
is never deterministically pruned. The *driver* that makes a weak-but-true claim actually
resurface is new evidence raising its posterior.

**DRIVER IMPLEMENTED** (2026-07-09): `ledger.corroborate(claim, corroborators)` (`ledger.py:304`)
raises a backlog claim's confidence when corroborators bring **independent** sources for the same
assertion (only sources the claim doesn't already cite count; a linear `+corroborate_per_source`
per independent source that saturates at the 0.95 cap; never lowers). `_rescore_corroboration(new_claims)` (`orchestrator.py:477`) runs each
explore wave before promotion: it finds backlog claims a fresh claim is a text near-duplicate of
(embedder rank, cosine ≥ `corroborate_thresh`) and corroborates them, so a weak-but-true claim
whose evidence just grew resurfaces into the sampler. This closes the C/B driver gap.

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `corroborate_enabled` | `True` | `orchestrator.py:107` | enable the corroboration driver |
| `corroborate_thresh` | `0.88` | `orchestrator.py:108` | text-embedding cosine to count a fresh claim as the same assertion |
| `corroborate_per_source` | `0.04` | `orchestrator.py:109` | linear confidence bump per independent corroborating source (saturates at the 0.95 cap) |
| `niche_boost` | `0.15` | `orchestrator.py:113` | promise boost for open directions whose parent is thin/contested |

**Two-level scoring — corrected (source, 2026-07-10):** the primary hierarchy is
**direction → its claims** (structural: `Claim.direction_id`, `Direction.produced_claims`), not
aspect. `ledger.direction_scores()` (`ledger.py:399`) scores each direction by its produced
claims (`strength = confirmed/(confirmed+refuted)`, `thin`, `contested`). `_select_batch`
(`orchestrator.py:380`) boosts an open direction's `promise` by `niche_boost` when its parent
direction is thin/contested (`orchestrator.py:395`) — follow up where the investigation was
inconclusive. The earlier cut mistakenly grouped by **aspect** via `niche_scores()`
(`ledger.py:376`); `niche_scores()` itself is now **dead** — it has no caller (only a passing
mention in the `direction_scores()` docstring at `ledger.py:403`). The aspect-diversity
tie-breaker role it once played is served independently by `_niche` (`orchestrator.py:447`) and
`_pick_spread` (`orchestrator.py:451`), which round-robin the verify slots across aspects — not
by `niche_scores()`.

**Still deferred:** the k-sample `(mean,var)` posterior (Component B.1) and re-sweeping the
archive at STALL/checkpoint on embedding match are noted as design intent; corroborator
*discovery* uses the Azure embedder and is exercised only on a real run.

## 6. Component D — Three-state verification

**Status (source): IMPLEMENTED** (2026-07-09). Ledger: `ERROR` state (`ledger.py:22`) plus
`Claim.defect` / `correction_attempts` fields (`ledger.py:74-75`, serialized);
`apply_verification` (`ledger.py:332`) routes on a three-state `verdict` via `_verdict()`
(`ledger.py:325`) — confirmed→lock, error→set ERROR + spawn a bounded "Correct and resubmit"
direction carrying the defect, refuted→"Re-investigate" direction — with a peeking guard
(default `correction_max_attempts=2`, `orchestrator.py:101`) that downgrades a claim to REFUTED
once its fix budget is spent (`ledger.py:356-373`). `schemas.VERIFY` gains `verdict` (enum) and
`defect` (`schemas.py:155-156`), keeping the legacy `confirmed` bool as a mirror
(`schemas.py:157`); `_verdict()` falls back to it for old payloads. `executors.verify`
(`executors.py:148`) prompt rewritten to search the literature to confirm/refute, using the
cited source only as an anchor, and to emit verdict + defect.

*Source verification note (offline):* error→ERROR+correction direction; two more errors exhaust
the budget→REFUTED; refuted→corrective direction; a legacy no-`verdict` payload still maps
confirmed→CONFIRMED.

**Core principle: VERIFY is literature-grounded, not source-bound.** It runs a web/literature
search to confirm *or* refute. Any cited `claim.evidence` is an **anchor** (a prior to check and
reconcile), not the sole target. This is a change from the old `executors.verify`, which fetched
only the single cited source (`claim.evidence[0]`) and never sought independent corroboration or
contradiction. Verifying against the field makes a genuine `refuted` verdict possible and lets
VERIFY confirm a true-but-mis-cited claim by finding the right source.

**Three states:**

| State | Meaning | Signal | Routing |
|-------|---------|--------|---------|
| **confirmed** | literature supports the claim (via the anchor and/or independently found sources) | `confirmed=true` | lock, graduate |
| **error** (correctable) | core assertion is supported, but the claim as written has a defect (wrong attribution / numbers / overstated scope / mis-cited anchor) | `confirmed=false` **and** `corrected_source`/`corrected_numbers` populated, core survives correction | targeted correction task carrying the defect → EXPLORE emits a *refined* claim (new node, Component F) |
| **refuted** (fundamental) | the search finds no support, or affirmatively contradicts the claim | `confirmed=false`, no salvageable core | stays down; skeptical prior; revive only on substantially new evidence under FDR budget (Component E) |

**Why VERIFY costs real money (source, 2026-07-10):** VERIFY is no longer a single-source fetch —
it runs a literature search (web_search + read several sources + reason), essentially a focused
re-investigation. Measured on the mini run: **$0.11/call vs $0.20 for an EXPLORE** — comparable,
not cheap. Aggregate verify spend is the bigger line item because there are more verify calls
(every promoted claim + every error→resubmit re-verification). Levers: anchor-only verify for
routine claims; lower `correction_max_attempts`; the Component E FDR budget already throttles the
tail. Search depth scales with stakes via `budget_hint` (`executors.py:148`), but it is always a
search, never a single-source fetch.

**Peeking guard (ties to E):** ≤2 correction attempts per claim; each must address the *named*
defect; a claim corrected twice and still failing → downgrade to refuted. Attempt budget draws
from the alpha-wealth in Component E.

## 7. Component E — Online-FDR resurfacing budget

**Status (source): IMPLEMENTED** (2026-07-09) as the `AlphaInvesting` class (`orchestrator.py:121`,
`cost` at `orchestrator.py:133`) plus a gate in `_drain_verify_pool` (`orchestrator.py:551`). Each
verify invests `cost(conf) = alpha_min + alpha·(1−conf)` (speculative low-confidence tests cost
more); a confirmation pays `payout` back, a refutation/error just spends. The drain gate is
cheapest-first (the queue is sorted by calibrated score desc, `orchestrator.py:543`): when the
cheapest test is unaffordable the round halts.

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `fdr_enabled` | `True` | `orchestrator.py:96` | enable the alpha-investing brake |
| `fdr_wealth0` | `0.5` | `orchestrator.py:97` | initial alpha-wealth (headroom for a healthy run) |
| `fdr_alpha` | `0.05` | `orchestrator.py:98` | investment scale: speculative tests cost more |
| `fdr_payout` | `0.05` | `orchestrator.py:99` | reward added back to wealth on each confirmation |
| `fdr_alpha_min` | `0.005` | `orchestrator.py:100` | floor so even a certain claim costs a little to test |

*Source verification note (offline):* a healthy 40%-confirm 44-test run keeps wealth positive and
skips 0 tests; an all-refute speculative stream brakes after 12 tests; at low wealth only
high-confidence tests are affordable.

**Tuning caveat (source):** the wealth0/payout balance was set from principle, **not calibrated on
a live run** — a real run may want them adjusted so the brake never fires on a healthy trajectory.
The mapping to formal alpha-investing is deliberately pragmatic (confidence-derived cost, not a
p-value).

Design rules: (1) re-test only on genuinely new evidence — never re-roll the same inputs;
(2) combine evidence across tests (posterior over everything seen) — never take the *max* verdict;
(3) bound total error with an online-FDR / alpha-investing budget. Not every resurfacing is
p-hacking: a fixable-framing `error` (Component D) is cheap and legitimate to re-verify after
correction; a fundamental `refuted` must clear a much higher, budgeted bar.

> **Decided (source, 2026-07-08):** use **alpha-investing** (Foster & Stine) as the default —
> simplest over a claim stream, adequate for now. LORD / SAFFRON can swap in later if FDR control
> proves loose, since they share the same alpha-wealth interface.

## 8. Component F — Claim identity (same vs refined)

**Status (source): IMPLEMENTED** (2026-07-09, lineage + matcher; embedding wiring deferred to B).
`Claim` gains `parent_claim_id` (`ledger.py:76`), `Direction` gains `corrects_claim_id`
(`ledger.py:97`), both serialized. Correction / re-investigation directions record which claim
they descend from; `ingest` (`ledger.py:227`) propagates `parent_claim_id` to regenerated claims
**and inherits the ancestor's `correction_attempts`** (`ledger.py:248-251`), so Component D's fix
budget now bounds the loop across EXPLORE-*regenerated* refinements (the gap D flagged).

Helpers:

| Helper | Location | Purpose |
|--------|----------|---------|
| `lineage(claim)` | `ledger.py:261` | ancestor chain via `parent_claim_id` (nearest first), to carry a refutation forward as skeptical context |
| `same_assertion(a, b, cosine, thresh=0.88)` | `ledger.py:277` | shared resolvable source OR near-duplicate text; ledger stays embedding-agnostic, caller supplies cosines |
| `find_corroborators(claim, cosines)` | `ledger.py:289` | designed as the hook for re-scoring a backlog claim's posterior on independent corroboration; **currently exercised only by `selftest`** — the live driver is `_rescore_corroboration` (`orchestrator.py:477`), which calls `embedder.rank` + `ledger.corroborate` directly, not this helper |

*Source verification note (offline):* lineage propagation; cross-regen budget inheritance →
REFUTED when exhausted; source/cosine matching; JSON round-trip of the new fields.

**Deferred to B:** actually computing the embeddings/cosines in the loop and applying the
posterior bump on corroboration.

Design intent: decide identity by **lineage + embedding**, not string match. Structural lineage is
reliable (a corrective direction's `parent_id` back to the claim's direction; its EXPLORE claims
are known descendants). Semantic identity clusters via `embed.py` (Azure text-embedding-3-large)
cosine + source overlap (`_source_index`). Treatment differs: same assertion + same evidence,
resurfaced → carry the refutation as a skeptical prior; a **refined** claim (narrower scope /
corrected attribution / new evidence) → new node linked to the ancestor, with the refutation
reason as *context*, not a probability penalty (a refinement must not inherit the veto).

## 9. Component G — Init-phase prior verification (calibration bootstrap)

**Status (source): IMPLEMENTED** (2026-07-09). Schema / seed scaffolding: `schemas.PRIOR`
`candidate_answers` are now `{answer, confidence, aspect}` objects (`schemas.py:89`);
`executors.prior` (`executors.py:49`) asks for a calibrated per-candidate confidence;
`ledger.seed` (`ledger.py:155`) accepts both the object form and legacy strings, stores the
structured list on `ledger.prior_candidates` (serialized), and prioritises each seeded "Confirm
or refute candidate answer" direction by its prior confidence (`promise = 0.5 + 0.4·conf`).

Probe wired: `orchestrator._prior_probe()` (`orchestrator.py:268`) runs at the end of `init()`
(`orchestrator.py:232`) — it VERIFYs the top `prior_probe_k` candidates
(`orchestrator.py:276`; VERIFY finds its own sources, Component D; no mandatory GROUND), and
`_probe_apply` (`orchestrator.py:298`) seeds the Component B calibrator with the real
`(prior confidence → outcome)` label, adds a confirmed prior as an early grounded claim, and lets
refuted priors spawn their re-investigation direction.

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `prior_probe_enabled` | `True` | `orchestrator.py:111` | run the init prior probe |
| `prior_probe_k` | `5` | `orchestrator.py:112` | how many top-confidence candidate answers to probe |

*Source verification note (offline):* seed prioritisation + JSON round-trip; `_probe_apply`
label-logging / claim-promotion on synthetic verdicts.

**Live tail:** the probe's VERIFY calls run only on a real `init()` (each ~`verify_task_usd`), so
the end-to-end calibration bootstrap is exercised on a live run.

Design intent: after `init()` we already hold `candidate_answers` (the model's self-assessed best
guesses). Verify them *first*, before the main loop, to (1) seed the calibration map warm,
(2) confirm cheap well-known priors early to anchor the report, and (3) catch confidently-wrong
priors before they steer the search. Because VERIFY now does its own literature search, a candidate
with no `evidence` can be verified straight away; GROUND is optional. Confirmed priors become early
grounded claims; `error` priors get corrected; `refuted` priors are downweighted as directions.
These early verifications are part of the same online-FDR stream (Component E), not a free pass.

## 9b. LLM frontier reranker

**Status (source): IMPLEMENTED + live-validated** (2026-07-09). Raw embedding cosine is a weak
*ranking* signal for the frontier; for a not-huge candidate set an LLM judge ranks far better.
`executors.rerank` (`executors.py:64`) scores each candidate direction's value-to-pursue in [0,1]
(reason mode, no tools); `_select_batch` (`orchestrator.py:380`) LLM-ranks the whole frontier
directly when it is small (`≤ rerank_direct_max`, default 60, `orchestrator.py:116`), else uses
embedding promise to shortlist a top-N (`rerank_pool`, default 50, `orchestrator.py:117`) and
reranks just those — the "embed → top-N → LLM rerank" pattern.

| Knob | Default | Location | Meaning |
|------|---------|----------|---------|
| `rerank_frontier` | `True` | `orchestrator.py:115` | LLM-rerank the frontier before selecting the batch |
| `rerank_direct_max` | `60` | `orchestrator.py:116` | if ≤ this many open directions, LLM-rank them all directly |
| `rerank_pool` | `50` | `orchestrator.py:117` | else embedding pre-filters to this top-N, then LLM-reranks those |

*Source live-smoke note:* relevant/specific directions scored 0.89–0.97, an off-topic vague one
0.0, ~$0.12/call. The same embed-shortlist-then-LLM-judge pattern is noted as a follow-on for
corroboration matching (F) and context selection.

---

## 10. Code touch-points (design map)

The source lists the intended edit surface. As shipped, the mapping is:

| Design touch-point | Shipped location |
|--------------------|------------------|
| `orchestrator._promote` → Component A (beam + Thompson) | `orchestrator.py:504` |
| `Claim` posterior + `verdict`/`defect`/lineage fields | `ledger.py:62-97` |
| `ingest` / `apply_verification` → calibration + three-state routing | `ledger.py:227`, `ledger.py:332` |
| `schemas.VERIFY` verdict/defect; `schemas.PRIOR` structured candidates | `schemas.py:148`, `schemas.py:81` |
| `executors.verify` literature-search; `executors.prior`, `executors.rerank` | `executors.py:148`, `:49`, `:64` |
| QD archive (C), calibration module (B), online-FDR (E), identity (F) | `orchestrator.py:447-540`, `calibration.py`, `orchestrator.py:121`, `ledger.py:261-304` |

**Note on `Claim.confidence`:** the source calls for replacing the scalar with a true `(mean, var)`
posterior. As shipped this is **not** done — the scalar is still turned into a Beta via
`promote_kappa` (Component A), and the true k-sample posterior is the deferred "live tail" of
Component B. The `(mean, var)` replacement is intended design, not running behavior.

## 11. Validation plan (from the source)

1. **Offline replay** of the new `_promote` + QD archive against the `v2_runs/genomic_pancreatic_200b` ledger — how many of the 114 backlog claims would resurface, and are any true-but-weak that the old floor killed.
2. **Calibration curve:** raw scorer value vs verified P(true) on `200/200b` labels; fit + report ECE before/after isotonic.
3. **Three-state audit:** re-classify the 27 run refutations into error vs refuted (expectation: most are *error*).
4. **Live $50 run** on `genomic_pancreatic` with the new core; compare confirmed-claim yield, FDR proxy, and cost vs the v2 baseline.

## 12. References and coverage caveat

The source cites Russo & Van Roy (posterior sampling); Chapelle & Li (Thompson sampling, NIPS
2011); Felicioni et al. (uncertainty in LLM decision-making, TMLR 2024); Hernández-Lobato et al.
(Predictive Entropy Search); Li et al. (Hyperband; ASHA); Wistuba & Pedapati (LCRankNet);
Pugh, Soros & Stanley (Quality Diversity); Lehman & Stanley (Abandoning Objectives); Xiong et al.
(LLM uncertainty calibration); Ramdas et al. (SAFFRON, online FDR).

> **Coverage note (verbatim from source):** the online-FDR angle (Component E) and LLM-confidence
> calibration specifics (Component B) were **not** covered by the deep-research verified findings —
> treat those two components as designed-from-principles pending a focused follow-up search.
