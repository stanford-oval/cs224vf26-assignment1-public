# Methodology v2 (design rationale)

This page is the faithful rendering of the original `METHODOLOGY_v2` design record: why v2
exists, the core principle, the blackboard architecture, executor contracts, the loop,
direction selection, the two-pool budget, the evaluation instruments, and termination.

> **Design record, not an as-built spec.** This is the intended design captured 2026-06-28
> ("design doc, to be prototyped"). The shipped code differs in places, and some pieces
> described here were never wired. The most important divergences are flagged inline in
> call-out boxes; where the flag says a component is unbuilt, that reflects the current tree,
> not the design. For current behaviour read the architecture docs, and treat this page as
> the rationale behind them.

Related: [System overview](../architecture/overview.md) ·
[The orchestration loop](../architecture/orchestration-loop.md) ·
[The belief ledger](../architecture/belief-ledger.md) ·
[The executor roles](../architecture/executor-roles.md) ·
[Frontier selection](../architecture/frontier-selection.md) ·
[Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md) ·
[Promotion redesign: Components A–G](./promotion-redesign.md) ·
[Formal algorithm spec](./algorithm-spec.md) ·
[documentation index](../README.md)

---

## 0. Why v2 (what the baseline comparison taught us)

A 3-cell agent-vs-plain-codex comparison (pancreatic × protein / genomic / clinical-lab) plus
a finalize ablation produced four findings that this methodology is designed around.

| # | Finding | Takeaway |
|---|---|---|
| 1 | **Plain codex is competitive on coverage** — it matched or beat the full agent on completeness in 2 of 3 modalities. | "More retrieval" is not the differentiator. |
| 2 | **Codex confabulates provenance** — it finds the right paper (correct DOI) but invents the first author and occasionally a number (verified: "Liu MC"→Wu, "Guzikowski"→Chowdhury, 232→198 PDAC). | Accuracy, not recall, is its weakness. |
| 3 | **The agent under-integrates its own discoveries** — high-value evidence (the Avantect 2024 validation, `surfaced ×4`) sat in "surfaced works" and was never read or ranked. | Frontier management, not search, is the gap. |
| 4 | **The agent's stop-judge can't force more work** — it can reject a stop and suggest directions but cannot make the model keep generating. | Runs self-stopped well under budget. |

The finalize ablation isolated the mechanism: the structural scaffold (confidence classes,
numbered references, synthesis separation) comes entirely from the **prompt**, not the data —
codex given the same data + question produced equally-grounded content in its own free-form
style.

**Design implication.** The value to engineer is **structure + verification + systematic
frontier management**, not raw search volume. The only reliable way to get those is to take
control of the loop and the state away from the model.

> **Core principle.** The orchestrator owns the belief state and the control flow. Every LLM
> call is a pure function `f(task, context) → structured JSON` against a fixed schema. The
> model never decides the next step and never holds the belief state. This lets the harness
> *enforce provenance*, *force continued work*, *manage the frontier*, and *verify
> adversarially* — none of which the model does on its own.

---

## 1. Architecture — a blackboard system

The design is, by name, a **blackboard architecture**: a shared structured memory, a set of
specialist workers that read/write it, and a control shell that schedules them.

```
    ┌──────────────────────── CONTROL SHELL (harness) ─────────────────────────┐
    │  loop: select directions → dispatch executors → ingest → verify →         │
    │        checkpoint(evaluate, self-correct) → promote/prune → terminate     │
    └───────────────┬──────────────────────────────────────────┬───────────────┘
                    │ reads/writes                              │ dispatches
            ┌───────▼────────┐                        ┌─────────▼──────────┐
            │  BELIEF LEDGER  │                        │  EXECUTORS (codex)  │
            │ (the blackboard)│◄───── results ─────────│  PRIOR / GROUND /   │
            │ Directions +    │                        │  EXPLORE / VERIFY / │
            │ Claims + Sources│                        │  EVALUATE           │
            └─────────────────┘                        └────────────────────┘
```

- **Blackboard** = the belief ledger (§2).
- **Knowledge sources** = the codex executor tasks (§3).
- **Control shell** = the orchestration loop (§4).

This is the same shape as recent deep-research systems — e.g. DeepEvidence runs "an
orchestrator … maintaining a state machine that tracks search budgets, manages the evidence
graph, and coordinates specialized research subagents."

In the shipped code the three parts map to `ledger.py`, `executors.py`, and the
`Orchestrator` in `orchestrator.py` (the loop entry point is `orchestrator.py:319`). See
[System overview](../architecture/overview.md).

---

## 2. The belief ledger (a typed graph, not a scratchpad)

Two first-class objects — **Direction** (the frontier) and **Claim** (grounded findings) —
plus **SourceRef** (provenance). There is deliberately **no `Entity` type**: grouping is done
with free-form `aspects[]` tags, so the ledger works for topics that have no entities (open
problems, mechanisms, comparisons) as well as for entity-ranking tasks.

```
Ledger:
  question: str
  required_fields: list[str]          # explicit asks parsed from the question
  glossary: dict[str, GroundedTerm]   # terminology nailed during init
  prior: Hypothesis                   # the model's initial guess (init step 2)
  directions: dict[id, Direction]     # the frontier (a tree via parent_id)
  claims: dict[id, Claim]             # atomic grounded findings
  # the "answer" is assembled at synthesis by clustering claims on `aspects`.

Direction:
  id, question_text, parent_id, rationale
  status: OPEN | EXPLORING | CLOSED | PROMOTED
  promise: float                      # EIG-based priority (§5)
  est_cost: float
  pool: explore | verify
  produced_claims: list[claim_id]

Claim:
  id, text
  stance: supports | refutes | neutral
  aspects: list[str]                  # free tags — the general grouping key (replaces Entity)
  numbers: dict[metric, value]        # extracted quantitative claims (n, AUC, sens, spec…)
  evidence: list[SourceRef]           # REQUIRED — a claim with no evidence cannot graduate
  verification: unverified | confirmed | refuted
  confidence: float

SourceRef:
  title, authors, year, journal, doi | pmid | pmc, url
  verified: bool                      # checked vs OpenAlex / NCBI — anti-confabulation gate
  quote | line_range                  # the actual supporting text
```

**Why this fixes findings #2/#3:** a claim cannot enter the final answer or graduate to the
verify pool without evidence, and the frontier is explicit state, so nothing is ever
"surfaced but forgotten."

> **As-built note.** The shipped `Claim` carries a richer posterior than the sketch — a
> calibrated confidence with a `conf_low`/`conf_high` credible interval (see the `EXPLORE`
> prompt at `executors.py:134`) that drives Thompson-sampled promotion (§6). The design's
> single `confidence: float` is a simplification. For the shipped dataclasses see
> [The belief ledger](../architecture/belief-ledger.md) and [ledger.py](../modules/ledger.md).

---

## 3. Executor task contracts (codex as a schema-constrained pure function)

Each task takes a task spec + a *slice* of the ledger and returns validated JSON. Structured
output is what makes ledger updates deterministic (the forced-tool / StructuredOutput
pattern).

| Task | Input | Returns (schema, per design) |
|---|---|---|
| `PRIOR` | question | `{knowledge, prior_hypothesis, candidate_answers[], key_terms[], open_questions[]}` |
| `GROUND(term)` | one term | `{definition, SourceRef}` |
| `EXPLORE(direction, ctx)` | one direction + relevant claims | `{claims[] (each w/ SourceRef+numbers), new_directions[] (w/ promise, est_cost), dead_end:bool}` |
| `VERIFY(claim)` | one claim + its source | `{confirmed:bool, corrected_numbers{}, corrected_source{}, refutation?, confidence}` |
| `EVALUATE(draft, prev, rubric)` | current draft + previous checkpoint | `{per_axis_intrinsics, weakest_axis, corrective_directions[], regressions[]}` |

`EXPLORE` mirrors LATS's three LLM roles — action generator (new directions), grounded finder
(claims), and self-estimated value (promise). `VERIFY` is the adversarial role; `EVALUATE` is
Reflexion's reflection role.

The shipped executor set is broader than these five. Every role is defined as a function in
`executors.py`, but not all are called by the loop:

| Executor | Defined | Called by the loop? |
|---|---|---|
| `fields` (parse explicit asks) | `executors.py:38` | yes — INIT (`orchestrator.py:235`) |
| `prior` | `executors.py:49` | yes — INIT (`orchestrator.py:236`) |
| `ground` | `executors.py:79` | yes — INIT (`orchestrator.py:255`) |
| `explore` | `executors.py:95` | yes — main loop (`orchestrator.py:350`) |
| `verify` | `executors.py:148` | yes — verify drain (`orchestrator.py:569`) + prior-probe (`orchestrator.py:287`) |
| `rerank` | `executors.py:64` | yes — frontier rerank (`orchestrator.py:406`) |
| `patterns` | `executors.py:219` | yes — checkpoint / finalize (`orchestrator.py:637`, `:663`) |
| `finalize_report` | `executors.py:238` | yes — finalize (`orchestrator.py:670`) |
| `judge_coverage` | `executors.py:274` | yes — measurement (`orchestrator.py:607`) |
| `judge_forward` | `executors.py:292` | **no — defined, never called** |
| `evaluate` (EVALUATE) | `executors.py:307` | **no — defined, never called** (see §4/§7 call-outs) |

See [The executor roles](../architecture/executor-roles.md) and
[Executor output schemas (reference)](../reference/schemas-reference.md).

---

## 4. The orchestration loop

The design's loop, in sketch form:

```
# ── INIT (steps 1–3) ────────────────────────────────────────────────
required_fields = parse_fields(question)                 # 1 cheap call
prior    = codex.PRIOR(question)                         # knowledge + hypothesis
glossary = parallel(codex.GROUND(t) for t in prior.key_terms)   # terminology
ledger.seed(directions = prior.open_questions + as_directions(prior.prior_hypothesis),
            claims_to_test = prior.candidate_answers)    # candidates are hypotheses
                                                         # to CONFIRM OR REFUTE

# ── MAIN LOOP (until budget or convergence) ─────────────────────────
while budget.explore.remaining() and not converged:
    batch = ledger.top_k_open(K=5, by=promise)           # best-first expansion (§5)
    for d in batch: d.status = EXPLORING
    results = parallel(codex.EXPLORE(d, ledger.context(d)) for d in batch)

    for d, r in zip(batch, results):
        ledger.ingest(r.claims)                          # claims w/ provenance + numbers
        ledger.add_directions(r.new_directions)          # spawn children
        d.status = CLOSED if r.dead_end else EXPLORED
        for c in r.claims:                               # confidence-gated promotion (§6)
            if c.confidence >= PROMOTE_TAU and c.evidence:
                verify_queue.push(c); d.status = PROMOTED

    # VERIFY pool — separate budget so rigor never starves discovery
    while verify_queue and budget.verify.remaining():
        c = verify_queue.pop()
        v = codex.VERIFY(c)
        ledger.apply_verification(c, v)                  # confirm→lock; refute→corrective dir

    # CHECKPOINT — self-evaluate vs the PREVIOUS checkpoint, steer, decide stop (§7)
    if spent_since_checkpoint >= CHECKPOINT_COST:
        ev = codex.EVALUATE(ledger.draft(), prev=last_draft, rubric=RUBRIC)
        ledger.add_directions(ev.corrective_directions, priority=HIGH)   # Reflexion gradient
        rollback_if(ev.regressions)
        converged = novelty_plateau(K) and faithfulness_checklist_full()
        last_draft = ledger.draft()

# ── FINALIZE ────────────────────────────────────────────────────────
answer = ledger.synthesize()         # cluster CONFIRMED claims by aspect, render
citation_verify_pass(answer)         # final anti-confabulation sweep
```

> **As-built note — the checkpoint does not run EVALUATE.** In the shipped orchestrator the
> checkpoint (`orchestrator.py:623`) computes intrinsic metrics with `_measure`
> (`orchestrator.py:606`), and when progress stalls it distils cross-cutting `patterns` and
> spawns deeper directions from them — it never calls `executors.evaluate` and never builds a
> draft-vs-previous-draft reflection. There is no `EVALUATE` "semantic gradient" and no
> `rollback_if(regressions)` in the loop. The `evaluate` executor and the `judge_forward`
> executor are dead code (defined, never called). See §7 and
> [The orchestration loop](../architecture/orchestration-loop.md).

---

## 5. Direction selection — best-first + EIG, not full MCTS

**Pick the top-K (=5) OPEN directions by `promise`, expand, re-rank.** This is best-first /
beam search over the frontier. The priority function is **expected information gain (EIG)**
about the answer — Bayesian Experimental Design in the LLM-native BED-LLM form:

```
promise(d) = w1·relevance(d, question)          # embedding similarity / judged
           + w2·uncertainty_it_resolves(d)      # how much it would move the belief state
           + w3·novelty(d, explored)            # distance from already-explored directions
           − w4·est_cost(d)
```

`EXPLORE` self-reports `(promise, est_cost)` for each child. The formal EIG core and its
weighted-sum proxy:

```
EIG(d)     = H(θ | ledger_t) − E_{r∼p(r|d)}[ H(θ | ledger_t, r) ]
promise(d) = w₁·rel(d) + w₂·ÊIG(d) + w₃·nov(d) − w₄·ĉost(d)
  rel(d)  = cos(emb(d), emb(question | under-covered fields))
  ÊIG(d)  = Σ_{c∈claims(d)} (1 − conf(c))
  nov(d)  = 1 − max_{d'∈explored} cos(emb(d), emb(d'))
batch = top-K(O_t by promise),  K=5
```

The default `K=5` is `Config.K` (`orchestrator.py:70`). Batch selection is `_select_batch`
(`orchestrator.py:380`), with an optional LLM `rerank` pass (`orchestrator.py:406`).

> **As-built note.** The design says "the checkpoint evaluator periodically re-scores the
> whole frontier with a global view." That global EVALUATE re-scoring is not wired (the
> evaluator is dead code, §4); the shipped re-ranking is the per-batch `rerank` call, not a
> whole-frontier EVALUATE sweep. See [Frontier selection](../architecture/frontier-selection.md).

**Why not full MCTS / LATS rollout+backprop.** MCTS assumes a tree of *reversible* states
with a *terminal reward* to back-propagate. Research is neither: exploring a direction
*permanently* changes the belief state (you can't un-read a paper), and there is no terminal
reward to backprop. So borrow LATS's **selection-by-value** and **reflection**; skip rollout
and backpropagation. The correct frame is **best-first frontier expansion**, not game-tree
search.

---

## 6. Budget & promotion — Hyperband-style two pools

Two budget pools, `B_explore` (breadth) and `B_verify` (depth/rigor), a 70/30 split tuned per
task. In code this is the `Budget` class (`orchestrator.py:41`): `explore_cap = total·ρ`,
`verify_cap = total·(1−ρ)`, with `ρ = 0.7` (`Config.rho`, `orchestrator.py:69`). Embedding
and judge instrument cost is charged to the explore pool.

```
promote c → verify  ⟺  conf(c) ≥ τ ∧ evidence(c) ≠ ∅
B_explore = ρ·B,  B_verify = (1−ρ)·B,   ρ ≈ 0.7,   τ set so ≈1/η of claims graduate (η = 3)
```

This is **successive halving / Hyperband**: promising findings *earn* escalating budget;
uncertain directions keep churning cheaply in `B_explore`; weak ones are pruned (`CLOSED`).
Separating the pools guarantees you both **find** things and **nail** them — the agent's
under-integration (finding #3) was exploration starving verification.

> **As-built note — promotion is not a `conf ≥ τ` floor.** The shipped promotion (`_promote`,
> `orchestrator.py:504`) is the "Component A" redesign: a per-wave **beam** of size
> `ceil(fresh_claims / η)` with `η = 3.0` (`Config.eta`, `orchestrator.py:72`), selected by
> calibrated confidence, plus a **Thompson-sampling** exploration reserve of
> `promote_explore_frac = 0.34` of the beam (`orchestrator.py:74`). The hard threshold
> `promote_tau = 0.6` is **DEPRECATED and unused** (`orchestrator.py:71`, kept only for CLI
> back-compat). Within the explore pool, only `explore_work_frac = 0.85` (`orchestrator.py:77`)
> is spent on EXPLORE waves; the remainder is reserved for judges and embeddings. Target
> spends: `explore_task_usd = 3.5`, `verify_task_usd = 1.5` (`orchestrator.py:79–80`). See
> [Promotion redesign: Components A–G](./promotion-redesign.md) and
> [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md).

---

## 7. Evaluation — two instruments, same four axes

The four axes are **Correctness** (no hallucination), **Completeness** (diverse coverage),
**Forward-looking** (good next directions), **Faithfulness** (answers the question as asked).
They are measured **two different ways** depending on whether you are grading finished outputs
or steering a live run.

### 7a. Offline instrument — pairwise, cross-system (grades finished reports)

- **Pairwise, not absolute.** LLM judges are far more reliable at "which is better on axis X"
  than at absolute 1–5.
- **Correctness is source-grounded, not judge-vibe:** sample claims → fetch each cited source
  → score = fraction faithful + penalise unsupported assertions. This is the axis that
  separates the systems, so it must check against sources or the judge confabulates too.
- **Judge-bias controls:** randomise A/B order (position bias), control for length (longer ≠
  better), use an adversarial panel for the correctness axis.

### 7b. In-loop instrument — intrinsic counts + temporal self-delta (steers the run)

A checkpoint has **one** evolving state and **no Report B**, so cross-system pairwise is
impossible there. Instead measure each axis **intrinsically** and compare to **your own
previous checkpoint**:

| Axis | Intrinsic checkpoint measure | Delta → action |
|---|---|---|
| Correctness | verification pass-rate `confirmed/verified`; count unsupported | backlog grows → shift budget to verify pool |
| Completeness | **novelty/discovery curve** + coverage matrix (`required_fields × aspects`) | new aspects still appearing → keep exploring; plateau → toward stop |
| Forward-looking | # OPEN, testable, non-obvious directions | thin → spawn "what's contested / next" directions |
| Faithfulness | checklist of explicit asks with ≥1 grounded claim → fraction | unfilled → target directions at those fields |

Use **countable anchors** (rates, matrix cells, checklist fractions,
novel-aspects-per-round), **not** a repeated LLM 1–5 (which drifts). The design also proposes
an optional **pairwise-temporal** judge ("draft_t vs draft_{t−1}: better? what regressed?").

> **As-built note.** The shipped in-loop instrument is `_measure` (`orchestrator.py:606`),
> which uses `metrics.Snapshot` plus the LLM `judge_coverage` executor (`orchestrator.py:607`)
> for the faithfulness/coverage checklist. The **pairwise-temporal draft judge and the
> `EVALUATE` reflection are not built** — that path is the dead `evaluate` executor
> (`executors.py:307`). The `judge_forward` per-direction judge (`executors.py:292`), meant
> to supply the forward-looking axis, is also dead code. See
> [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) and
> [measure.py](../modules/measure.md) / [metrics.py](../modules/metrics.md).

### 7c. Completeness is special — the denominator problem

Absolute completeness is unmeasurable mid-run (you don't know the universe of relevant
findings).

- **In-loop proxy:** the **discovery/novelty curve** — fraction of each batch's claims that
  introduce a *new* aspect. When it flattens for K checkpoints you've saturated what the
  method can reach (loop-until-dry). This is the single best in-loop completeness signal.
- **Externally-anchored option (recommended):** build a **reference set** `G` = the union of
  grounded findings from the existing agent + baseline reports (9 cancers × 3 modalities × 2
  systems), optionally curated to key papers. Then completeness = **recall against the
  reference set**, computable both in-loop and offline — the one absolute completeness number
  available without a human gold standard.

### 7d. Meta-axis for comparing *methodologies* (not reports)

**Efficiency = quality per dollar.** The whole point is "exhaust the budget *reasonably*," so
the decision metric for v2-vs-v1-vs-baseline is quality-per-dollar, not absolute quality.

### 7e. Formal metrics & equations

**Notation.** Ledger at checkpoint *t*: claims `C_t`; verified `V_t = Conf_t ∪ R_t`
(confirmed ∪ refuted); sourced `Src_t`; with extracted numbers `Num_t`. Aspects `A_t`;
required asks `F`; reference set `G`. Open directions `O_t`; cost spent `κ_t`.

**Correctness** — confirmed counts fully, sourced-but-unverified discounted by β, sourceless = 0:

```
Corr(t) = ( |Conf_t| + β·|Src_t \ V_t| ) / |C_t|              β ≈ 0.5

confab-rate(t)  = |{c∈V_t : cited author/venue ≠ source}| / |V_t|
num-fidelity(t) = |{c∈Num_t∩V_t : numbers(c) ⊆ source-text}| / |Num_t∩V_t|
```

Offline per-report correctness = sample n claims, x faithful, Wilson interval:

```
p̂ = x/n,  CI = [ p̂ + z²/2n ± z·√( p̂(1−p̂)/n + z²/4n² ) ] / (1 + z²/n)
```

**Completeness** — three measures:

```
(a) saturation:  Cov(t) = (1/|A_t|) Σ_{a∈A_t} |{f∈F : filled(a,f)}| / |F|
(b) richness (Chao1, f₁/f₂ = aspects seen in exactly 1 / 2 distinct sources):
      Â∞ = |A_t| + f₁²/(2 f₂)
      Comp_intrinsic(t) = |A_t| / Â∞
(c) reference recall:  Recall_G(t) = |G ∩ covered(t)| / |G|
      novel-beyond-G(t) = |covered(t) \ G|
```

**Forward-looking** (q(d)∈[0,1] = judged testable & non-obvious):

```
Fwd(t) = (1/m) Σ_{d ∈ top-m(O_t)} q(d)
```

**Faithfulness** (hard checklist over the question's asks, optional weights w_f):

```
Faith(t) = Σ_f w_f·1[∃ grounded claim covering f] / Σ_f w_f
```

**Composite** (correctness-gated, so padding can't inflate it):

```
S(t) = Corr(t) · ( ω₁ + ω₂·Comp(t) + ω₃·Fwd(t) + ω₄·Faith(t) ),   Σω = 1
```

**Convergence / stop** — marginal gain per dollar, sustained:

```
Δ_t = ( S(t) − S(t−1) ) / ( κ_t − κ_{t−1} )
STOP ⟺ [ Δ_τ < ε  ∀ τ∈(t−K, t] ] ∧ Faith(t)=1 ∧ |verify-queue|=0   OR  budget exhausted
```

**Direction selection** — EIG core, weighted-sum proxy in practice (see §5).

**Promotion / budget (Hyperband):**

```
promote c → verify  ⟺  conf(c) ≥ τ ∧ evidence(c) ≠ ∅
B_explore = ρ·B,  B_verify = (1−ρ)·B,   ρ ≈ 0.7,   τ set so ≈1/η of claims graduate (η = 3)
```

**Offline composite & efficiency:**

```
Q = Corr · (ω₁ + ω₂·Comp + ω₃·Fwd + ω₄·Faith)
Efficiency = Q / cost_$            # decision metric for v2 vs v1 vs baseline
```

Knobs to calibrate on `genomic_pancreatic`: `β, ω, w_f, ε, K, w₁..₄, τ, ρ, η`. Judged terms
(`q(d)`, pairwise verdicts, `covered(f)`) are LLM calls; only **correctness** must be
source-grounded. See [Config knobs (reference)](../reference/config-reference.md).

---

## 8. Termination

Stop when **budget is exhausted** OR **converged** = (novelty curve flat for K checkpoints)
AND (faithfulness checklist full) AND (verify backlog drained). The orchestrator owning the
loop is what makes "run until genuinely done, up to budget" achievable — fixing finding #4
(the stop-judge couldn't force work; here the loop simply continues by construction).

> **As-built note.** The shipped convergence test (`_checkpoint`, `orchestrator.py:650`)
> requires: `required_fields` non-empty, `coverage ≥ 0.999`, `backlog == 0`, and
> `progress ≤ progress_eps` (`Config.progress_eps = 0.02`, `orchestrator.py:85`). "Progress
> ≈ 0" alone is treated as *shallow* saturation and triggers deeper pattern-driven
> exploration rather than a stop.

---

## 9. How v2 addresses each finding

| Finding | Mechanism in v2 |
|---|---|
| Codex confabulates authors/numbers (#2) | provenance gate (no claim without a resolvable SourceRef) + `VERIFY` extracts exact numbers + final citation sweep |
| Agent leaves surfaced hits unranked (#3) | frontier is explicit ledger state; promotion gate pulls high-value findings into verify+rank |
| Stop-judge can't force work (#4) | harness owns the loop; runs to budget/convergence by construction |
| Plain codex competitive on coverage (#1) | keep codex's coverage as the `EXPLORE` executor; add the structure + verification it lacks |

---

## 10. Implementation plan (as designed)

1. **Harness** = a Workflow-style script: parallel `EXPLORE`/`VERIFY` fan-out, schema'd
   agents, ledger as plain Python (deterministic bookkeeping, no LLM for state).
2. **Calibrate** the promotion threshold, the 70/30 pool split, K, and the `promise` weights
   on **one** task (`genomic_pancreatic`) against the existing agent + baseline reports + the
   reference-set recall.
3. **Score** v2 vs v1-agent vs baseline on the offline rubric (pairwise + source-verified
   correctness + reference-set recall) and on quality-per-dollar.
4. Iterate weights, then run the full 9×3 matrix if v2 wins on quality-per-dollar.

---

## References

1. **Blackboard / bMAS — LLM-Based Multi-Agent Blackboard System for Information Discovery in
   Data Science.** <https://arxiv.org/abs/2510.01285>
2. **Advanced LLM Multi-Agent Systems Based on Blackboard Architecture.**
   <https://arxiv.org/html/2507.01701v1>
3. **LATS — Language Agent Tree Search** (MCTS + LLM + reflection).
   <https://arxiv.org/html/2310.04406v3>
4. **BED-LLM — Bayesian Experimental Design with LLMs** (pick queries by expected information
   gain). <https://arxiv.org/abs/2508.21184>
5. **Reflexion — Language Agents with Verbal Reinforcement Learning** (self-eval as a semantic
   gradient). <https://arxiv.org/pdf/2303.11366>
6. **Deep Research Agents: A Systematic Examination and Roadmap.**
   <https://arxiv.org/html/2506.18096v2>
7. **DeepEvidence — Biomedical Discovery with Deep Knowledge Graph Research** (orchestrator +
   evidence graph + budget state machine). <https://arxiv.org/pdf/2601.11560>
8. **Hyperband — Bandit-Based Configuration Evaluation** (successive halving; escalate budget
   to survivors). <https://openreview.net/pdf?id=ry18Ww5ee>

### Related (optional reading)

- Tree of Thoughts / Graph of Thoughts — search over reasoning steps with a value heuristic.
- Information-Directed Sampling (IDS) — the explore/exploit ratio used in the v1 planner.
- Truth-Maintenance Systems / argumentation frameworks — claim retraction when evidence changes.
