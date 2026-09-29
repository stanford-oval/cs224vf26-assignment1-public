# Plan: Process-based epistemics (v3)

**Status:** plan / design review. Nothing implemented.
**Scope:** replace self-graded confidence with process-derived belief status; separate *allocation*
(what to research next) from *adjudication* (what we believe); make verification an independent
reconstruction + adversarial challenge. Lands on top of the interactive-steering work already merged;
should be its own branch/PR.

This document is ordered **high-level → low-level**: read §1–§4 for the shape, §5 for the decisions that
need sign-off, §6–§12 for the mechanics, §13–§16 for migration, phasing, and risk.

---

## 1. Thesis

Today one number — the LLM's self-reported `confidence` on a `Claim` — does four jobs at once: it ranks
the beam, seeds the Thompson posterior, keys the online-FDR gate, and *stands in as the belief itself*.
That is the model grading its own work, and no amount of extra columns fixes it.

The redesign **splits allocation from adjudication**:

- **Allocation** (what to investigate/verify next) keeps beam search + Thompson sampling, but the
  posterior becomes *"probability that researching this next yields materially useful information"* —
  research yield, not truth.
- **Adjudication** (what we believe) becomes a **status derived by rules from events that actually
  happened** — evidence found, and the outcome of an independent verification — not a number the model
  picks.

Belief is expressed as a **coarse index of five buckets**, computed from a small fixed vocabulary of
**four verification outcomes**, computed over a flexible **evidence** layer.

---

## 2. Goals & non-goals

**Goals**
- Belief status is auditable: for any hypothesis you can answer *"which events put it in this bucket?"*
- Verification means *independent reconstruction*, not paragraph-by-paragraph review of the explorer.
- "Failed to verify" is distinct from "refuted."
- Allocation remains smart (beam + Thompson) without reusing a shaky confidence for truth.
- Structure is added only where it earns its keep (selection, state, reproducibility).

**Non-goals**
- No large claim ontology (`generalizes`/`supersedes`/`depends-on` graphs).
- No attempt to attach a calibrated probability to every hypothesis.
- Not "verify everything" — verification stays bounded (it gets *more* expensive, see §12).
- No change to the interactive-steering surface beyond what naturally reflects the new status.

---

## 3. Principles

1. **Confidence is not belief.** An LLM confidence may inform *allocation*; it never sets *status*.
2. **Status follows process.** The question shifts from *"how sure are you, 0–1?"* to *"did this evidence
   satisfy the stated verification test?"*
3. **Absence of proof ≠ proof of absence.** No reproduction → `need-more-information`; refutation requires
   actual contrary evidence or a valid counterexample.
4. **Independence is a gradient, not a binary** (§7.4).
5. **Allocation learns yield; verification determines belief.** The bandit and the adjudicator optimize
   different things and must not share a signal.
6. **Task-specific where it helps, minimal where it doesn't.** Evidence schemas vary by question; the
   status vocabulary and claim contract are fixed and small.

---

## 4. Architecture: three layers + the allocation/adjudication split

```
                          ┌───────────────────────────── ADJUDICATION ─────────────────────────────┐
 Layer 3  HYPOTHESIS STATUS   unexplored · need-more-info · weakly-validated ·
          (5 buckets)         strongly-verified · strongly-refuted        ← rules over Layer 2
                                        ▲
 Layer 2  VERIFICATION OUTCOME  reproduced · challenged-but-survived · overturned · inconclusive
          (4-word vocabulary)          ▲                                  ← independent reconstruction
                                        │                                    + adversarial challenge (§7)
 Layer 1  EVIDENCE  task-specific rows {finding, source, supports/contradicts/qualifies}
                                        ▲
                                        │
                          ┌───────────────────────────── ALLOCATION ───────────────────────────────┐
          beam search (exploit best candidates) + Thompson sampling (explore uncertain yield)
          posterior = P(researching this next yields useful info)   ← NOT P(true)
```

The two halves meet only at the ledger: allocation decides *which* hypotheses get explored/verified;
adjudication reads the resulting events and assigns status. Neither reads the other's private numbers.

**Terminology bridge to the code:** the proposal's *working hypothesis* ≈ the current `Claim` (a
proposition under test). The plan extends `Claim` with a claim contract + status and **extracts its
evidence into its own layer**. *Research direction* ≈ the current `Direction`.

---

## 5. The pivotal decisions (need sign-off before Phase 3–4)

These are where the redesign collides with machinery that's already built and tested. Recommendations
given; each is a real fork.

### D1 — Fate of the two-map isotonic calibrator (`calibration.py`)
It exists solely to recalibrate `confidence → P(true)` — exactly the thing §1 drops.
- **(a)** Retire it from the epistemic path.
- **(b) [recommended]** Repurpose it to calibrate *predicted research-yield → observed yield*, feeding the
  Thompson posterior (§9). Preserves the online-learning machinery and finally dissolves the
  "mini confirms everything → vacuous calibration" problem in `FIX_PLAN_post_review.md`, because the label
  becomes an observable research event, not model self-agreement.

### D2 — The Thompson reward signal
Currently rewarded by verify pass-rate. New: rewarded by **research yield** — a research action succeeds
if it does ≥1 of: changes a hypothesis's bucket, resolves a required part of the question, finds a
material contradiction, meaningfully narrows a claim, produces an independently verified conclusion, or
reveals a high-value new direction (§9.2). This is new, observable plumbing but far more groundable than
"was it true."

### D3 — Fate of online-FDR (`AlphaInvesting`)
Keyed on calibrated confidence to bound *false confirmations*. But "confirmation" is being redefined as a
process event (reconstruct + survive), and the FDR's statistical basis was already thin.
- **[recommended]** Demote it to a plain verify-budget rationer (or drop it); let the reconstruct+challenge
  protocol carry false-confirmation control.

---

## 6. Data model (low-level)

Target shape. Names map to current `ledger.py` structures; **bold** = new.

### 6.1 Hypothesis (extends today's `Claim`)
```
id
research_direction_id          # was direction_id
proposition                    # was `text`
**scope**                      # the claim contract (§6.2)
**support_condition**
**refutation_condition**
**status**                     # 5-bucket (§8); replaces `verification` as the headline
verification_state             # keep the 4-outcome record of the last attempt (§7.5)
evidence_refs                  # → Evidence rows (§6.3), replaces embedded `evidence[]`
**verification_refs**          # → Verification rows (§6.4)
aspects                        # keep (QD/niche behaviour space)
parent_hypothesis_id           # was parent_claim_id
**change_from_parent**         # short free-text (§6.5)
origin / pinned                # keep (interactive steering)
**yield_prior**                # allocation-only hint (§9); NOT surfaced as belief
```
`confidence` / `conf_lo` / `conf_hi` are **removed from the core belief path**. If retained at all they
live only as a weak `yield_prior` input and are never rendered as "how true."

**Provenance gate stays:** a hypothesis is only promotable/reportable if it has ≥1 evidence row with a
resolvable source (today's `graduates()`).

### 6.2 Claim contract (small, fixed)
Generated at EXPLORE time, tested at VERIFY time:
```
Claim (proposition):
Scope:                 # population / conditions / time window the claim is asserted over
Support condition:     # what evidence would count as supporting it
Refutation condition:  # what evidence would count as refuting it
```
Purpose: gives the verifier a concrete, *predeclared* test, and prevents two processes from "disagreeing"
when they're actually evaluating different scopes.

### 6.3 Evidence (new first-class layer, task-specific)
Minimal common wrapper (always present):
```
evidence_id
hypothesis_id
source / provenance            # resolvable SourceRef (today's model)
finding                        # what the source actually says, in context
relation                       # supports | contradicts | qualifies
```
Plus a **question-specific payload** (free-form dict), e.g.:
- empirical: `study_design, population, outcome, effect, limitations`
- mathematical: `lemma_or_derivation, proof_dependency, counterexample, verification_result`
- software: `input, expected, observed, environment, reproduction_status`

Only the wrapper is enforced by schema; the payload is question-shaped and not adjudicated on.

### 6.4 Verification record (new)
One row per verification attempt:
```
verification_id
hypothesis_id
outcome                        # reproduced | challenged-but-survived | overturned | inconclusive
independent_conclusion         # what the reconstruction concluded
challenge_finding              # strongest contrary evidence, if any
source_overlap                 # fraction shared with the explorer's evidence (§7.4)
independence_level             # gradient rung reached (§7.4)
```

### 6.5 Lineage (minimal)
`parent_hypothesis_id` + `change_from_parent` (e.g. *"narrowed population to experienced engineers"*).
On a new hypothesis the only decision is: **duplicate / refinement / genuinely new** — no taxonomy.

---

## 7. Verification protocol (the heart of the redesign)

Replaces the single adversarial `verify()` (today `executors.py:129`, which sees the claim text *and* its
cited anchor source).

### 7.1 Neutralize
Turn the hypothesis + scope into a neutral question. The verifier receives **only** the atomic claim,
scope, and support/refutation conditions. It does **not** receive: the explorer's chain of reasoning, its
confidence, the current status, or its preferred sources.
```
Under scope S, what is the best-supported answer to whether H is true?
Investigate independently. Do not assume the proposed answer is correct.
```

### 7.2 Independent reconstruction
A fresh-context process generates its own queries, retrieves its own sources, and reaches its own scoped
conclusion. The gold standard is *reconstructing* the conclusion from the normalized question — not
critiquing the explorer paragraph by paragraph.

### 7.3 Adversarial challenge (separate pass)
```
Find the strongest credible evidence that H is false, overstated, scope-dependent, or explained by an
alternative mechanism. Address the exact claim and scope, not a nearby claim.
```

### 7.4 Independence gradient
Independence is measured, not assumed (full model/source disjointness is often impossible in narrow
fields). Rungs, weakest → strongest:
1. Fresh context 2. Neutral prompt 3. Independent query generation 4. Independent retrieval
5. Different search seeds/databases 6. Different agent/model where available 7. Source-overlap measured.
Record the rung reached and the source-overlap fraction on the verification row.

### 7.5 Compare → outcome
Compare on six axes: same conclusion? reached via an independent path? evidence overlap? material
contradiction found? does it address the *same scoped* claim? does the conclusion still satisfy the
support/refutation condition? Map to the fixed vocabulary:
```
same conclusion, independently reached          → reproduced
strong challenge found but resolved             → challenged-but-survived
contrary conclusion / decisive counterexample   → overturned
mixed or insufficient evidence                  → inconclusive
```

### 7.6 Cost
Neutralize + reconstruct + challenge = **2–3 codex calls** per promoted hypothesis (all research/web
mode), vs 1 today. See §12.

---

## 8. Status rules (Layer 3, process-derived)

Status is a pure function of events — never chosen by the LLM.

| Status | Operational rule |
|---|---|
| **unexplored** | no meaningful evidence search completed |
| **weakly-validated** *(a.k.a. provisionally-supported)* | exploration found relevant direct support; not yet independently verified |
| **strongly-verified** | an independent process reconstructed the scoped conclusion **and** it survived an explicit contradictory-evidence search → `reproduced` or `challenged-but-survived` |
| **strongly-refuted** | an independent process found evidence meeting the predeclared refutation condition, or reliably reproduced the opposite result → `overturned` with *actual* contrary evidence |
| **need-more-information** | evidence mixed/indirect/dependent/scope-mismatched, or verification `inconclusive` |

Outcome → bucket:
```
exploration only, supporting evidence          → weakly-validated
reproduced OR challenged-but-survived          → strongly-verified
overturned (with real refuting evidence)       → strongly-refuted
inconclusive / disagreement / weak negative    → need-more-information
```
Key correctness fix vs today: **inability to reproduce defaults to need-more-information, not refuted**
(today's `apply_verification` maps "no support" → `refuted`).

---

## 9. Allocation (beam + Thompson, retargeted)

Selection is unchanged in *structure* (beam exploits, Thompson explores; today `_promote` /
`_beta_params` / `_score` in `orchestrator.py`) but repointed off truth.

### 9.1 What each selector optimizes
- **Beam** — exploit best candidates: relevance to the grand question, impact on the final answer,
  connection to unmet requirements, promising evidence so far, potential to resolve dependent
  hypotheses.
- **Thompson** — explore where another research action could pay off: weakly-validated and
  need-more-info hypotheses, underexplored directions, conflicting-evidence claims, uncertain-yield
  directions.

### 9.2 The posterior = research yield
```
Beta posterior over:  P(researching this hypothesis next produces materially useful info)
reward = 1 if the research action did ≥1 of {bucket change, requirement resolved, material
         contradiction found, claim meaningfully narrowed, independently verified conclusion,
         high-value new direction}, else 0
```
Per D1, the calibrator (if kept) maps *predicted yield → observed yield* to set the posterior mean/spread,
learning online from these observable rewards.

### 9.3 Separation guarantee
Beam/Thompson decide *what to investigate*; they never write status. The verification protocol (§7) is the
only writer of belief. This is the concrete expression of Principle 5.

---

## 10. Convergence

Refines today's `_checkpoint` rule. Stop when:
1. required parts of the question are addressed, **and**
2. no *critical* unresolved hypothesis could materially change the answer, **and**
3. further research has low expected value (Thompson yield posteriors are low across the frontier).

The **need-more-information bucket need not be empty at convergence** — it only must contain no unresolved
claim that would materially change the answer. (Otherwise the system researches forever, or forces
ambiguous claims into "verified" merely to stop.)

---

## 11. Metrics

- Replace `quality = confirmed/(confirmed+refuted)` (`metrics.py`) with a **bucket distribution**
  (counts per status) + a headline *"answered & strongly-verified"* share.
- `coverage` (ask-level judge) stays.
- Add **independence health**: mean independence rung + mean source-overlap across verifications (a low
  rung / high overlap means "review, not reproduction" — a quality alarm).
- `answeredness` becomes coverage × (strongly-verified share of required claims).

---

## 12. The revised loop (control flow)

```
Initialize:
    extract requirements
    extract priors
    generate initial research directions
    decompose initial hypotheses into atomic claim contracts (proposition, scope, support, refute)

Loop:
    select directions via beam + Thompson (yield posteriors)
    for each selected direction:
        generate bounded candidate hypotheses
        classify each: duplicate | refinement | new   (lineage: parent + change note)
        for each selected hypothesis:
            explore for supporting evidence; record contradictory evidence encountered
            status: unexplored → weakly-validated | need-more-information

    select hypotheses for verification via beam + Thompson + verification budget
    for each promoted hypothesis:
        independent_result = neutralize → independently reconstruct   (§7.1–7.2)
        challenge_result    = adversarial contrary search             (§7.3)
        outcome = reproduced | challenged-but-survived | overturned | inconclusive   (§7.5)
        status  = map(outcome)                                        (§8)
        if strongly-verified or strongly-refuted: update worldview
        if narrowed/corrected/overturned: spawn child hypothesis when appropriate

    update beam + Thompson state from observed research yield          (§9.2)

    stop when: required parts addressed
               ∧ no critical unresolved hypothesis can materially change the answer
               ∧ further research has low expected value               (§10)
```
Verification is still **bounded** (promotion + budget); it just becomes stronger and costlier per item
(§7.6), which makes the beam/Thompson pick-the-few even more important.

---

## 13. Migration map (current → target, by file)

| File | Today | Change |
|---|---|---|
| `ledger.py` | `Claim{confidence,conf_lo,conf_hi,verification,evidence[]}` | add `scope`/`support`/`refute`/`status`/`change_from_parent`; extract `Evidence` + `Verification` rows; keep provenance gate; `apply_verification` emits 4 outcomes and stops "no-support→refuted" |
| `calibration.py` | confidence→P(true) two-map | D1: repurpose to yield→observed-yield, or retire |
| `orchestrator.py` | `_score`/`_beta_params` on calibrated confidence; FDR gate; `_promote`; `_checkpoint` | repoint posterior to yield (§9); demote FDR (D3); status is written by verify, not promote; convergence per §10 |
| `executors.py` | single `verify()` sees claim+anchor; `explore` emits confidence | split into `neutralize`/`reconstruct`/`challenge`; `explore` emits the claim contract instead of a confidence number |
| `metrics.py` | `quality=conf/(conf+ref)` | bucket distribution + independence health (§11) |
| `schemas.py` | claim/verify schemas | contract fields; 4-outcome verify; evidence wrapper + task payload |
| `measure.py` / `metrics` | frontier scoring on promise | add yield-based frontier signals |
| interactive layer (`steer.py`, portal) | shows confidence/verification | render 5 buckets + independence health (Trajectory view already exists) |

---

## 14. Phasing (dependency-ordered, low → high risk)

- **Phase 0 — Status layer (additive, low risk, no behavior change).** Add the 5-bucket `status`, computed
  by rules from the *existing* 3 verification states; surface buckets in ledger/report/Trajectory. Makes
  belief auditable and sets up everything else. *Test:* offline bucket-assignment unit tests.
- **Phase 1 — Four outcomes + "failure ≠ refutation" (low risk, high value).** Extend `apply_verification`
  to emit `inconclusive`; stop mapping "no support found" → refuted. Independent of the bigger redesign.
  *Test:* selftest routing cases.
- **Phase 2 — Claim contract (medium).** Add scope + support/refutation conditions, generated in EXPLORE;
  thread into the verifier. Enables §7–§8 and kills scope-mismatch false disagreements. *Test:* schema +
  a live smoke run confirming contracts populate.
- **Phase 3 — Verification protocol (high, the heart).** Neutralize + independent reconstruction + separate
  adversarial challenge + source-overlap/independence gradient. *Test:* verify a known-true and a
  known-false claim; assert outcomes + independence recorded. **Budget-sensitive (§12).**
- **Phase 4 — Allocation split (high).** Repoint Thompson at research yield (D2), repurpose/retire
  calibration (D1), demote FDR (D3). *Test:* bandit reward accrues on observable yield events; no shared
  signal between allocation and status.
- **Phase 5 — Evidence layer + convergence (medium).** First-class task-specific evidence rows; lineage
  change_note; refined "no critical unresolved hypothesis" stopping rule. *Test:* evidence round-trip;
  convergence with a non-empty need-more-info bucket.

Each phase is shippable and offline-testable in `src/selftest.py` before the next.

---

## 15. Risks & open questions

- **Core re-architecture, not an add-on.** Phases 3–4 touch the verification and allocation heart; this is
  categorically bigger than interactive steering.
- **Cost.** ~2–3× verify cost per item (§12). Needs a budget re-tune; "verify all" stays off the table.
- **Independence is hard with one model + narrow fields.** Mitigation: treat it as a measured gradient
  (§7.4) and *report* the rung, rather than claiming binary independence.
- **Yield reward definition is a judgment call.** The six success conditions (§9.2) need tuning; too loose
  and the bandit rewards noise, too strict and it never explores.
- **Open:** does the LLM confidence survive *at all* as a `yield_prior`, or is it removed entirely? (Leaning
  weak-prior-only.)
- **Open:** how to detect "materially change the answer" for convergence (§10) without a truth oracle —
  likely an ask-level judge over required fields.

---

## 16. Keep / retire / defer

- **Keep:** beam + Thompson (for *allocation*), the provenance gate, two-pool budget, resurfacing pool,
  the evidence-aware convergence skeleton, the 5 buckets, interactive steering.
- **Retire (or repurpose):** confidence-as-truth; point-map calibration as an epistemic signal; online-FDR
  as a statistical guarantee.
- **Defer:** the full task-specific evidence-table system (Phase 5) — valuable but not on the critical path
  to the epistemic fix.
