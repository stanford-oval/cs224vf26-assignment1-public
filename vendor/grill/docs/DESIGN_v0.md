# graph-search — v0 design

Status: locked for first implementation pass · 2026-05-11
Scope: enough decisions to start building the planner + node + synthesizer
loop. Schema is fixed; prompts and concurrency knobs are tunable inside the
locked shape.

This doc is the audit trail. Each section names the **decision**, the
**alternatives** considered, **why** the chosen option won under the
"principled / robust / quality / generalises" lens, and the **revisit
trigger** that should pull it back open.

---

## 0. Goals (the lens every decision is judged against)

1. **Principled** — every behavior should have a defensible reason, not
   "because the planner felt like it." Heuristics over vibes.
2. **Robust** — failures of individual nodes / agents / paperclip calls
   must not corrupt the investigation. Restartable, idempotent, durable.
3. **Quality** — conclusions must be evidence-grounded (every claim cites
   a paper + line range), contradictions must be visible, duplication must
   be deduped.
4. **Generalises** — the system should work on any research question, not
   just hand-tuned PubMed topics. Source filters and decomposition depth
   are per-investigation knobs, not constants in the prompt.

---

## 1. Architecture (the unchanging skeleton)

Three agent roles, three node kinds, one shard queue.

- **Planner agent** — codex shard with the `planner` prompt. Runs once
  per round. Reads a compact graph view from SQLite, emits next-round node
  specs (expand / synthesize / done).
- **Node agent (expand)** — codex shard with the `expand` prompt. Fresh
  context. Receives a `NodeBrief`, runs `paperclip` searches itself, fills
  in a structured `NodeConclusion`.
- **Node agent (synthesize)** — codex shard with the `synthesize` prompt.
  Fresh context. Reads K child conclusions from SQLite (no paperclip),
  emits one merged `NodeConclusion` whose body covers the children.
- **Decomposer (round 0 only)** — codex shard with the `decompose`
  prompt. Takes the root question, emits the first batch of expand nodes.

Storage is SQLite (WAL + `BEGIN IMMEDIATE`) following the `papers_search`
pattern. Codex is the agent harness; `paperclip` is the search tool inside
the codex sandbox.

```
artifacts/graph_search/
  database.sqlite
  investigations/<inv_id>/
    nodes/<node_id>/
      brief.json          # what we sent codex
      prompt.txt          # frozen full prompt
      transcript.log      # codex stdout/stderr
      conclusion.json     # validated NodeConclusion
      error.txt           # on failure
    planning/round_<n>/
      input.json          # graph view shown to planner
      output.json         # next-round node specs
      transcript.log
```

---

## 2. Decisions

### 2.1 Planner type — LLM agent (codex shard)

**Chosen.** The planner is a codex shard, invoked once per round, with a
prompt that reads the graph view JSON and emits next-round node specs.

**Alternatives rejected**
- Deterministic policy (BFS by hypothesis priority score). Cheaper, more
  debuggable, but rigid — couldn't form novel cross-cutting hypotheses
  that don't already exist in the graph.
- Hybrid (deterministic candidate generation + LLM ranking). Defensible
  but two systems to maintain for v0.

**Why this wins**
- The whole point of long-horizon expansion is non-trivial hypothesis
  formation; that's an LLM strength.
- Codex already gives us the auth / sandbox / cost telemetry plumbing.

**Revisit if**
- Planner cost dominates the budget (>30% of total) and we can't shrink
  the graph view.
- Planner output quality degrades on graphs >100 nodes (it should, since
  context grows; see §2.7 for the mitigation).

---

### 2.2 Node harness — codex (matches `papers_search`)

**Chosen.** Every node runs as a codex shard with `paperclip` available in
the sandbox, mirroring the `papers_search` pattern exactly. Reuse the
shard queue, worker pool, cost telemetry, paperclip-auth guards.

**Alternatives rejected**
- Direct Claude API / Agent SDK orchestration. Tighter control over briefs
  and output schema enforcement, but the team has no Claude credits and we
  lose the proven `papers_search` plumbing.
- Pure Python wrapper around `paperclip` (the `PaperclipClient` we already
  built). Works for one-shot search, but a node agent needs to *iterate*
  (search → read → re-search) and we don't want to build a mini-agent loop.

**Why this wins**
- Re-uses a known-working harness. Lowest implementation risk.
- Codex sandbox already solves the paperclip-auth bind-mount problem.

**Revisit if**
- Codex's output-schema discipline turns out to be a recurring failure
  mode (>10% of nodes need re-runs because JSON is malformed).
- We get Claude credits and want the structured-output tooling.

---

### 2.3 Node kinds — three: `decompose`, `expand`, `synthesize`

**Chosen.** Three kinds, three prompt templates, one shard table.

**Alternatives rejected**
- Two kinds (`expand`, `synthesize`). Simpler, but conflating "first-pass
  root decomposition" with "given a graph, what should we expand" forces
  the planner prompt to handle an empty-graph special case, which makes it
  worse at the normal case.
- Five kinds (add `verify`, `replicate`). Premature — until we hit a real
  case where expand-with-contradiction-bias underperforms a dedicated
  verify prompt, two extra prompts is dead code.

**Why this wins**
- Decomposition is a genuinely different cognitive task (split → cover →
  parallelize) than expansion (graph-aware exploration). Cleaner prompts.
- Synthesize is structurally different (no paperclip, just merge).

**Revisit if**
- We notice the planner consistently failing to spawn verification of a
  contradicted claim, or refuting evidence. Add a `verify` kind.

---

### 2.4 Brief assembly — templated by the harness

**Chosen.** When the planner emits a node spec, the harness assembles the
`NodeBrief` deterministically from SQLite:

- root question (always)
- ancestor chain summaries (parent → grandparent → ..., each as the
  parent's `conclusion.summary`, capped at depth 3)
- topically-relevant sibling conclusions (siblings whose hypotheses
  overlap with this node's question by ≥1 hypothesis_id)
- the node's `question` and `rationale` (from planner output)
- the `NodeConclusion` JSON schema the node MUST fill
- source filter + budget caps inherited from the investigation

**Alternatives rejected**
- Planner-authored briefs (planner writes the brief per child node).
  Compresses better but doubles planner cost, and "why didn't this node
  know about X" becomes a planner-bug diagnosis instead of a SQL query.
- Hybrid (templated + optional `focus_note` from planner). Solid v1 idea,
  but added complexity without proven need.

**Why this wins**
- Deterministic. Same graph state → same brief. Reproducible.
- The relevance filter (hypothesis overlap) is explicit code we can
  improve independently.
- Cheapest at scale — planner only writes node specs, not whole briefs.

**Revisit if**
- Sibling-relevance filter misses obvious context (false negatives) AND
  expanding to "all siblings" blows context budgets.

---

### 2.5 Synthesizer trigger — planner-driven with safety floor

**Chosen.** The planner emits `synthesize` ops in its round output
alongside `expand` ops. The harness adds one safety rule: if any
`hypothesis` has ≥5 supporting nodes and no `synthesize` node yet covering
them, the harness force-spawns one before the next planner round.

**Alternatives rejected**
- Pure heuristic (every K nodes). Predictable but spawns useless
  synthesizers when nothing has converged.
- Pure planner-driven (no safety floor). Risks unbounded growth if the
  planner forgets — and "agents forget" is the default assumption.
- Periodic (every N rounds unconditionally). Wasteful on early rounds,
  insufficient on late ones.

**Why this wins**
- Planner has the most context to know what's worth synthesising.
- Safety floor bounds the worst case without removing planner agency.

**Revisit if**
- The safety floor fires more than the planner-driven path does (means
  the planner isn't using its agency).

---

### 2.6 Convergence rule — multi-signal, no human-in-loop

**Chosen.** Stop the investigation when **any** of:

1. `budget_usd_consumed >= investigation.budget_usd`
2. `current_round >= max_rounds` (default 8, configurable)
3. Planner emits `{"action": "done", "reason": "..."}`
4. 2 consecutive rounds where: no new hypotheses were created AND no
   `open_question` was newly answered (i.e., the graph is stalled)
5. Frontier empty: every node `done`, no `open_questions` remaining

The investigation row records which trigger fired.

**Alternatives rejected**
- Single signal (e.g., budget only). Misses early-finish cases and
  hides stalled investigations.
- Human checkpoint every N rounds. User said no for POC.
- "Planner says done" only. Planners under-stop in practice.

**Why this wins**
- Robust to any single failure mode (planner won't stop, budget
  miscounted, stalled but in-budget).

**Revisit if**
- We see investigations consistently stopping on the same trigger and
  producing low-quality output (means the others aren't pulling weight).

---

### 2.7 Planner context bounding — collapse synthesized subgraphs

**Chosen.** The "graph view" handed to the planner each round is:

- root question
- all open hypotheses (table is small in practice; cap at top 50 by
  support_count)
- recent contradictions (last 20)
- **frontier leaves** — nodes that are `done` but whose `open_questions`
  or `proposed_hypotheses` haven't been expanded yet, AND that aren't
  covered by a `synthesize` node
- **synthesis rollups** — for any subgraph with a `synthesize` node, the
  view shows only the synthesis conclusion. The children are hidden.

If the assembled view exceeds a token threshold (default 60k input
tokens), force a global meta-synthesis: a synthesize node whose parents
are all currently-visible frontier leaves. Next round, the planner sees
just that meta-rollup + new frontier.

**Alternatives rejected**
- Show everything. Doesn't scale past ~30-50 nodes.
- Fixed K most-recent nodes. Loses old contradictions, misses
  cross-cutting patterns.
- Embed-and-retrieve over conclusions. Defensible but adds an embedding
  store dep for marginal gain over rollups.

**Why this wins**
- Depth and breadth can grow unbounded; planner view stays bounded.
- Mechanism is the same as user-facing synthesis — no separate machinery.

**Revisit if**
- Meta-synthesis fires more than once per investigation in normal use
  (means rollups aren't reducing the view enough).

---

### 2.8 Source defaults — per-investigation set, default PMC + abstracts

**Chosen.** Each `investigation` row has a `sources` column (JSON array
from {pmc, biorxiv, medrxiv, arxiv, abstracts}). Default `["pmc",
"abstracts"]` since the user explicitly framed this as PubMed-focused.
The expand-node prompt receives the source set and picks among them per
query.

**Alternatives rejected**
- Constant default (all sources). Wastes searches on irrelevant corpora
  for many investigations.
- All-source default with planner-side filtering. Doubles paperclip cost
  for no gain.

**Why this wins**
- One knob captures "what kind of investigation is this" without
  bloating per-node logic.
- Generalises: a methods investigation can flip to bioRxiv+arxiv at
  creation time, no code change.

**Revisit if**
- Per-query source decisions inside the expand prompt routinely override
  the investigation default (means we should expose it at finer grain).

---

### 2.9 Round 0 — dedicated `decompose` shard

**Chosen.** Investigation creation enqueues exactly one `decompose` shard
with the root question. Its output is a list of expand-node specs (3-8
sub-questions) which become round 1.

**Alternatives rejected**
- Same planner with empty-graph special case. Mixes two cognitive tasks
  in one prompt; degrades both.
- User supplies first nodes. Ruled out by no-human-in-loop.

**Why this wins**
- Question decomposition has well-understood criteria (sub-questions
  should be independent, jointly cover the root, individually answerable
  from literature). A focused prompt nails this; a generalist planner
  prompt has to learn it from few-shot examples.

**Revisit if**
- We discover the decomposer's sub-questions are systematically wrong in
  the same way (suggests prompt refactor, not architecture change).

---

### 2.10 Hypothesis dedup — at node-merge time, by small-model classifier

**Chosen.** When a node's `conclusion.json` is merged, the harness
extracts `proposed_hypotheses`. For each one, it runs a small-model LLM
classifier against the existing `hypotheses` table:

- If matches existing hypothesis → insert into `hypothesis_support`
  with stance ∈ {supports, contradicts, refines}.
- If novel → insert new `hypotheses` row, then add support.

Small model = `gpt-4o-mini` (or the cheapest credible classifier
available). The classifier sees: candidate statement + the K most
embedding-similar existing statements (use a tiny SQLite-FTS index over
statements for retrieval, no separate vector store).

**Alternatives rejected**
- Planner does it at round boundaries. Adds latency, and the planner sees
  stale hypothesis table within a round.
- No dedup, let it sprawl. Then "X causes Y" appears 5 times with no
  cross-support tracking — defeats the point of the hypothesis table.
- Embedding-only dedup. Cheap but conflates "related" with "equivalent".

**Why this wins**
- Dedup happens immediately, so the planner's next round sees a clean
  table.
- Small model is fine for the binary "is this the same hypothesis"
  judgment; we don't need the planner-grade model.

**Revisit if**
- Classifier false-merge rate exceeds ~5% (we lose distinct claims) or
  false-novel rate creates obvious dups.

---

### 2.11 NodeConclusion schema (the contract every node MUST fill)

**Chosen.**

```json
{
  "summary": "2-3 sentence answer to the node's question.",
  "key_findings": [
    {
      "statement": "concrete finding",
      "citations": [
        {"paper_id": "PMC12345", "claim": "exact claim", "lines": "L42-L58"}
      ]
    }
  ],
  "open_questions": ["unresolved sub-question 1", "..."],
  "proposed_hypotheses": [
    {
      "statement": "X causes Y",
      "stance_evidence": "supports|contradicts|partial",
      "supporting_paper_ids": ["PMC12345"],
      "confidence": "low|medium|high"
    }
  ],
  "contradicts_node_ids": [],
  "confidence": "low|medium|high",
  "notes": "free text; only used for human review, never read by other agents"
}
```

Validated with Pydantic on merge. Malformed → node marked `failed`,
shard goes to retry queue (one retry; second failure stays failed).

**Why this wins**
- Every consumer downstream (planner, synthesizer, hypothesis dedup) has
  a fixed contract. No string-parsing of free-form prose.
- Citations include line ranges so the `citations.gxl.ai` URL is
  reconstructible; quality is verifiable.

**Revisit if**
- We need more structured fields for a specific node kind (e.g., a
  `methods_comparison` kind would want a table).

---

### 2.12 Concurrency — 4 parallel node shards default

**Chosen.** Default worker pool = 4 codex shards in parallel. Configurable
per `shards run`. Planner and decomposer run single-threaded between
rounds.

**Alternatives rejected**
- Single shard at a time. Too slow for iteration.
- 8+ default. `papers_search` README warns codex is CPU-heavy (~1 core
  per shard); 4 is the conservative sweet spot.

**Why this wins**
- Matches the proven sweet spot in `papers_search`.
- Round-based gating (next round waits for all current shards) keeps
  reasoning about cost and convergence trivial.

**Revisit if**
- We move off codex (e.g., to Claude API) and the per-shard cost profile
  changes.

---

### 2.13 Models — `gpt-5.5` everywhere except hypothesis dedup

**Chosen.**
- decomposer, planner, expand, synthesize: `gpt-5.5`
- hypothesis dedup classifier: `gpt-4o-mini`

**Alternatives rejected**
- Cheaper model on expand. Tested in `papers_search` to be a quality
  cliff for paper-reading tasks.
- One model for everything. Wastes money on the dedup classifier.

**Revisit if**
- Budget pressure forces a cheaper expand model — first try splitting
  expand into "exploratory" (cheap) and "depth" (strong) kinds.

---

### 2.14 Storage — SQLite, WAL, per-thread connections

**Chosen.** SQLite at `artifacts/graph_search/database.sqlite`, WAL
journal mode, `BEGIN IMMEDIATE` per write, one connection per worker
thread. Identical to `papers_search`.

**Alternatives rejected**
- JSON-per-node file tree. Easy to inspect, hard to query
  ("all nodes touching hypothesis H?" requires walking the tree).
- Postgres / managed DB. Overkill for POC, adds infra.

**Why this wins**
- Cross-cutting queries are exactly what the planner view needs.
- WAL + BEGIN IMMEDIATE handles our concurrency model without `flock`.

---

### 2.15 Search infra (the existing `PaperclipClient`) — kept as side tools

**Status.** The Python wrapper built in the previous slice is not in the
hot path (node agents call paperclip directly via the codex sandbox). It
stays useful for:

- Pre-flight smoke checks before launching an investigation.
- Planner-side meta queries ("how many results does query X return?" to
  gate whether to spawn a node).
- Tests.

No deprecation; just narrower scope than originally framed.

---

## 3. SQLite schema (concrete)

```sql
investigations(
  id TEXT PRIMARY KEY,
  root_question TEXT NOT NULL,
  sources TEXT NOT NULL,                -- JSON array
  status TEXT NOT NULL,                 -- pending|running|done|failed|stalled
  stop_reason TEXT,                     -- which convergence trigger fired
  current_round INTEGER NOT NULL DEFAULT 0,
  max_rounds INTEGER NOT NULL DEFAULT 8,
  budget_usd REAL NOT NULL,
  cost_usd REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  finished_at TEXT
);

nodes(
  id TEXT PRIMARY KEY,
  investigation_id TEXT NOT NULL REFERENCES investigations(id),
  round INTEGER NOT NULL,
  kind TEXT NOT NULL,                   -- decompose|expand|synthesize
  question TEXT NOT NULL,
  rationale TEXT NOT NULL,
  status TEXT NOT NULL,                 -- pending|running|done|failed
  model TEXT,
  cost_usd REAL DEFAULT 0,
  created_at TEXT NOT NULL,
  finished_at TEXT
);

node_parents(node_id, parent_id, PRIMARY KEY(node_id, parent_id));
-- 1 parent for expand; many for synthesize.

node_searches(
  id INTEGER PRIMARY KEY,
  node_id TEXT NOT NULL REFERENCES nodes(id),
  paperclip_search_id TEXT NOT NULL,
  query TEXT NOT NULL,
  source TEXT,
  filters TEXT,                         -- JSON
  n_results INTEGER
);

papers(
  id TEXT PRIMARY KEY,                  -- paperclip doc id
  title TEXT, authors TEXT, source TEXT,
  doi TEXT, abstract TEXT, date TEXT, url TEXT
);

node_papers(node_id, paper_id, PRIMARY KEY(node_id, paper_id));

node_conclusions(
  node_id TEXT PRIMARY KEY REFERENCES nodes(id),
  summary TEXT NOT NULL,
  key_findings TEXT NOT NULL,           -- JSON
  open_questions TEXT NOT NULL,         -- JSON array
  confidence TEXT NOT NULL,
  notes TEXT
);

node_citations(
  id INTEGER PRIMARY KEY,
  node_id TEXT NOT NULL REFERENCES nodes(id),
  paper_id TEXT NOT NULL REFERENCES papers(id),
  claim TEXT NOT NULL,
  lines TEXT                            -- e.g. "L42-L58"
);

node_contradicts(node_id, contradicts_node_id, PRIMARY KEY(node_id, contradicts_node_id));

hypotheses(
  id TEXT PRIMARY KEY,
  statement TEXT NOT NULL,
  status TEXT NOT NULL,                 -- open|supported|contradicted|resolved
  created_at TEXT NOT NULL
);

hypothesis_support(
  hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
  node_id TEXT NOT NULL REFERENCES nodes(id),
  stance TEXT NOT NULL,                 -- supports|contradicts|refines
  confidence TEXT NOT NULL,
  PRIMARY KEY(hypothesis_id, node_id)
);

planning_rounds(
  investigation_id TEXT NOT NULL REFERENCES investigations(id),
  round INTEGER NOT NULL,
  planner_node_id TEXT,                 -- the shard that did the planning
  input_view TEXT,                      -- JSON the planner saw (path to file)
  decision TEXT,                        -- JSON the planner emitted
  PRIMARY KEY(investigation_id, round)
);
```

Indexes to add at build time:
- `nodes(investigation_id, round, status)`
- `node_papers(paper_id)` for "all nodes citing paper X"
- `hypothesis_support(hypothesis_id)` and `hypothesis_support(node_id)`
- FTS5 virtual table over `hypotheses.statement` for dedup retrieval.

---

## 4. Known gaps / open questions for after v0 ships

These are conscious deferrals — we'll learn more from a run than from
arguing them now.

- **Cross-investigation memory.** v0 has no shared paper / hypothesis
  cache across investigations. Adding it later means an additional
  `global_papers` / `global_hypotheses` layer with provenance — defer.
- **Image / figure analysis.** Paperclip's `ask-image` is available
  inside the codex sandbox; expand prompt doesn't require it in v0.
- **Hypothesis lifecycle (resolved / archived).** Hypotheses are
  created and accumulate support; v0 doesn't actively "close" them. The
  planner's `done` action implicitly handles this. Revisit if hypothesis
  count drifts unbounded.
- **Verify kind.** Listed under §2.3 as a v1 candidate; trigger is
  "planner repeatedly fails to challenge a low-evidence hypothesis."
- **Brief focus_note from planner.** Listed under §2.4 as the natural
  v1 evolution; trigger is "templated brief consistently loses critical
  cross-cutting context."
- **Resumability across crashes.** Codex shards are atomic; SQLite has
  WAL. A `shards reset` flips orphaned `running` rows to `pending`,
  matching `papers_search`. Should work for free; verify in first run.

---

## 5. Build order (the next implementation slice)

1. SQLite schema + migrations module + Pydantic models for
   `Investigation`, `Node`, `NodeBrief`, `NodeConclusion`, `Hypothesis`.
2. Codex runner reused from `papers_search` (or copied minimally).
3. Decompose prompt + shard kind, end-to-end on a real PubMed question.
4. Expand prompt + shard kind. Brief assembler. Conclusion validator
   + merger. Hypothesis dedup classifier.
5. Planner prompt + graph view assembler. Round loop. Convergence
   triggers.
6. Synthesize prompt + safety floor.
7. CLI: `graph-search investigate "<question>" --budget-usd 20`.
8. Report renderer (markdown of the final graph + cited claims).

Stop after each step; verify with a real investigation.
