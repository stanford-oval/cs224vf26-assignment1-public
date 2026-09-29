---
marp: true
theme: default
paginate: true
size: 16:9
---

# Calibrated Evidence-Grounded Advisor for Literature-Research Agents

A plan for a domain-pretrained surprisal/EIG advisor that steers a frozen frontier reasoner.

Draft — research plan

---

## The problem

- The frontier agent reasons well, but its **own uncertainty isn't calibrated** to the task — at SMC3 it stopped at $2.30 with the wrong belief; only forcing explicit θ/D ledgers pushed it to keep going.
- The closest prior work (Hu et al., ICML'26) computes EIG from the **frontier model's own semantic entropy** — which the frontier can satisfy by **self-soothing** (confidence-collapse failure mode).
- Frontier models are closed / expensive to RL-train; calibration drifts every release; we don't want to lose their reasoning power.
- We want an **external, lightweight, calibrated** uncertainty signal the planner can trust — without retraining the frontier.

---

## What's already taken (honestly)

- **Search-R1, R1-Searcher** (2025) — RL-trained search agents; **outcome reward only**.
- **Hu et al., ICML'26** — *Optimizing Agentic Reasoning … via Synthetic Semantic Information Gain Reward.* Closest to "your idea v1" — RL on frontier's own semantic entropy.
- **Asawa et al., 2025** — *How to Train Your Advisor.* Small advisor steering a frozen frontier; **outcome-supervised**.
- **PRMs, semantic entropy (Farquhar 2024), FLARE** — calibration / uncertainty pieces, none assembled this way.

→ The advisor template is taken. Semantic-entropy RL is taken. What isn't: **the advisor's objective.**

---

## The proposal — Option 2: Evidence-grounded entropy advisor

A small advisor `A` estimates, given `(question, evidence-so-far)`:

- **`H_evidence(θ | q, E_t)`** — how much the evidence determines the answer, *not* how confident the frontier feels.
- **`EIG(a) = H_evidence(θ | E_t) − E[H_evidence(θ | E_t ∪ obs(a))]`** for each candidate next action.

Planner picks actions to maximize **EIG / cost**. Frontier still reasons and writes — `A` only scores.

**Why evidence-grounded:**

- Model-agnostic — calibrated to the *evidence*, not a particular frontier.
- Sidesteps the chicken-and-egg of "calibrate `A` to `F`'s subjective entropy."
- Breaks the confidence-collapse mode: `F` can't self-soothe an evidence-grounded entropy.

---

## Architecture — where the advisor plugs in

```
   q ──▶ ┌───────────┐    candidate    ┌────────────────┐
        │  Frontier  │── actions ────▶ │  Advisor A     │
        │  (frozen)  │ ◀── EIG / cost ─│  (small;       │
        └─────┬──────┘                 │  pretrained on │
              │ pick top                │  the domain)   │
              ▼                         └────────────────┘
       reasoning, notes,
       extraction, synthesis
```

- Frontier `F` keeps reasoning + final synthesis (no fine-tune).
- Advisor `A` exposes a scalar EIG + a distribution over candidate answers.
- Plugs in front of any tool-using agent.

---

## Defining θ — a structured candidate space

We don't measure entropy over free text (noisy, surface-form confounded).
We measure it over a **structured candidate space**:

- For our task: `θ` = top-K list of `{entity, confidence class}` drawn from a domain vocabulary `V` (HGNC human gene symbols).
- `A` outputs a distribution over `V`; entropy is computed exactly.
- **Sharp, comparable across states, independent of `F`'s sampling.**

Open-vocabulary tasks fall back to semantic clustering (Hu et al.'s issue) — first target domains have an enumerable `V`.

---

## Training data — corpus + state distribution

Two things to assemble:

- **Domain corpus `C`** — full-text papers in the target domain.
- **State distribution `(q, E_t)`** — what the agent really encounters mid-run:
  - **Synthetic states:** mask supporting passages of `(q, θ*, E_full)` triples extracted from papers.
  - **Bootstrap from trajectories:** snapshot real agent runs on a held-out gene set.

State distribution must include **ratty mid-trajectory states**, not just clean queries — else `A` is off-distribution at deployment.

---

## Supervision — three label-free signals

| | A: masked-evidence reveal | B: ensemble disagreement | C: held-out gold |
|---|---|---|---|
| **Target** | Reference predictor's distribution over θ given **full** evidence `E_full` | Entropy of K independent strong open LLMs' clustered answers on `(q, E_t)` | Dirichlet over true/false given known answers |
| **Pros** | Scalable, no outcome labels | Independence breaks self-soothing | Sharp, well-defined |
| **Cons** | Reference smuggles in its biases | K models, cost | Only where GT is clean |

Train `A` against the **distribution** (KL), not the scalar entropy. Mix as `α·A + β·B + γ·C`; ablate.

---

## The EIG head

`A` learns two outputs from `(q, E_t)`:

1. **Posterior distribution** over θ → gives `H(θ | E_t)` exactly.
2. **EIG head:** given a hypothetical observation `obs(a)`, predict `E[H(θ | E_t ∪ obs(a))]`.

EIG-head supervision falls out of the masked-reveal data:
adding the masked passage back **is** an observation — before/after entropies for free.

This is what makes the planner **forward-looking**, not just reactive.

---

## Ablations — what would convince us

Hold frontier + agent loop fixed; vary only the entropy signal:

1. **No advisor** (current θ/D ledger heuristic).
2. **`F`'s own semantic entropy** (Hu et al. reproduction).
3. **`A` on Signal A only** (corpus self-study — *the thesis*).
4. **`A` on Signal B only**.
5. **`A` on A + B + C**.
6. **Outcome-trained advisor of equal size** (Asawa baseline).

**The claim:** **3 beats 1 and 2, and matches 6 — without using outcome labels.**

---

## Metrics

Per ablation:

- **Task quality** (against narrated GT subset):
  precision at confident tier, recall at broad tier, AP.
- **Trajectory efficiency:**
  information gained per dollar; dead-end searches; cost-normalized score.
- **Calibration check:**
  does `A`'s predicted EIG correlate with the **realized** entropy drop on held-out evidence?

A working advisor must show **task improvement** *and* **calibration**.

---

## Honest risks

1. **Bootstrapping circularity** — Signal A's reference predictor is itself an LLM; if same family as `F`, biases leak in. *Mitigation:* independent family; test under reference swap.
2. **`V` must be enumerable** — entropy needs a defined candidate space. Clean for "human genes"; harder for open-text answers. Fallback: clustered semantic entropy.
3. **Off-distribution drift** — agent reads cross-domain papers mid-run; `A`'s calibration degrades. *Mitigation:* training distribution must include real agent-trajectory states.

---

## Minimal first experiment

- **Domain:** human SL (we already have SynLethDB + a characterized narrative subset).
- **`V`:** HGNC human gene symbols.
- **Advisor:** 8B open model — distribution head over `V` + EIG head.
- **Training:** **Signal A only** — masked reveal over ~50 narrated SL papers; ~5k synthetic states + ~100 bootstrap trajectories.
- **Test:** SMC3 + 1–2 other narrative-heavy genes. Does advised proto2 beat unadvised at **lower** budget?

**Stop conditions:** if (i) no task gain at matched budget, or (ii) predicted EIG doesn't correlate with realized drop — calibration thesis is weak; iterate or pivot.

---

## What we'd need to decide

- **Frontier model** to lock for the experiment.
- **Reference predictor** for Signal A — independent family (Claude Sonnet / Llama / Qwen)?
- **Stick to enumerable `V`** for v1 (HGNC), or invest in clustering fallback up front?
- **Build budget:** ~K frontier samples for Signal A targets + advisor pretraining compute.
- **Asawa baseline:** confirm equal-size, equal-data outcome-trained advisor is the fair comparison.

---

## Summary

- Frontier model keeps reasoning — we don't retrain it.
- A small advisor predicts **evidence-grounded** entropy + EIG, **not** the frontier's subjective uncertainty.
- Trained without outcome labels via masked-evidence reveal on a domain corpus.
- Plugs in front of any tool-using agent; planner consumes EIG / cost.
- Differentiates from **Hu et al.** (frontier-subjective entropy) and **Asawa et al.** (outcome-trained advisor) on **what** is calibrated and **how** it's trained.

The defensible contribution is the **objective**, not the architecture.
