# Methodology (draft)

A generic methodology for **grounded relation prediction from the literature** and
for **evaluating** it. It is written to be task- and domain-agnostic so that
multiple benchmarks (synthetic lethality being the first) plug into the same
framework. Throughout, a *benchmark* supplies (i) a set of query entities,
(ii) a relation of interest, and (iii) a reference set of related entities (the
ground truth, GT) with provenance for each pair.

---

## 1. Task formulation

Given a natural-language question that names a **query entity** `q` and a
**relation** `R`, the system predicts the set of entities `{eᵢ}` that stand in
relation `R` to `q`, returned as a **ranked, confidence-tiered list**, with each
prediction **grounded** in retrievable evidence and resolved to the **identifier
form the question asks for**.

The formulation makes no domain assumptions: `R` may be "synthetically lethal
with," "binds," "regulates," "is a risk factor for," etc. The only domain signal
is the question itself; the engine carries no entity lists, ontologies, or
hand-coded rules.

---

## 2. The research agent

### 2.1 Two-channel retrieval + reading

Retrieval is split into two complementary channels because no single source is
both broad and readable:

- **Discovery channel** — a wide index (web / scholarly search). Maximizes
  *coverage*: surfaces documents an in-house corpus lacks or under-ranks
  (older, cross-domain, long-tail). Returns titles/snippets/identifiers, **not**
  full text.
- **Corpus channel** — a full-text retriever over a readable corpus. Provides
  *grounding*: citeable, line-addressable full text.

The agent uses a **discover→read handoff**: discover candidate documents with the
discovery channel, resolve each to a readable identifier, then fetch full text
from the corpus channel. Documents reachable only via discovery are recorded as
lower-confidence, snippet-only leads.

**Reading is agent-driven.** Fetched documents are staged to disk and mined by the
agent with general-purpose tools (regex/search over the text) rather than a fixed
extraction schema — the agent decides what to read and how. Findings accumulate in
a structured, queryable **notes store**.

### 2.2 Explicit belief state and information-directed planning

The agent maintains two beliefs as an explicit, continuously updated ledger:

- **θ — belief over the answer.** A table of candidate entities *and plausible
  answer-categories* (enumerated up front, before any hits), each annotated with
  the number of independent supporting documents, a confidence, and a status
  (`confirmed` / `tentative` / `open` / `contradicted`). Empty categories are
  visible high-uncertainty gaps.
- **D — belief over methodology.** Which query angles and sources are still
  yielding new documents vs. saturating, and which remain untried.

Action selection is **information-directed** (an IDS/BOED-style trade-off): prefer
the action that best reduces answer-uncertainty per unit of design-redundancy
(broad exploration early, when categories are untouched and source-productivity is
unknown; targeted exploitation as coverage saturates). The belief state is
externalized so the policy is auditable, not hidden in the model's context.

### 2.3 Prediction, not just retrieval

The agent is expected to **infer** candidates, not only to extract stated ones.
Two generic mechanisms:

- **Mechanistic / pattern-based generation.** From what the readable literature
  establishes about `q` (its function, modules, pathways), the agent proposes
  entities that plausibly stand in `R` even absent a paper that states the pair.
- **Resolution to the requested form.** Using the model's own general knowledge,
  the agent expands a group/class/category to its specific members and renders an
  entity named under one convention into the form the question asks for (e.g.
  alias normalization, cross-naming/ortholog mapping). *Identity resolution may use
  prior knowledge; the underlying claim must remain grounded in a finding.*

### 2.4 Confidence tiering

Every prediction carries a **confidence class**, decoupling discovery from
assertion:

- **Class 1 — established / validated:** direct, reproducible evidence; ideally
  orthogonal assays or independent studies.
- **Class 2 — strongly supported / likely:** supported, but with residual
  uncertainty (limited replication, context dependence, missing mechanism).
- **Class 3 — plausible / candidate:** indirect, computational, correlative,
  inferred, or pattern-based — for prioritization, not conclusion.

Resolution- or inference-derived entries are never Class 1. The tiering lets a
single run serve both high-precision use (read the confident tier) and
broad-recall use (read all tiers) without re-running.

### 2.5 Cost control and termination

A **budget** meters spend. The agent stops only when the belief state justifies it
— every plausible category `confirmed` or ruled out, the discovery/corpus channels
saturated, no productive angle left — or the budget is exhausted; not at the first
plausible answer. Budget is a ceiling to be *used* against open categories, not a
target to minimize.

---

## 3. Evaluation methodology

The central evaluation challenge is that **reference sets are incomplete and
provenance-skewed**: a gold standard is assembled from particular evidence
modalities, and some of those modalities are *structurally unreachable* by a
literature agent (entries that live only in supplementary data tables, external
structured datasets, or computational predictions, with no narrated claim). Naive
exact-match overlap therefore conflates **agent quality** with **GT-modality
reachability**, and penalizes correct, well-grounded predictions that are simply
absent from the reference. The methodology below separates these factors.

### 3.1 Provenance stratification of the ground truth

Partition the GT by the **provenance of each pair's supporting evidence**:

- **Narrated** — stated as a focused claim in readable text (the reachable target
  for a literature agent).
- **Tabular / screen-derived** — high-throughput results living in tables or
  supplementary files, not narrated.
- **External / computational** — imported from a separate structured dataset or
  produced by an inference method.

Diagnose provenance from the *source document's characteristics*, not its source
label: e.g., a single source document contributing many pairs indicates a screen
or computational table rather than a narrated finding; verify a sample by checking
where the pair actually appears (body text vs. supplementary vs. absent). Report
metrics **per stratum**; the narrated stratum is the apples-to-apples literature
target. Audit the GT for provenance errors (mis-citations) and exclude them.

### 3.2 Retrieval vs. reasoning decomposition

Score the pipeline in two stages so failures are attributable:

- **Supporting-document recall** — did the agent find (and read) the document(s)
  the GT cites as support? Measures the retrieval/readability subsystem.
- **Answer correctness** — given evidence, are the predicted entities correct?
  Measures extraction + inference.

This isolates retrieval gaps (out-of-corpus, unreadable) from reasoning gaps.

### 3.3 Matching: exact vs. equivalence-class

Exact-identifier matching undercredits predictions that are biologically/semantically
**equivalent** to a GT entry but not identical (a different member of the same
complex/family, a paralog, an ortholog, an alias). Report **both**:

- **Exact** match (strict).
- **Equivalence-class** match — credit a prediction in the same complex / pathway /
  family / ortholog group / alias set as a GT entity, using an external grouping
  resource. This reveals *mechanistic recall* — whether the agent reached the right
  functional neighborhood — which exact matching hides.

### 3.4 Confidence-tier-aware, ranked metrics

Because output is tiered and ranked, evaluate accordingly rather than as a flat set:

- Report precision/recall/AP/hit@k/MRR **at each confidence tier** (e.g.
  Class 1+2 = the confident shortlist; all classes = the broad prioritization list).
- Read **precision at the confident tier** and **recall at the broad tier**; a
  flat score conflates the two and is gameable by list length.

### 3.5 Grounding-quality judgment

To escape GT incompleteness entirely, judge predictions on **grounding** rather
than membership: an automated (or expert) judge checks whether each prediction is
supported by **real, cited evidence for a genuine instance of `R`**, independent of
whether the reference set happens to list it. This rewards being *correct and
grounded*, and credits novel-but-true predictions a static GT would mark wrong.
Use it alongside, not instead of, overlap metrics.

### 3.6 Baselines and cost normalization

Report against:

- a **parametric baseline** (LLM answering from memory, no retrieval) — the floor
  for "what's already memorized";
- a **grounded baseline** (retrieval-augmented but without the full agent loop).

Always report **cost per query** and compare **cost-normalized** — a cheap
parametric model casting a wide net can win raw recall while losing precision,
ranking, and grounding; the comparison is meaningful only at matched cost or with
cost reported.

### 3.7 Leakage control for structured-data access

If the agent is granted a **structured-data channel** (to reach tabular/external
GT modalities), guard against **circularity**: when the reference set is itself
derived from that data, access turns prediction into lookup and inflates the score.
Enforce independence via **held-out or cross-source splits** — evaluate on pairs
whose provenance is *disjoint* from the data the agent can query (e.g. give
modality X, test on pairs supported only by modality Y).

### 3.8 Variance and reproducibility

Agent runs are stochastic. Report **variance across repeats**, fix seeds and model
versions where possible, and persist per-run artifacts (belief-state ledger,
fetched documents, notes, final tiered list) so a score is traceable to its run.

---

## 4. Summary of the framework

A run produces a **ranked, confidence-tiered, grounded** candidate list from a
domain-agnostic agent that plans over an explicit answer/methodology belief state
and both retrieves and reasons. It is evaluated under a battery that **stratifies
the reference by reachable provenance**, **separates retrieval from reasoning**,
**credits functional equivalence**, **scores per confidence tier at matched cost**,
and — to bound GT incompleteness — **judges grounding directly**, with leakage
controls whenever structured data is in play. New benchmarks instantiate the task
triple (queries, relation, provenance-tagged GT) and inherit the rest.
