# Formal algorithm spec (summary)

This page is a prose-and-table rendering of the formal specification in
`METHODOLOGY_v2_algorithm.tex` (LaTeX, compiles to a ~7-page PDF). It covers the
notation, the parameter table, and every algorithm block: the main loop, INIT and
the prior-probe, frontier selection, ingest/lineage, corroboration, beam-plus-Thompson
promotion, the FDR-gated three-state verify with isotonic calibration, the
Pool-Adjacent-Violators calibrator, the direction-level hierarchy score, and the cost
model. The math is explained rather than pasted verbatim.

Related: [Methodology v2 (design rationale)](./methodology.md) ·
[Promotion redesign: Components A-G](./promotion-redesign.md) ·
[The orchestration loop](../architecture/orchestration-loop.md) ·
[Promotion and verification](../architecture/promotion-and-verification.md) ·
[Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) ·
[Config knobs (reference)](../reference/config-reference.md) ·
[documentation index](../README.md)

> **Altitude: design / rationale.** This is a faithful summary of the intended
> mathematical design as written in the spec. It describes *intended* behavior and may
> include parts that are simplified, renamed, or not yet built in the code. Where a name
> here differs from the running implementation, treat the module docs
> ([orchestrator.py](../modules/orchestrator.md), [ledger.py](../modules/ledger.md),
> [calibration.py](../modules/calibration.md)) as the source of truth for what actually
> executes. Symbols and citations below refer to `METHODOLOGY_v2_algorithm.tex`.

---

## 1. Objects and notation

The agent's whole state is a **belief ledger**
`L = (Directions, Claims, Priors, glossary)`, a two-level hierarchy: *directions* are
questions to investigate, and each direction owns the *claims* produced while
investigating it (`METHODOLOGY_v2_algorithm.tex:34`).

### Direction

A direction `d` (`METHODOLOGY_v2_algorithm.tex:39`):

| Field | Symbol | Meaning |
|---|---|---|
| question | `q_d` | the question this direction investigates |
| parent | `π_d` | parent direction (the hierarchy edge) |
| status | `σ_d` | lifecycle state (see below) |
| promise | `ρ_d ∈ [0,1]` | frontier score used to pick what to explore next |
| produced claims | `Π_d ⊆ Claims` | claims generated under this direction |
| corrects | `χ_d` | the claim this direction was spawned to correct (else ⊥) |

Direction status `σ_d ∈ {OPEN, EXPL, DONE, PROM, CLOSED}`
(`METHODOLOGY_v2_algorithm.tex:46`).

### Claim

A claim `c` (`METHODOLOGY_v2_algorithm.tex:48`):

| Field | Symbol | Meaning |
|---|---|---|
| text | `txt_c` | the assertion |
| aspects | `asp_c` | topical tags; first one becomes the QD niche |
| evidence | `E_c` | source set |
| verdict | `v_c` | verification state (see below) |
| posterior | `θ_c, [ℓ_c, h_c]` | LLM posterior: mean and ~90% credible interval |
| owner dir | `d_c` | the direction that produced it |
| defect | `def_c` | recorded reason when refuted/erroring |
| corrections | `n_c` | number of correction attempts so far |
| parent claim | `φ_c` | prior version, for lineage across regenerations |

Claim verdict `v_c` is one of four states (`METHODOLOGY_v2_algorithm.tex:61`):

| State | Symbol | Meaning |
|---|---|---|
| Unverified | `U` | produced, not yet tested |
| Confirmed | `C` | literature supports it; locked |
| Refuted | `R` | contradicted or unsupported |
| Error | `E` | fixable defect; eligible for a bounded correct-and-resubmit loop |

### Prior candidate

A prior candidate `p = (ans_p, θ_p, aspect_p)` is a model self-scored guess produced
before any tool use (`METHODOLOGY_v2_algorithm.tex:63`).

### Derived functions

Four functions derived from ledger state (`METHODOLOGY_v2_algorithm.tex:66`):

| Function | Definition |
|---|---|
| provenance gate `g(c)` | 1 iff `c` has at least one *resolvable* source; the admission test for promotion and corroboration |
| niche `ν(c)` | first aspect of `asp_c`, lower-cased (else ⊥); the QD diversity descriptor |
| calibrated score `s(c)` | `Γ(θ_c)`, the isotonic point map; `Γ = id` until fitted (Alg. 11 / §7) |
| Beta posterior | `Beta(s̄·κ_c, (1-s̄)·κ_c)` with `s̄ = clip(s(c), ε, 1-ε)` |

The posterior mean is the calibrated confidence `s(c)`; its spread is LLM-derived and is
itself calibrated against verification outcomes. EXPLORE/VERIFY emit a ~90% credible
interval `[ℓ_c, h_c]` per claim, and the Beta concentration `κ_c` is
(`METHODOLOGY_v2_algorithm.tex:76`):

```
κ_c = clip( s̄(1-s̄)/v_c − 1 , 1 , 200 )

         ⎧ W(h_c − ℓ_c)                  if the width map W is fitted (calibrated variance)
   v_c = ⎨ ((h_c − ℓ_c) / (2·1.645))²    else if an interval was given (raw)
         ⎩ s̄(1-s̄)/(κ+1)                 else (fixed fallback)
```

A wide or unreliable posterior gives a small `κ_c`, which makes the claim more likely to
be Thompson-sampled. The design intent is to *calibrate both the belief and its
uncertainty* (Alg. 11) rather than trust the raw stated interval
(`METHODOLOGY_v2_algorithm.tex:84`).

### Global run state

Beyond the ledger the run carries (`METHODOLOGY_v2_algorithm.tex:86`): explore/verify
budget pools `B_ex = ρB` and `B_ve = (1-ρ)B` with spends `S_ex, S_ve`; the verify queue
`Q`; the FDR wealth `W`; the calibration label set
`Λ = {(θ_raw_i, w_i, y_i)}` (raw confidence, stated interval width, and outcome
`y_i ∈ {0,1}`; matching §7 FitCalibrator); the isotonic map `Γ`; and a round
counter `t`.

### Parameters (`Config`)

The parameter table (`METHODOLOGY_v2_algorithm.tex:91`):

| Symbol | Meaning | Default |
|---|---|---|
| `B`, `ρ` | total USD budget; explore/verify split | —, `0.7` |
| `K` | best-first batch width (directions explored per wave) | `5` |
| `η` | Hyperband factor: `keep = ⌈|fresh|/η⌉` | `3` |
| `f_ex` | fraction of beam budget reserved for Thompson exploration | `0.34` |
| `κ` | fallback Beta concentration (claim has no LLM interval) | `8` |
| `w_0, α, ω, α_min` | FDR: initial wealth, invest scale, reward, floor cost | `0.5, 0.05, 0.05, 0.005` |
| `L_min, R` | calibration: min labels to fit; refit every `R` labels | `12, 6` |
| `τ_cos, δ_src` | corroboration: cosine threshold; per-source confidence bump | `0.88, 0.04` |
| `A_max` | max error→correct→re-verify attempts (peeking guard) | `2` |
| `β_niche` | frontier promise boost for thin/contested parent directions | `0.15` |
| `c_ex, c_ve, μ` | per-task target USD (explore/verify) and watchdog cap multiplier | `3.5, 1.5, 1.8` |
| `m_rr` | rerank directly if `|frontier| ≤` this, else shortlist then rerank | `60` |

---

## 2. Main loop

The orchestrator is a control shell around stateless executor calls
(`METHODOLOGY_v2_algorithm.tex:114`). Each round explores a wave of directions in
parallel, ingests their claims, rescoring backlog on corroboration, promotes a bounded
set to the verify queue, and drains the queue under an FDR brake.

```
INIT(Q)                          parse asks, seed ledger, probe priors (Alg. 2-3)
  │
  ▼   while  t < maxRounds
      and  {d : σ_d = OPEN} ≠ ∅
      and  B_ex − S_ex ≥ ½·c_ex
  ┌───────────────────────────────────────────────────────────┐
  │ t += 1                                                     │
  │ cap = μ·c_ex                                               │
  │ k   = max(1, min(K, ⌊(B_ex − S_ex)/cap⌋))   wave fits pool │
  │ batch = SelectBatch(k)          best-first frontier (Alg.4)│
  │   if batch = ∅ then break       frontier gave nothing      │
  │   for d in batch  IN PARALLEL   each ≤ cap USD, watchdog   │
  │     r = Explore(d); σ_d = DONE                             │
  │     fresh += Ingest(r.claims, d); add r.newDirections      │
  │ RescoreCorroboration(fresh)     backlog bump  (Alg. 6)     │
  │ Promote(fresh)                  beam + Thompson → Q (Alg.7)│
  │ DrainVerify()                   FDR + calibration (Alg. 9) │
  │ if spend since checkpoint ≥ B/6: converged = Evaluate()    │
  └───────────────────────────────────────────────────────────┘
  ▼
Finalize(converged)              LLM outline-then-fill over confirmed claims + refs
```

Termination: the loop stops when the round cap or budget half-task floor is hit, the
open frontier empties, or `SelectBatch` returns an empty batch. `Evaluate`'s convergence
verdict is *recorded* and passed to `Finalize`, but it does **not** appear in the
while-condition, so convergence does not itself gate the loop
(`METHODOLOGY_v2_algorithm.tex:120`, `METHODOLOGY_v2_algorithm.tex:132`).

---

## 3. Initialisation and prior probe

### INIT (`METHODOLOGY_v2_algorithm.tex:140`)

1. In parallel and in reason-mode (no tools), derive the required output `fields` and a
   `prior` from the question (`:143`).
2. For each open question in `prior`, add a `Direction` with promise `ρ = 0.6` (`:145`).
3. For each prior candidate `p = (ans, θ, aspect)`, add a "confirm/refute" direction with
   promise `ρ = 0.5 + 0.4·θ` (higher prior confidence → higher-promise seeded direction)
   and append `p` to `Priors` (`:146`).
4. Ground the first `groundTerms` key terms into the glossary in parallel (`:149`).
5. Call `PriorProbe` (Component G) (`:150`).

### PriorProbe (Component G) (`METHODOLOGY_v2_algorithm.tex:154`)

Verifies the highest-confidence priors up front to seed the calibrator with real
`(confidence → outcome)` labels before the main loop begins.

- Returns early if the probe is disabled or `Priors` is empty (`:157`).
- Takes the top-`k_probe` priors by `θ_p` (`:158`).
- For each, builds a sourceless claim, runs `Verify` (which finds its own sources via
  literature search), and applies the verdict (`:160`).
- If the verdict is `C` or `R`, appends a label `(θ_p, 1[v_c = C])` (`:163`).
- If confirmed *and* provenance-gated, admits the claim as an early grounded claim
  (`:164`).
- If enough labels accumulate (`|Λ| ≥ L_min`), fits the calibrator `Γ` (`:166`).

---

## 4. Frontier selection

`SelectBatch(k)` is a best-first frontier selector with a hierarchy boost and an optional
LLM rerank (`METHODOLOGY_v2_algorithm.tex:172`).

1. Take the open directions `O = {d : σ_d = OPEN}`; return ∅ if empty (`:175`).
2. Base promise from an embedding score
   `ρ_d^0 = w1·rel(d) + w2·EIG(d) + w3·nov(d) − w4·cost(d)`, where
   `rel = cos(d, question ↓ uncovered)`, `nov = 1 − max_{e∈explored} cos(d, e)`, and
   `cost = 1 − e^(−est_d/5)` (`:176`).
3. Compute `DirectionScores` (Component C hierarchy, §7). For any open `d` whose *parent*
   is `thin` or `contested`, boost `ρ_d^0 ← min(1, ρ_d^0 + β_niche)` — dig deeper where
   the parent was inconclusive (`:178`).
4. Sort by promise. If `rerankFrontier` is on, take the full ranked list when
   `|O| ≤ m_rr` else the top `rerankPool`, LLM-rerank each direction's value into `[0,1]`
   in reason-mode, overwrite `ρ_d`, and re-sort (`:183`).
5. Return the top `k` (`:188`).

---

## 5. Ingest and corroboration

### Ingest (Component F, lineage) (`METHODOLOGY_v2_algorithm.tex:194`)

For each non-empty raw claim, create a `Claim` with `v = U` and owner `d`. If the owning
direction was a correction/re-investigation direction (`χ_d ≠ ⊥` and `χ_d ∈ Claims`),
inherit lineage: set `φ_c ← χ_d` and carry the correction count `n_c ← n_{χ_d}` so the
attempt budget stays bounded across regenerations (`:200`). Index sources, append to
`Π_d`, and return the added claims (`:203`).

### RescoreCorroboration + Corroborate (Component B/C) (`METHODOLOGY_v2_algorithm.tex:209`)

The resurfacing driver. It cross-matches fresh claims against the unverified,
provenance-gated backlog by embedding similarity and raises confidence only on genuinely
*independent* evidence.

- Returns early if corroboration is disabled (`:212`).
- Backlog `back = {c ∈ Claims : v_c = U ∧ g(c) ∧ c ∉ Q ∧ c ∉ fresh}` (`:213`).
- For each provenance-gated fresh claim `c'` and each backlog claim `c` with
  `cos(txt_c', txt_c) ≥ τ_cos` (same assertion), call `Corroborate(c, c')` (`:214`).
- `Corroborate` computes the set `N` of source keys in `c'` that are resolvable and *not
  already* in `c`. If `N` is empty (same source only) it returns 0 and makes no change.
  Otherwise it raises confidence
  `θ_c ← max(θ_c, min(0.95, θ_c + δ_src·|N|))` — a diminishing, capped bump that never
  lowers confidence (`:220`).

---

## 6. Promotion: beam search + Thompson sampling (Components A + C)

`Promote(fresh)` decides which claims enter the expensive verify queue each wave
(`METHODOLOGY_v2_algorithm.tex:230`).

- Pool `U = {c ∈ Claims : v_c = U ∧ g(c) ∧ c ∉ Q}` — fresh plus carried-over backlog;
  return if empty (`:233`).
- **Beam width** `keep = max(1, ⌈|fresh|/η⌉)` is the per-wave verify budget. Split into
  `n_ex = max(1, round(keep·f_ex))` exploration slots and `n_beam = max(0, keep − n_ex)`
  exploitation slots (`:235`).
- **Beam (exploit):** sort `U` by calibrated score `s(c)` descending and take the top
  `n_beam` via `NicheSpread` (best-first, niche-spread across aspects) (`:238`).
- **Exploration:** from the tail `U \ P`, draw one sample per claim
  `x_c ~ Beta(s̄_c·κ_c, (1-s̄_c)·κ_c)`, sort by the draw, and take `keep − |P|` via
  `NicheSpread` (`:241`).
- Push the selected set to `Q` and set `σ_{d_c} ← PROM` (`:243`).

### NicheSpread (MAP-Elites diversity) (`METHODOLOGY_v2_algorithm.tex:247`)

Round-robins one claim per niche to spread the selection across aspects. Returns ∅ if
`n ≤ 0`; partitions the ordered input into per-niche queues keyed by `ν(c)` preserving
order; then repeatedly pops the head of each non-empty niche queue in insertion order
until `n` items are collected (`:250`).

The beam width bounds *how many* claims are verified per wave; the beam plus Thompson
sampling decide *which*. Unpromoted claims stay in `U` and can resurface later. Because
the beam ranks on *calibrated* score, once `Γ` deflates overconfident `θ` the beam
re-orders toward genuinely strong claims, and the LLM-derived posterior widths set how
aggressively Thompson explores the rest (`METHODOLOGY_v2_algorithm.tex:262`).

---

## 7. Verification, FDR budget, and calibration (Components D, E, B)

### DrainVerify (`METHODOLOGY_v2_algorithm.tex:271`)

FDR-gated three-state verification with online calibration.

- Return if `Q` is empty (`:274`).
- Sort `Q` by calibrated score `s(c)` descending — cheapest, most calibrated-certain
  tests first (`:275`).
- While `Q` is non-empty and `B_ve − S_ve ≥ ½·c_ve`:
  - **FDR brake:** if enabled and wealth `W < Cost(s(Q[0]))`, break — the error budget is
    spent (`:277`).
  - Pop a wave of up to `n` affordable claims and, in parallel, `Verify` each (anchoring
    on `E_c` if present) (`:279`).
  - Capture `θ_raw ← θ_c` and `s* ← s(c)` before overwrite, apply the verdict (`:281`).
  - Update wealth `W ← max(0, W − Cost(s*) + ω·1[v_c = C])` (`:283`).
  - On a decisive verdict (`C` or `R`), append the label `(θ_raw, w_c, 1[v_c = C])`
    (raw confidence, stated width, outcome) (`:284`).
  - Refit `Γ` once `R` new labels have accumulated (`:286`).

The wealth cost is `Cost(x) = α_min + α·(1 − x)`: speculative, low-score tests cost more
wealth (`METHODOLOGY_v2_algorithm.tex:289`).

### ApplyVerification — three-state routing (Component D) (`METHODOLOGY_v2_algorithm.tex:293`)

Sets `θ_c ← v.conf`, folds corrected numbers/source into the claim, and marks sources
verified only when attribution matches (`:296`). Then routes on the verdict
(`v.verdict ∈ {C, E, R}`, with a legacy fallback of `C` if `v.confirmed` else `R`):

| Verdict | Action |
|---|---|
| `C` | `v_c ← C`, lock, return ⊥ (`:298`) |
| `E`, `n_c+1 ≤ A_max` | record defect, `v_c ← E`, spawn a "correct & resubmit" direction with `χ = c`, `ρ = 0.70` (bounded fix loop) (`:300`) |
| `E`, attempts spent | fall through to refuted (`:303`) |
| `R` (or fallthrough) | `v_c ← R`, spawn a "re-investigate" direction with `χ = c`, `ρ = 0.65` (`:305`) |

The `A_max` cap is the peeking guard: it bounds error→correct→re-verify attempts so a
claim cannot be re-tested indefinitely.

### FitCalibrator (Component B) (`METHODOLOGY_v2_algorithm.tex:309`)

Calibrates *both* the point estimate and the interval width from labels
`Λ = {(θ_raw_i, w_i, y_i)}`.

- If `|Λ| < L_min`, set `Γ ← id`, `W ← ⊥`, return (`:313`).
- **POINT map** `Γ ← Isotonic({(θ_raw_i, y_i)})`: raw confidence → P(true), nondecreasing
  (`:314`).
- **WIDTH map** `W ← Isotonic({(w_i, (Γ(θ_raw_i) − y_i)²) : 0 ≤ w_i ≤ 1})`: stated
  interval width → outcome variance (`:315`). `W` is the mean squared error of the
  calibrated belief per stated width. Informative widths yield an increasing `W` (wide =
  unreliable = high variance); uninformative widths yield a flat `W` (widths ignored)
  (`:316`).

### The PAV calibrator (`METHODOLOGY_v2_algorithm.tex:321`)

`Isotonic` is Pool-Adjacent-Violators: sort by `x`, push singleton blocks, merge adjacent
blocks while their means violate monotonicity, then evaluate as the step function of
block means. The Thompson posterior variance from §1 is `W(w_c)` when `W` is fitted, else
the raw interval, else the fixed `κ`.

---

## 8. The hierarchy score (Component C)

`DirectionScores` maintains the two-level belief hierarchy (direction → its claims)
(`METHODOLOGY_v2_algorithm.tex:327`). For each direction `d` over its claims `C_d = Π_d`,
with `n+ = |{v_c = C}|`, `n− = |{v_c = R}|`, and `chk = n+ + n−`:

| Quantity | Definition |
|---|---|
| strength | `strength_d = n+ / chk` if `chk > 0` else `0` |
| thin | `thin_d = 1[ |C_d| > 0 ∧ n+ = 0 ]` — explored, nothing confirmed |
| contested | `contested_d = 1[ chk ≥ 2 ∧ 0.34 ≤ strength_d ≤ 0.66 ]` — confirms ≈ refutes |

A thin or contested direction is where the frontier should dig deeper; frontier selection
(§4) boosts open directions whose *parent* is thin/contested. The aspect grouping `ν` is
used only as the diversity tie-breaker inside `NicheSpread`, not as the hierarchy
(`METHODOLOGY_v2_algorithm.tex:338`).

---

## 9. Cost model and stop rule

### Model-aware pricing (`METHODOLOGY_v2_algorithm.tex:343`)

Each codex task's real cost is read from its rollout token count and scaled by the model
that actually ran:

```
usd(task) = [ (input − cached) + output ] × rate(m)          (billed tokens × rate)

           ⎧ $10 /M   m ∈ {gpt-5.x, -codex}
   rate  = ⎨ $1  /M   m ∈ {-mini}
           ⎨ $0.3/M   m ∈ {-nano}
           ⎩ $10 /M   otherwise (default)
```

A single fixed rate over-charges cheap models by ~10× and starves their budget; keying
the rate on the model fixes both accounting and budget enforcement
(`METHODOLOGY_v2_algorithm.tex:356`).

### Termination / stop rule (`METHODOLOGY_v2_algorithm.tex:359`)

The loop stops when the budget or round cap is hit or the frontier empties. `Evaluate`
additionally computes a convergence verdict, but it is only recorded and forwarded to
`Finalize` (§2) — it is not a loop guard. That verdict is:

```
converged  ⟺  coverage = 1  ∧  backlog = 0  ∧  progress ≤ ε

coverage = (# asks answered) / (# asks)
quality  = n+ / (n+ + n−)                     (global confirm rate)
progress = Δ(covered + confirmed) / Δ$
```
