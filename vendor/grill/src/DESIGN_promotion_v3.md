# Design: Uncertainty-aware promotion, calibration, and a resurfacing hypothesis pool

**Status:** proposed (design), 2026-07-08
**Scope:** replaces the promotion / verification core of `methodology_v2`
**Supersedes behaviour in:** `orchestrator._promote`, `orchestrator.init`, `ledger.apply_verification`, `schemas.VERIFY`, `schemas.PRIOR`

---

## 1. Problem

Today promotion to the (expensive) VERIFY stage uses **Hyperband-style successive halving + a hard
confidence floor**: in `orchestrator._promote`, a claim is eligible only if
`c.graduates() and c.confidence >= promote_tau (0.6)`, then we keep the top `ceil(n/eta)` (`eta=3`) by
confidence. Everything else lands in an inert `unverified` backlog (114 of 158 claims in
`v2_runs/genomic_pancreatic_200b`).

Three defects:

1. **Premature pruning of true-but-weak claims.** A hard floor on a *point estimate* deterministically
   excludes surprising/low-confidence-but-true claims. This is a documented failure mode of
   successive-halving/Hyperband — fixed-schedule pruning ignores each candidate's trajectory and kills
   slow-starters (the "n vs B/n" problem; Wistuba & Pedapati, ICML 2020; Hyperband, JMLR 16-558; ASHA,
   arXiv:1810.05934). The theoretical case against a point-estimate objective is deceptiveness: it can
   *actively* misdirect search away from the true answer (Lehman & Stanley, *Abandoning Objectives*,
   Evol. Comp. 2011).
2. **No resurfacing.** A merely low-confidence claim sits in the backlog forever; nothing re-scores it
   when later evidence corroborates it. The only feedback path today is VERIFY *refuting* a claim and
   spawning a corrective direction (`ledger.apply_verification`).
3. **Confidence is an uncalibrated point estimate.** `Claim.confidence` is a single self-reported number
   from one EXPLORE call (`ledger.ingest`: `confidence=float(rc.get("confidence", 0.0))`). LLM verbalized
   confidence is systematically overconfident (Xiong et al., arXiv:2306.13063). Greedy point-estimate
   selection underperforms uncertainty-aware policies for LLM agents (Felicioni et al., TMLR 2024,
   arXiv:2404.02649).

## 2. Design overview

Seven components, all mapping onto existing symbols:

| # | Component | Replaces / extends |
|---|-----------|--------------------|
| A | Hybrid promotion: elitism + Thompson-sampled tail | `_promote` |
| B | Calibrated uncertainty (k-sample posterior + LLM Bayesian update + isotonic recalibration) | `Claim.confidence`, `ingest`, `apply_verification` |
| C | Hierarchical Quality-Diversity archive (resurfacing) | the `unverified` backlog |
| D | Three-state verification (confirmed / error / refuted) + defect feedback | `apply_verification`, `schemas.VERIFY`, `executors.verify` |
| E | Online-FDR resurfacing budget (optional-stopping guard) | new |
| F | Claim identity: lineage + embedding (same vs refined) | `embed.py`, `_source_index`, `Direction.parent_id` |
| G | Init-phase prior verification (calibration bootstrap) | `orchestrator.init`, `schemas.PRIOR` |

---

## 3. Component A — Hybrid promotion

**Status: IMPLEMENTED** (2026-07-08) in `orchestrator._promote` + `_beta_params`/`_conf_lower`, Config knobs
`promote_tau_high=0.75`, `promote_kappa=8.0`, `promote_z=1.0`, `promote_explore_frac=0.34`, `promote_seed=0`
(`promote_tau` retained but deprecated/unused). Since Component B's real posteriors don't exist yet, the
scalar `confidence` is turned into a Beta(`conf·κ`,`(1−conf)·κ`) via the concentration `κ`; the elitism
gate uses a normal-approx lower bound and the exploration slots draw from that Beta (`random.betavariate`,
seeded by `promote_seed + len(ledger.claims)` for reproducibility). B slots in by replacing κ with a
per-claim variance. Verified behaviourally (200-trial sim, batch of 9, keep=3): total promoted stays = 3
(budget-neutral); the two certain claims promote 100%; weak claims (conf 0.15–0.35, which the old 0.6 floor
pruned to 0%) now promote 2–8% scaling with confidence; the 0.60 mid claim promotes 73%.

**What "promote" means:** move a claim from the candidate pool into the VERIFY queue — i.e. spend an
(expensive) adversarial literature-check on it (→ confirmed / error / refuted). Un-promoted claims are NOT
discarded; they stay in the pool (Component C) and can be promoted in a later wave. `keep = ceil(fresh/eta)`
is the per-wave promotion *budget* (how many claims we're willing to verify this wave); percentile+Thompson
decide *which* claims fill those `keep` slots, not how many.

**UPDATE (2026-07-10): promotion = BEAM SEARCH + Thompson sampling.** The deterministic part *is* beam
search — keep the top-scored claims (best-first over the belief ledger), so we call it that rather than
"elitism/percentile." Each wave's budget is `keep = ceil(fresh/eta)` (the **beam width**); of those,
`n_beam = keep·(1−promote_explore_frac)` go to the **beam** (top claims by calibrated confidence,
niche-spread) and the rest are **Thompson-sampled** from the remaining pool. No percentile/threshold knob —
beam is inherently relative (always the top-k), which sidesteps the overconfident-tie problem that broke the
earlier value-threshold (`_elite_cut`, which logged `41 certain` on a 41-claim pool). Retired:
`promote_tau_high`, `promote_elite_pctl`, `promote_z`, `_elite_cut`, `_conf_lower`.

**UPDATE (2026-07-10): the Thompson posterior is LLM-derived AND its spread is now CALIBRATED against
verification.** EXPLORE and VERIFY emit, per claim, a point belief `confidence` (posterior mean) AND a
~90% credible interval `[conf_low, conf_high]` = how sure the model is given the evidence it read. Both are
calibrated against VERIFY's confirm/refute stream (Component B), because a monotone point map barely moves
the *beam* (which uses rank order) — the leverage is in the **interval**, which drives Thompson exploration:
- **Point map** (existing): `raw confidence → P(true)`. Corrects the level; used for the FDR cost and the
  honesty of the reported belief.
- **Width map** (new): `stated interval width → actual outcome variance` = the mean squared error of the
  calibrated belief for claims the model stated that width. If the LLM's widths track real error, wide-stated
  claims get a wide posterior; if the widths are uninformative, the map flattens and everyone gets the
  base-rate spread (widths ignored). Verified offline: informative widths → var 0.12→0.25 monotone;
  uninformative → flat.

`_beta_params` variance priority: (1) calibrated variance for the claim's width, else (2) the raw LLM
interval, else (3) fixed `promote_kappa`. Mean = calibrated confidence; spread = **verify-calibrated**
uncertainty — *"calibrate the belief, don't just trust the LLM's stated uncertainty."*

Keep the aggressive halving for the *certain* claims (exploit), sample the rest by *uncertainty*
(explore). This mirrors Hyperband's own hedge (an aggressive core + a no-early-stop reserve).

```
def _promote(batch):
    ranked  = sort(batch, key=posterior_mean, desc)
    # ELITISM — deterministic, only genuinely-certain claims skip the lottery.
    #   Bar is an uncertainty-aware LOWER bound, NOT the old 0.6 point estimate.
    certain = [c for c in ranked if c.conf_lower_bound >= TAU_HIGH]        # e.g. 0.8
    # EXPLORATION — Thompson-sample the remaining n - topk, weight by the full posterior.
    tail    = [c for c in ranked if c not in certain]
    sampled = thompson_sample(tail, k=EXPLORE_SLOTS)   # draw ~Beta/posterior per claim, take top-k of draws
    promote(certain + sampled)
```

- `thompson_sample`: for each tail claim draw a value from its posterior; promote the k highest draws.
  A claim with mean 0.5±0.3 can out-draw a claim with mean 0.55±0.05 — the surprising-discovery
  protection. No claim with nonzero posterior mass is ever *deterministically* excluded (Russo & Van Roy;
  Chapelle & Li, NIPS 2011, which also show TS beats UCB under *delayed/batched* feedback — our regime).
- `TAU_HIGH` is a high bar on the posterior lower bound, not a floor on the mean. `0.6±wide` now falls
  into the sampled tail instead of being deleted.
- Knobs: `TAU_HIGH` (elitism bar), `EXPLORE_SLOTS` (tail exploration budget per wave). Keep a nonzero
  `EXPLORE_SLOTS` even when many claims clear `TAU_HIGH` — that's the no-early-stop reserve.

## 4. Component B — Calibrated uncertainty

**Status: CORE IMPLEMENTED** (2026-07-09), live tail deferred. Done offline: `calibration.py` — a pure
isotonic (Pool-Adjacent-Violators) `Calibrator` that learns `raw_confidence → P(true)` from VERIFY's own
confirm/refute labels, with `fit`/`apply`/`ece` and an identity no-op below `calibrate_min_labels`. Wired
into the orchestrator: `_drain_verify_pool` logs a `(promotion-time confidence → outcome)` label per
terminal confirm/refute (ERROR is not a label) and refits every `calibrate_refit_every`; promotion now
scores on `_score(c)` = calibrated confidence (used by `_beta_params`, `_conf_lower`, and elitism), and the
FDR cost/settle now uses the promotion-time confidence too. Verified offline: isotonic cuts ECE 0.163→~0.00
on synthetic overconfident data, is monotone, stays identity below the label threshold, and leaves
promotion/selftest unchanged until fitted. **Live tail (needs a paid run):** (1) replacing the scalar with a
true k-sample `(mean, var)` posterior so kappa is no longer a hack — needs repeated codex scoring; (2)
computing embeddings/cosines in the loop and applying a posterior *bump* on corroboration via
`ledger.find_corroborators` (Component F's hook) — the actual "driver" that makes a weak-but-true backlog
claim resurface (Component C's boundary); (3) confirming the calibration map genuinely improves a real run.

**Bootstrap timing (observed live, mini run 2026-07-10):** the calibrator fits from the init prior-probe
labels PLUS the first round's verify labels — a run fit at 7 labels (3 probe + 4 round-1), refined to 23 by
the end. So "init + first verify → calibration" holds. Two caveats: the probe alone rarely reaches
`calibrate_min_labels` (set `prior_probe_k ≥ calibrate_min_labels` to fit from init alone); and an early fit
on ~7 points is rough — the reported `ECE 0.000` is in-sample/overfit, not a real out-of-sample number.

**Posterior, not point estimate.** Replace the scalar `Claim.confidence` with `(mean, var)` (or Beta
`(alpha, beta)`).

1. **Base signal — one fixed scorer, sampled k times.** Sample the designated scorer model at
   temperature > 0, k times; the spread across samples *is* the posterior. Cheap, and it's a single
   estimator we can calibrate. Watch the pathology: a confidently-wrong model gives k agreeing samples →
   falsely tight posterior (mitigated by the cross-family check below and by recalibration).
2. **LLM Bayesian update (resurfacing / new evidence).** When new evidence arrives, feed the scorer
   {prior belief + prior verdict/reason + new evidence} and ask for the *update*, not an absolute number:
   "does this raise/lower the belief, and by roughly what odds ratio?" Relative judgments calibrate far
   better than absolute scalars. This naturally carries a skeptical prior forward for resurfaced claims.
3. **Recalibration against our own verified outcomes.** VERIFY produces confirm/refute *labels*. Over a
   run accumulate `(raw_scorer_value, verified_outcome)` pairs and fit a monotone map (isotonic / Platt)
   `raw → P(true)`. Apply it before promotion.
   - **Estimator is fixed.** Calibration is per-estimator: pin `(scorer_model, prompt, k)`. The prompt is
     part of the estimator — changing it invalidates the map. **Use the same model family** (this is why
     multi-family scores must not be averaged into the calibrated scalar).
   - **Cold start.** Seed the map from prior runs' labels (`genomic_pancreatic_200/200b`); shrink toward
     that prior until the current run has enough labels. (See Component G for an in-run bootstrap.)
   - **Label bias.** Only verified claims get labels, and under the hybrid sampler that slice is
     non-random. Include the exploration-sampled (lower-confidence) verifications in the calibration set,
     not just elites — the hybrid gives us these for free.
4. **Cross-family disagreement = a separate uncertainty flag**, used only for high-stakes/contested
   claims, routed to *more exploration* — never folded into the calibrated scalar.

Information-theoretic acquisition (Predictive Entropy Search; Hernández-Lobato et al., arXiv:1406.2541)
is a heavier alternative that selects by information gain over the whole predictive distribution; Expected
Improvement under-explores high-uncertainty regions and is *not* recommended here. TS is the default.

## 5. Component C — Hierarchical Quality-Diversity archive (resurfacing)

**Status: IMPLEMENTED** (2026-07-09) in `orchestrator._promotable_pool` / `_niche` / `_pick_spread` and the
`_promote` rewrite. Promotion now fills its `keep = ceil(fresh_batch/eta)` slots from the WHOLE pending pool
(every gated, still-unverified, not-currently-queued claim = this wave's fresh claims + the carried-over
backlog), not just the current wave. Niche descriptor = a claim's primary `aspect`; elitism and the
Thompson-sampled tail are both drawn niche-spread (round-robin per niche) so one crowded aspect can't
monopolise the budget. Per-round verify load stays tied to fresh throughput (budget-neutral). Verified
offline: (A) an un-promoted weak claim persists in the pool instead of rotting; (B) when new evidence bumps
its confidence it resurfaces as an elite the next wave; (C) a *static* weak claim (conf 0.22) is promoted
~8% of trials vs exactly 0% under the old hard floor; (D) with a 30-claim wave promotions span all 5 niches;
per-round total stays = keep. NOTE the C/B boundary: C only provides the *mechanism* (the claim stays
sampleable, never deterministically pruned); the *driver* that makes a weak-but-true claim actually
resurface is new evidence raising its posterior — that is Component B/F, not yet built. Re-scoring an
archived claim when corroborating evidence arrives (`_source_index`/embedding match) is deferred to B/F.

Replace the inert backlog with a **QD archive** (MAP-Elites style; Pugh, Soros & Stanley, 2016): partition
claims into niches, keep the best-per-niche alive, spread verification budget across niches so a surprising
claim in a thin niche isn't crowded out by 20 claims in a popular one.

- **Niche descriptor:** the existing `Claim.aspects` (mechanism / biomarker-class / evidence-type).
- **Two-level scoring — CORRECTED (2026-07-10):** the PRIMARY hierarchy is **direction → its claims**
  (structural: `Claim.direction_id`, `Direction.produced_claims` — already in the ledger). The two-level
  score is per-DIRECTION: `ledger.direction_scores()` scores each direction by ITS produced claims
  (tallies + `strength` = confirmed/(confirmed+refuted) + `thin` = explored-but-nothing-confirmed /
  `contested` = confirmed≈refuted), recomputed as evidence arrives. `_select_batch` boosts an open
  direction's `promise` by `niche_boost` (0.15) when its **parent direction** (`d.parent_id`) is
  thin/contested — i.e. follow up where the investigation was inconclusive. Verified offline.
  - *Earlier mistake:* the first cut used `niche_scores()` (grouping by **aspect**, a cross-cutting
    bucket) as "the hierarchy" — wrong grouping. `niche_scores()` is retained but **demoted** to a
    promotion-diversity tie-breaker only (that role lives in `_pick_spread`, which round-robins the
    verify slots across aspects so one biomarker type can't monopolise the budget across directions).
- **Re-scoring on new evidence:** when a new EXPLORE wave produces a claim that corroborates an archived
  one (matched via `_source_index` / embedding — Component F), update its posterior (Component B.2) and
  let it re-enter the sampler (Component A). Re-sweep the archive at STALL/checkpoint, not only on fresh
  batches.

**DRIVER IMPLEMENTED** (2026-07-09): `ledger.corroborate(claim, corroborators)` raises a backlog claim's
confidence when corroborators bring INDEPENDENT sources for the same assertion (only sources the claim
doesn't already cite count; diminishing per-source bump, capped, never lowers). Orchestrator
`_rescore_corroboration(new_claims)` runs each explore wave before promotion: it finds backlog claims a
fresh claim is a text near-duplicate of (embedder `rank`, cosine ≥ `corroborate_thresh`) and corroborates
them, so a weak-but-true claim whose evidence just grew resurfaces into the sampler. This closes the C/B
"driver" gap. Config: `corroborate_enabled`, `corroborate_thresh=0.88`, `corroborate_per_source=0.04`.
Verified offline: the bump rule (independent sources raise confidence +per_source each, same-source
contributes 0, capped at 0.95, never lowers) is unit-tested in `selftest`. **Live tail:** the corroborator
*discovery* uses the embedder (Azure), exercised only on a real run; the k-sample `(mean,var)` posterior
(Component B.1) is still outstanding.

## 6. Component D — Three-state verification

**Status: IMPLEMENTED** (2026-07-09). Ledger: `ERROR` state + `Claim.defect`/`correction_attempts` fields
(serialized); `apply_verification` now routes on a three-state `verdict` via `_verdict()` — confirmed→lock,
error→set ERROR + spawn a bounded "Correct and resubmit" direction carrying the defect, refuted→"Re-investigate"
direction — with a `max_corrections` peeking guard (default `correction_max_attempts=2`) that downgrades a
claim to REFUTED once its fix budget is spent. `schemas.VERIFY` gains `verdict`(enum)/`defect` (keeps the
legacy `confirmed` bool as a mirror; `_verdict()` falls back to it for old payloads). `executors.verify`
prompt rewritten to **search the literature to confirm/refute, using the cited source only as an anchor**,
and to emit the verdict + defect. Verified offline in `selftest`: error→ERROR+correction direction, two more
errors exhaust the budget→REFUTED, refuted→corrective direction, and a legacy no-`verdict` payload still maps
confirmed→CONFIRMED. **Live tail (needs a paid run):** whether the LLM actually performs good independent
literature search (vs just re-reading the anchor) and classifies error-vs-refuted well is only judgeable on
a real run. **Deferred:** bounding corrections across EXPLORE-*regenerated* refinements (not just the same
claim id) needs claim-lineage — Component F.

**Core principle: VERIFY is literature-grounded, not source-bound.** It runs a web/literature search to
confirm *or* refute the claim. Any cited `claim.evidence` is used as an **anchor** (a starting point / prior
to check and reconcile), **not** as the sole target. This is a change from today's `executors.verify`, which
fetches only the single cited source (`claim.evidence[0]`) and never seeks independent corroboration or
contradiction. Verifying against the field — not just against the paper the claim happened to cite — is what
makes a genuine `refuted` verdict (the field says otherwise) possible, and it lets VERIFY confirm a
true-but-mis-cited claim by finding the *right* source.

Today VERIFY is binary (`confirmed` true/false) but the schema *already* collects `corrected_numbers` and
`corrected_source` — so it already distinguishes "citation was wrong but the claim may hold" from "the
claim is unsupported"; it just discards that distinction into REFUTED. Formalize three states:

| State | Meaning | Signal | Routing |
|-------|---------|--------|---------|
| **confirmed** | literature supports the claim (via the anchor and/or independently found sources) | `confirmed=true` | lock, graduate |
| **error** (correctable) | core assertion is supported by the literature, but the claim as written has a defect — wrong attribution / numbers / overstated scope / mis-cited anchor | `confirmed=false` **and** `corrected_source`/`corrected_numbers` populated, core survives correction | back to EXPLORE with the specific defect → EXPLORE emits a *refined* claim (new node, Component F) |
| **refuted** (fundamental) | the literature search finds no support, or affirmatively contradicts the claim | `confirmed=false`, no salvageable core, `refutation` cites the contradicting evidence | stays down; skeptical prior; revive only on substantially new evidence under FDR budget (Component E) |

**Why VERIFY costs real money (2026-07-10):** because of this change, VERIFY is no longer a single-source
fetch — it runs a *literature search* (web_search + read several sources + reason), essentially a focused
re-investigation. Measured on the mini run it averaged **$0.11/call vs $0.20 for an EXPLORE** — comparable,
not cheap. Aggregate verify spend is the bigger line item because there are simply *more* verify calls
(every promoted claim + every error→resubmit re-verification). Levers if it's too costly: anchor-only verify
(skip the web search) for routine claims and reserve full literature search for high-stakes ones; lower
`correction_max_attempts`; the Component E FDR budget already throttles the tail.

Two builds required:

- **Literature-search verification (change to `executors.verify`).** The prompt goes from "fetch the ONE
  cited source and check it" to "search the literature to confirm or refute this claim; if a source is
  cited, anchor on it — verify its attribution/numbers and seek independent corroboration or contradiction."
  It already runs `mode="research"` (web_search enabled), so this is a prompt/logic change, not new plumbing.
  Search **depth scales with stakes/budget** via `budget_hint` (a quick check for routine claims, a deeper
  multi-source sweep for high-stakes/contested ones) — but it is always a *search*, never a single-source
  fetch. The provided evidence being optional means VERIFY can also run on claims that arrive with no
  citation (see Component G).
- **Structured defect feedback (claim-level).** VERIFY emits a `verdict ∈ {confirmed, error, refuted}` and
  a `defect` payload. `error` routes as a *targeted correction task* carrying the defect + the already-
  collected `corrected_*` fields — not a fresh open direction. This lets EXPLORE fix the author count /
  re-scope / swap in the correct source, instead of re-exploring the whole direction.

**Peeking guard (ties to E):** the error→fix→re-verify loop is itself a peeking risk. Bound it:
≤2 correction attempts per claim; each must address the *named* defect (no re-rolling the same check); a
claim corrected twice and still failing → downgrade to refuted. Attempt budget draws from the alpha-wealth
in Component E.

## 7. Component E — Statistical validity: online-FDR resurfacing budget

**Status: IMPLEMENTED** (2026-07-09) as the `AlphaInvesting` class + a gate in `_drain_verify_pool`, Config
knobs `fdr_enabled`, `fdr_wealth0=0.5`, `fdr_alpha=0.05`, `fdr_payout=0.05`, `fdr_alpha_min=0.005`. Each
verify invests `cost(conf)=alpha_min + alpha·(1−conf)` (speculative low-confidence tests cost more); a
confirmation pays `payout` back, a refutation/error just spends. The drain gate is cheapest-first (queue is
already sorted by confidence desc): when the cheapest test is unaffordable the round halts. Verified offline:
a healthy 40%-confirm 44-test run keeps wealth positive and skips 0 tests; an all-refute speculative stream
brakes after 12 tests; at low wealth only high-confidence tests are affordable. **Tuning caveat:** the knob
values (wealth0/payout balance) were set from principle, not calibrated on a live run — a real run may want
them adjusted so the brake never fires on a healthy trajectory. The mapping to formal alpha-investing is
deliberately pragmatic (confidence-derived cost, not a p-value), per "don't over-optimize."

Resurfacing is structurally an **optional-stopping ("peeking") machine**: each resurface is another shot
at a fluke "confirmed" (from verifier sampling variance or cherry-picked evidence). Left unchecked this
inflates the ledger's false discovery rate.

Rules:

1. **Re-test only on genuinely new evidence** — never re-roll the same inputs.
2. **Combine evidence across tests** (posterior over everything seen) — never take the *max* verdict.
3. **Bound total error with an online-FDR / alpha-investing budget** (alpha-investing — Foster & Stine;
   LORD; SAFFRON — Ramdas et al., ICML 2018): a pool of "error wealth"; each verify spends some, a genuine
   confirmation pays some back. A stubborn false claim runs out of budget before it flukes a pass. This is
   the right tool because hypotheses arrive in an online stream where each decision is made without seeing
   the future.

**Not every resurfacing is p-hacking.** The tell is *why* it was refuted (Component D): a fixable-framing
`error` is cheap and legitimate to re-verify after correction; a fundamental `refuted` must clear a much
higher, budgeted bar.

> **DECIDED (2026-07-08):** use **alpha-investing** (Foster & Stine) as the default — simplest to
> implement over a claim stream (an alpha-wealth pool: each verify spends, each genuine confirmation pays
> back), adequate for now; not over-optimizing. LORD/SAFFRON can swap in later if FDR control proves loose,
> since they share the same alpha-wealth interface.

## 8. Component F — Claim identity (same vs refined)

**Status: IMPLEMENTED** (2026-07-09, lineage + matcher; embedding wiring deferred to B). Claim gains
`parent_claim_id`, Direction gains `corrects_claim_id` (both serialized). Correction/re-investigation
directions record which claim they descend from; `ingest` propagates `parent_claim_id` to regenerated
claims AND inherits the ancestor's `correction_attempts`, so Component D's fix budget now bounds the loop
across EXPLORE-*regenerated* refinements (the gap D flagged). Helpers: `lineage(claim)` (ancestor chain,
for carrying a refutation forward as skeptical context), `same_assertion(a,b,cosine=None,thresh=0.88)`
(shared resolvable source OR near-duplicate text — the ledger stays embedding-agnostic; the caller supplies
cosines), and `find_corroborators` (the hook Component B's re-scoring uses to raise a backlog claim's
posterior on independent corroboration). Verified offline in `selftest`: lineage propagation, cross-regen
budget inheritance → REFUTED when exhausted, source/cosine matching, and a JSON round-trip of the new fields.
**Deferred to B:** actually computing the embeddings/cosines in the loop and applying the posterior bump on
corroboration.

Decide by **lineage + embedding**, not string match:

- **Structural lineage (already present):** a refutation-spawned corrective direction has `parent_id` back
  to the claim's direction; claims EXPLORE produces from it are *known descendants*. Reliable, no guessing.
- **Semantic identity:** cluster with `embed.py` (Azure text-embedding-3-large) cosine similarity + source
  overlap (`_source_index`). The niche/group (Component C) is this clustering.

Treatment differs:

- **Same assertion + same evidence, resurfaced** → carry the refutation as a **skeptical prior** (E's
  peeking guard).
- **Refined claim** (narrower scope / corrected attribution / *new* evidence) → **new node linked to the
  ancestor**; the refutation reason is **context** ("your ancestor failed because X — addressed?"), *not*
  a probability penalty. A refinement must not inherit the veto or we block legitimate corrections.

## 9. Component G — Init-phase prior verification (calibration bootstrap)

**Status: IMPLEMENTED** (2026-07-09). Schema/seed scaffolding: `schemas.PRIOR` `candidate_answers` are now
`{answer, confidence, aspect}` objects; `executors.prior` asks for a calibrated per-candidate confidence;
`ledger.seed` accepts both the object form and legacy strings, stores the structured list on
`ledger.prior_candidates` (serialized), and prioritises each seeded "Confirm or refute candidate answer"
direction by its prior confidence (`promise = 0.5 + 0.4·conf`). Probe wired: `orchestrator._prior_probe()`
runs at the end of `init()` — it VERIFYs the top `prior_probe_k` candidates (VERIFY finds its own sources,
Component D; no mandatory GROUND), and `_probe_apply` seeds the Component B calibrator with the real
`(prior confidence → outcome)` label, adds a confirmed prior as an early grounded claim, and lets refuted
priors spawn their re-investigation direction. Verified offline: seed prioritisation + JSON round-trip
(`selftest`), and `_probe_apply` label-logging / claim-promotion on synthetic verdicts. Config:
`prior_probe_enabled`, `prior_probe_k=5`. **Live tail:** the probe's VERIFY calls run only on a real
`init()` (each ~`verify_task_usd`), so the end-to-end calibration bootstrap is exercised on a live run.

After `init()` we already hold `candidate_answers` — the model's self-assessed best guesses. Verify them
*first*, before the main loop, to (1) seed the calibration map (Component B.3) warm, (2) confirm cheap
well-known priors early to anchor the report, and (3) catch confidently-wrong priors (the PRIOR step
already emits a "negative prior to test") before they steer the search.

Mechanism:

1. **PRIOR schema change:** `candidate_answers` is currently `array[string]` with credibility buried in
   prose. Make each candidate a structured object with a **self-reported confidence scalar** (and
   biomarker-class / evidence-type for the niche descriptor). This scalar is the `raw` in the calibration
   pairs.
2. **Init probe = VERIFY directly.** Because VERIFY now does its own literature search (Component D), a
   candidate answer with no `evidence` can be verified straight away — VERIFY finds the supporting or
   contradicting sources itself. GROUND is optional (it can seed a starting anchor and a niche descriptor,
   but is no longer a prerequisite). Each candidate runs through three-state VERIFY.
3. **Record `(prior_self_confidence, verify_outcome)`** → seed the isotonic map. The main loop then starts
   with a warm calibration instead of cold.
4. Confirmed priors become early grounded claims; `error` priors get corrected; `refuted` priors are
   downweighted as directions (their `Direction.promise` drops).
5. **Cost + validity:** bound the probe (small K, cheap per-check via `budget_hint`); these early
   verifications are part of the same online-FDR stream (Component E), not a free pass.

## 9b. LLM frontier reranker

**Status: IMPLEMENTED + live-validated** (2026-07-09). Raw embedding cosine is a weak *ranking* signal for
the frontier; for a not-huge candidate set an LLM judge ranks far better. `executors.rerank` scores each
candidate direction's value-to-pursue in [0,1] (reason mode, no tools); `_select_batch` LLM-ranks the whole
frontier directly when it is small (`≤ rerank_direct_max`, default 60), else uses the embedding promise to
shortlist a top-N (`rerank_pool`, default 50) and reranks just those — the "embed → top-N → LLM rerank"
pattern. Config `rerank_frontier` (default on). Live smoke: relevant/specific directions scored 0.89–0.97,
an off-topic vague one 0.0, ~$0.12/call. The same embed-shortlist-then-LLM-judge pattern can extend to
corroboration matching (F) and context selection — noted as follow-ons.

---

## 10. Code touch-points

- `orchestrator._promote` → Component A (hybrid), knobs `TAU_HIGH`, `EXPLORE_SLOTS`; retire `promote_tau`.
- `ledger.Claim` → `confidence: float` becomes a posterior `(mean, var)` or Beta `(alpha, beta)`; add
  `verdict` (three-state), `defect`, lineage/identity fields.
- `ledger.ingest` / `apply_verification` → write posteriors; apply calibration map; three-state routing.
- `schemas.VERIFY` → add `verdict`, `defect`; `schemas.PRIOR` → structured `candidate_answers` w/ confidence.
- `executors.verify` → literature-search verification anchored on cited evidence (evidence optional) +
  structured defect/verdict output; `executors` → correction task + init VERIFY probe on candidate answers.
- new: QD archive (Component C) over the backlog; calibration module (isotonic/Platt, cross-run seed);
  online-FDR budget (Component E); identity/clustering via `embed.py` + `_source_index` (Component F).

## 11. Validation plan

1. **Offline replay:** run the new `_promote` + QD archive against the existing
   `v2_runs/genomic_pancreatic_200b` ledger — how many of the 114 backlog claims would resurface, and are
   any of them true-but-weak that the old floor killed?
2. **Calibration curve:** plot raw scorer value vs verified P(true) on `200/200b` labels; fit + report ECE
   before/after isotonic.
3. **Three-state audit:** re-classify the 27 run refutations into error vs refuted — expectation (from the
   run) is that most are *error* (real paper, mostly-correct numbers, overreach), which the old binary lost.
4. **Live $50 run** on `genomic_pancreatic` with the new core; compare confirmed-claim yield, FDR proxy,
   and cost vs the v2 baseline.

## 12. References (deep-research, 3-0 adversarially verified unless noted)

- Russo & Van Roy, *Learning to Optimize via Posterior Sampling* — web.stanford.edu/~bvr/pubs/LearningToOptimize.pdf
- Chapelle & Li, *An Empirical Evaluation of Thompson Sampling*, NIPS 2011 — microsoft.com/en-us/research/wp-content/uploads/2016/02/thompson.pdf
- Felicioni et al., *On the Importance of Uncertainty in Decision-Making with LLMs*, TMLR 2024 — arxiv.org/abs/2404.02649
- Hernández-Lobato et al., *Predictive Entropy Search*, 2014 — arxiv.org/abs/1406.2541
- Li et al., *Hyperband*, JMLR 16-558 — jmlr.org/papers/volume18/16-558/16-558.pdf
- Li et al., *ASHA / Massively Parallel Hyperparameter Tuning* — arxiv.org/abs/1810.05934
- Wistuba & Pedapati (LCRankNet), ICML 2020 — proceedings.mlr.press/v119/wistuba20a/wistuba20a.pdf
- Pugh, Soros & Stanley, *Quality Diversity*, Front. Robotics & AI 2016
- Lehman & Stanley, *Abandoning Objectives*, Evol. Comp. 2011
- Xiong et al., *Can LLMs Express Their Uncertainty?* — arxiv.org/abs/2306.13063 (calibration; not in verified top-25)
- Ramdas et al., *SAFFRON*, ICML 2018 — proceedings.mlr.press/v80/ramdas18a/ramdas18a.pdf (online FDR; not in verified top-25)

> Coverage note: the online-FDR angle (Component E) and LLM-confidence calibration specifics (Component B)
> were *not* covered by the deep-research verified findings — treat those two components as designed-from-
> principles pending a focused follow-up search.
