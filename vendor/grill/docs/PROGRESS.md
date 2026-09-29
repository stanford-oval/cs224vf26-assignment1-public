# graph-search — progress

Living doc. Updated at the end of every slice. The DESIGN doc
(`DESIGN_v0.md`) holds the *plan*; this doc holds the *state*.

A fresh agent should be able to read this top-to-bottom and know exactly
where to pick up.

---

## Status snapshot

| Slice | Status | Verified |
|------|--------|----------|
| 0. Search infra (`PaperclipClient`) | done | live PMC + bioRxiv + abstracts smoke tests |
| 1. SQLite schema + Pydantic models + store | done | 11 unit tests + `db init` CLI |
| 2. Decomposer codex shard | done | 5 unit tests + live decompose → 5 sub-questions |
| 3. Expand-node shard + brief assembler + conclusion merge | done | 9 unit tests + live drain → 31 papers, 74 citations, 0 orphans |
| 4. Hypothesis dedup classifier + backfill | done | 7 unit tests + live backfill → 13 → 7 deduped |
| 5. Planner shard + round loop + graph view | done | 11 unit tests + live plan → 6 high-quality round-2 expand specs |
| 6. Synthesize + safety floor + meta-synth | done | 9 unit tests + live force-spawn → 4-parent merge, 6 findings, 27 citations, frontier collapsed 5→1 |
| 7. CLI: `graph-search investigate "<question>"` (full loop) | not started | — |
| 8. Final-report renderer | not started | — |

Build order is from `DESIGN_v0.md` §5.

---

## What's on disk

```
graph-search/
  pyproject.toml                       — deps: pydantic, click, openai
  uv.lock
  README.md
  docs/
    DESIGN_v0.md                       — locked v0 architecture + decision log
    PROGRESS.md                        — this file
  src/graph_search/
    __init__.py                        — re-exports public types
    models.py                          — all Pydantic models (wire + domain + brief + planner)
    paperclip_client.py                — subprocess wrapper for `paperclip`
    database.py                        — connect / init_schema / writer_transaction
    store.py                           — CRUD (incl. reset_node_to_pending)
    codex_runner.py                    — codex exec wrapper, paperclip credential redirect
    decomposer.py                      — round-0 orchestration
    briefs.py                          — assemble_brief(node_id) → NodeBrief (handles synth kind)
    expand.py                          — claim + run + persist; merge_proposed_hypotheses
    hypothesis_dedup.py                — classify(candidate, existing) → DedupResult
    hypotheses_backfill.py             — re-merge from on-disk expand_output.json
    planner.py                         — view, run_planning_round, safety floor, meta-synth, run_one_step
    synthesize.py                      — claim + run + persist for kind='synthesize'
    cli.py                             — search, db init, decompose, expand, hypotheses, plan, step, synthesize
    sql/schema.sql                     — DDL (schema_version 1)
    prompts/
      decompose.md
      expand.md
      plan.md (updated for synthesize specs)
      synthesize.md
  tests/
    test_parsing.py                    — paperclip CSV parser
    test_store.py                      — schema + CRUD round-trips (incl. reset)
    test_decomposer.py                 — orchestration with fake codex
    test_briefs.py                     — round-1 vs round-2 brief assembly
    test_expand.py                     — expand orchestration with fake codex
    test_hypothesis_dedup.py           — dedup with fake classify_fn
    test_planner.py                    — view + orchestration + meta-synth
    test_synthesize.py                 — brief, happy path, reductive guards, safety floor
artifacts/graph_search/                 — created at run time
  database.sqlite
  investigations/<inv>/nodes/<n>/
    brief.json | view.json
    prompt.txt, transcript.log
    decompose_output.json | expand_output.json | plan_output.json | synthesize_output.json
    .paperclip_cfg/credentials.json    — per-shard writable copy
    error.txt | dedup_error.txt        — only on failure
```

### Imports the rest of the code depends on

- `from graph_search.database import connect, writer_transaction, now_iso`
- `from graph_search import store`
- `from graph_search.models import Investigation, Node, NodeBrief, NodeConclusion, PlannerView, SynthParentConclusion, ...`
- `from graph_search.codex_runner import CodexInvocation, run as run_codex, DEFAULT_MODEL`
- `from graph_search.briefs import assemble_brief, BriefError`
- `from graph_search import decomposer, expand, hypothesis_dedup, hypotheses_backfill, planner, synthesize`
- `from graph_search import PaperclipClient`

---

## What's been verified end-to-end

- **Live paperclip searches** for `pmc`, `biorxiv`, `abstracts`.
- **Schema init + idempotence** via `graph-search db init`.
- **CRUD round-trips** (9 unit tests).
- **Decomposer orchestration** (5 unit tests).
- **Live decompose** → 5 sub-questions for the GLP-1/MACE question.
- **Brief assembler** (3 unit tests; round-1 and round-2 cases).
- **Expand orchestration** (6 unit tests).
- **Live drain** → 5/5 done, 31 papers, 74 citations, 0 orphans.
- **Hypothesis dedup** (7 unit tests + live backfill: 13 → 7 deduped).
- **Planner view + orchestration** (11 unit tests; mixed expand/synth
  decisions accepted; bogus parents rejected).
- **Live planning round** → 6 round-2 expand specs targeting open
  questions and weakly-supported hypotheses.
- **Synthesize orchestration** (5 unit tests with fake codex): brief
  pulls full parent conclusions; happy path persists merged conclusion
  with cross-parent citations; reductive guards reject non-empty
  `searches` or `proposed_hypotheses`; safety floor inserts auto-synth
  when ≥5 supporters and skips when already covered.
- **Meta-synth fallback** (2 unit tests): oversized view triggers
  meta-synth over the frontier; no-frontier oversized view raises
  cleanly.
- **Live force-spawn synthesize** over the GLP-1/MACE top hypothesis:
    - 4 parent nodes (the supporters of `h_d3c00657fcad`).
    - **Merged conclusion** with 6 evidence-pooled key_findings, each
      citing 2–6 papers across multiple parents (27 total citations,
      16 unique paper links).
    - **Confidence: medium** — correctly calibrated: directional
      agreement with explicit variation noted (component-level MI,
      head-to-head with SGLT2i, exenatide/lixisenatide neutrality).
    - **8 open questions carried forward** for residual gaps.
    - **0 fabricated paper_ids** — every cite traces to a parent's
      citation pool.
    - **Frontier collapse**: after the synthesize node, the planner
      view shows ONLY the synthesis (`frontier = [n_a266e5eaa8cb]`);
      the 4 parents are correctly excluded because they now have a
      child in `node_parents`.

---

## What's intentionally not done yet

- **Cost telemetry per shard.** `tokens used` parsing from transcripts
  is still TODO. Add when slice 7's full investigate loop wants budget
  gating.
- **Parallel worker pool.** `drain_round` and `drain_synthesizes` are
  serial. Atomic claim is in place; just needs a ThreadPoolExecutor +
  per-thread `connect()`.
- **`papers` metadata hydration.** Cited papers land with `id` only.
- **Hypothesis lifecycle.** `hypotheses.status` is always `open` —
  no code transitions to `supported` / `contradicted` / `resolved`.
  Natural place: the synthesizer could close a hypothesis when its
  merged conclusion explicitly resolves it.
- **Stalled-rounds detection.** Convergence trigger #4 from DESIGN
  §2.6. Lives in slice 7's investigate loop.
- **Cross-investigation hypothesis sharing.** Schema supports it
  (hypotheses are global), code scopes to one investigation.
- **planning_rounds.new_hypotheses / answered_qs.** Stamped as 0
  today. Compute deltas across rounds in slice 7.
- **Hierarchical meta-synth.** Current meta-synth is one-shot over the
  whole frontier. If a 50-node frontier produces a merged brief too
  big for the synthesize prompt itself, we'd need recursive meta-synth.
  Untested live (live view is 11.6k chars).

---

## Known small risks worth tracking

- **Default-path footgun.** Convention: every caller passes `conn=`.
- **FTS sanitizer.** Alphanum length≥3 + OR. Working in practice.
- **Schema migration discipline.** New columns → `_ADDITIVE_MIGRATIONS`.
- **Prompt-template substitution.** `str.replace` only, not
  `str.format` — prompts contain literal `{` / `}` in JSON examples.
- **Codex sandbox trust.** New artifacts directories may trigger a
  one-time codex trust prompt.
- **Paperclip credentials inside codex sandbox.** Handled via
  `PAPERCLIP_CONFIG_DIR` redirect to per-shard writable copy. Escape
  hatches: `GRAPH_SEARCH_DISABLE_PAPERCLIP_PREWARM`,
  `GRAPH_SEARCH_DISABLE_PAPERCLIP_REDIRECT`.
- **Dedup model assumption.** `gpt-4o-mini` via Stanford Azure.
- **Dedup failures absorbed → potential duplicates.** Backfill command
  re-merges.
- **Planner-view bounds are coarse.** 4-chars-per-token proxy. Replace
  with `tiktoken` once views get large.
- **Synthesizer is purely reductive.** Cannot generate new
  `proposed_hypotheses` — design call documented in DESIGN_v0.md §2.3
  + slice-6 design note in this doc's history. If the synthesizer's
  merged conclusion DOES reveal a new claim, the operator has to
  re-spawn an expand node to "make it official" in the hypothesis
  table. v1 may relax this.
- **Safety floor overlap threshold.** A synthesize node covers a
  hypothesis if it has ≥3 of the hypothesis's supporters as parents.
  The threshold is arbitrary — re-evaluate if we see hypotheses
  ping-ponging between covered and uncovered as new supporters land.
- **Meta-synth assumes frontier ≥ 2.** A frontier of 1 oversized node
  (e.g., huge `key_findings`) can't be merged further by the current
  meta-synth — `PlannerViewTooLarge` raises. Hierarchical meta-synth
  is the fix.

---

## Convention

When you finish a slice:

1. Move its row in the *Status snapshot* table to `done` and fill the
   *Verified* column with the concrete check you ran.
2. Update *What's on disk* if new files landed.
3. Update *What's been verified end-to-end* with the new capability.
4. Cull anything from *What's intentionally not done yet* that's now done.
5. If you discovered a new risk, add it to the small-risks list.
6. Leave the build order intact unless you actually changed it; if you
   did, link the decision back to a `DESIGN_v0.md` section or a new
   addendum doc.
7. Replace the *Next slice* section at the bottom with the next one.

---

## Next slice (slice 7 — full `graph-search investigate` loop)

Goal: a single command that takes a research question and runs the
investigation from cold start to convergence — decompose → drain →
{plan → safety-floor → drain expand + synth} × N → done. Idempotent
across crashes; resumable from any partial state.

Concrete work:

1. **Convergence orchestrator** (`investigate.py` or `planner.run_loop`):
     - Loop invariant: investigation in `pending` / `running` →
       step until any of the convergence triggers fires (DESIGN §2.6:
       budget exhausted, max_rounds, planner_done, frontier_empty,
       stalled-for-2-rounds).
     - **Stalled detection**: compare `hypotheses` count and number of
       newly-resolved `open_questions` between the last two rounds
       (use `planning_rounds.new_hypotheses` / `answered_qs` once
       slice 7 starts stamping them).
     - **Budget exhaustion**: needs cost telemetry — parse
       `tokens used:` lines from transcripts inside
       `codex_runner.run` or in a post-shard hook, multiply by a
       configured `USD/Mtoken`, and call
       `store.add_investigation_cost`. Gate `claim_*` calls on the
       remaining budget.
     - **Frontier-empty detection**: the planner already emits `done`
       when convergence conditions are met; harness can also check
       view.frontier == [] as a backstop.

2. **Idempotent restart**: pick up wherever the DB left off. If there
   are pending expand/synthesize nodes at `current_round`, drain
   them first. Then run the planner. If the planner crashed mid-round
   (plan node in `running`), reset to `pending` and re-run.

3. **CLI**: `graph-search investigate "<question>" --budget-usd 20
   --max-rounds 6 --sources pmc,abstracts`. Three subcommands wrap the
   loop:
     - `investigate` — start a NEW investigation and run to convergence
       (decompose + loop).
     - `resume --investigation <id>` — pick up an existing one.
     - `status --investigation <id>` — show round, frontier size,
       hypothesis counts, spend.

4. **Live verify**: kick off a fresh investigation on a different
   biomedical question (e.g., "Does intermittent fasting improve
   metabolic outcomes in adults with prediabetes?"). Let it run to
   `done` and inspect the final state — frontier should be empty or
   minimal, hypotheses well-supported, the convergence trigger
   recorded in `investigations.stop_reason`.

Open question to settle: **should `investigate` fork a worker pool
to parallelise drain phases?** Live drain of 5 nodes took ~30 minutes
serially. A 4-worker pool would cut that to ~8 minutes per round.
The atomic claim is already safe across threads — the gating
question is whether crashes mid-round become harder to reason about.
Lean: ship serial in slice 7, parallel in slice 7b once the loop is
proven on at least one full investigation.

Stop after step 4 and inspect both the answer and the convergence
trace on the new investigation.

---

## Future work — planner-side conclusion consolidation

(Noted but not implemented in the paper-digest / scout-output / paper-mine
slice; reserved for a future change.)

The planner today is purely **generative**: it draws drafts from frontier
gaps + open threads, consolidates them against in-flight work, emits the
next batch. It doesn't *restructure* the accumulated conclusion state —
it can't reorganise hypotheses into a hierarchy, prune stale or
superseded claims, or restructure the open-question backlog. As an
investigation grows past a few dozen done nodes, the planner's view is a
flat list of frontier summaries + hypotheses; structure has to live in
the planner's head each call, which doesn't scale.

The principled move is to give the planner a periodic **consolidate /
restructure** stage that:

- Groups related hypotheses into clusters and emits a cluster summary
  (a "what does the graph believe about X" rollup).
- Marks individual hypotheses as superseded when a newer one strictly
  extends them.
- Promotes open_questions to first-class graph entities so the planner
  can track which ones have been answered, deferred, or abandoned.
- Surfaces "themes" — recurring entities or mechanisms that appear
  across many digests and hypotheses but haven't been named explicitly
  yet.

This is a structural counterpart to the in-shard multi-turn the planner
already does for question consolidation. Architecturally similar lever,
different operating layer.
