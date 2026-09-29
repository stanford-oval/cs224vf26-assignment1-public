# methodology_v2 — documentation

methodology_v2 is a budget-bounded, self-correcting literature-research agent. It answers one research question by spending a fixed USD budget on many small LLM calls, accumulating grounded, source-verified claims, and rendering a report. It is built as a **Blackboard architecture**: a plain-Python orchestrator owns a typed belief ledger and all control flow, and drives the run as a sequence of stateless, schema-constrained `codex` executor calls — INIT, a best-first main loop, then finalize.

The organizing idea is that **the orchestrator owns the state and the control; the LLM is a pure function.** Every model call is `f(task, context) → structured JSON` against a fixed schema; the model never decides the next step and never holds the belief state. That inversion — taking the loop and the state away from the model — is what lets the harness enforce provenance, manage a frontier, calibrate its own confidence, and keep working until the budget (not the model) says stop.

## Suggested reading order

A newcomer should read these in order, from concept to code:

1. [Architecture: system overview](architecture/overview.md) — what the system is and how the three parts fit together.
2. [Architecture: the orchestration loop](architecture/orchestration-loop.md) — the control shell: INIT, the best-first round loop, and finalize.
3. [Architecture: the belief ledger](architecture/belief-ledger.md) — the typed graph that *is* the blackboard.
4. [Architecture: the executor roles](architecture/executor-roles.md) — how `codex` is used as a set of stateless pure functions.
5. [Architecture: promotion and verification](architecture/promotion-and-verification.md) — how a claim travels from a raw hit to an adjudicated verdict.
6. Then the [Reference](#reference) tables (schemas, config knobs, claim lifecycle) for exact contracts,
7. and the [Modules](#modules-low-level) pages for the top-to-bottom code walk of each source file.

## Architecture (high-level)

Concept-level tours of each subsystem.

- [overview.md](architecture/overview.md) — Entry point: what methodology_v2 is, the orchestrator-owns-state / LLM-as-pure-function premise, and how the ledger, executors, and control loop fit across a run.
- [orchestration-loop.md](architecture/orchestration-loop.md) — The single-threaded control shell that owns run state and drives stateless executors in parallel waves: INIT, the best-first round loop, stall-driven deepening, termination, and finalize.
- [belief-ledger.md](architecture/belief-ledger.md) — The typed graph that is the v2 blackboard: its objects, why there is no `Entity` type, the provenance gate that lets a finding graduate, and how claims link to the frontier and to one another.
- [executor-roles.md](architecture/executor-roles.md) — The LLM layer: how `codex` is used as stateless, schema-constrained pure functions that take a slice of state and return validated JSON plus the USD it cost.
- [promotion-and-verification.md](architecture/promotion-and-verification.md) — How a claim is promoted from an EXPLORE hit to a spent VERIFY call: the resurfacing pool, the beam-plus-Thompson lottery, the three-state verdict, and corroboration re-scoring.
- [calibration-and-uncertainty.md](architecture/calibration-and-uncertainty.md) — How the agent represents belief confidence and corrects it against its own verification outcomes (Component B: the isotonic recalibrator that feeds promotion).
- [budget-cost-fdr.md](architecture/budget-cost-fdr.md) — The resource-control subsystem: the two-pool USD budget, real per-model cost metering, wave sizing, and the online-FDR "error wealth" that throttles speculative verifies — and why the budget is what stops the run.
- [frontier-selection.md](architecture/frontier-selection.md) — How the orchestrator picks which OPEN directions to explore next each round: the embedding-based promise score, the EXPLORE context slice, the optional LLM reranker, and the niche/hierarchy boost.

## Modules (low-level)

One page per source file — a top-to-bottom implementation walkthrough with `file:line` citations.

- [ledger.py](modules/ledger.md) — The belief ledger: the typed in-memory blackboard the orchestrator owns and mutates deterministically — four dataclasses, constants/helpers, and every `Ledger` method.
- [orchestrator.py](modules/orchestrator.md) — The only stateful component: the two budget classes, the `Config` dataclass, and every `Orchestrator` method (INIT, round loop, frontier selection, promotion posterior, verify pool, checkpoint/convergence, finalize).
- [executors.py](modules/executors.md) — Three digest helpers plus eleven executor functions, each a thin, stateless wrapper that builds a prompt, calls `run_task` with a fixed schema and mode, and returns `(validated_json, usd)`.
- [schemas.py](modules/schemas.md) — The flat set of module-level JSON-Schema `dict` constants (Azure-strict conventions, shared leaf objects, one per executor output) passed to `codex exec --output-schema`.
- [codex_exec.py](modules/codex_exec.md) — The single LLM primitive: `run_task(...) -> (validated_json, usd)` as one ephemeral `codex exec` subprocess — execution modes, proxy wiring, retries, per-model pricing and real-spend metering.
- [calibration.py](modules/calibration.md) — The Component B posterior calibrator: pure Python that fits two isotonic step functions from VERIFY's confirm/refute labels (confidence→probability, stated-width→outcome-variance).
- [embed.py](modules/embed.md) — The semantic-similarity helper: a small cached `Embedder` around `text-embedding-3-large` plus cosine utilities used for the methodology's `cos(emb(·), emb(·))` terms.
- [measure.py](modules/measure.md) — The semantic-instrument layer that turns embeddings and LLM-judge output into scalar terms: the EXPLORE context slice, the frontier promise function, and the coverage reducer.
- [metrics.py](modules/metrics.md) — The `PromiseWeights` tunable, two ledger-derived scores (`confab_rate`, `quality`), and the `Snapshot` dataclass plus `build_snapshot` recorded at every checkpoint — pure reducers over a `Ledger`.
- [cli.py](modules/cli.md) — The command-line entry point: the argument parser, how each flag maps onto a `Config` field, and how the question, reference set, and `Orchestrator` are constructed and launched.
- [selftest.py](modules/selftest.md) — The offline correctness harness that exercises the deterministic core (provenance gate, promotion, three-state verification, lineage, corroboration, reducers, synthesis) with no codex calls and no embeddings.
- [build_trajectory_html.py / build_explore_html.py](modules/html-inspectors.md) — Two standalone hand-run scripts that turn a completed run directory into a single self-contained offline HTML file (whole-run trajectory view and per-EXPLORE-agent view).
- [stage_to_portal.py](modules/stage_to_portal.md) — A standalone CLI that converts a finished run directory into a "report-only" investigation the OVAL portal can display (`extracted/<slug>_db/` with report, question, and a v2-native activity summary).

## Reference

Exhaustive, lookup-oriented reference tables.

- [schemas-reference.md](reference/schemas-reference.md) — Field-by-field reference for every JSON schema in `schemas.py` — the exact contract each `codex exec` call must satisfy.
- [config-reference.md](reference/config-reference.md) — Field-by-field reference of every `Config` knob and the `Budget` split, each with its default, meaning, and the exact `orchestrator.py` read sites (deprecated/unwired knobs marked).
- [claim-lifecycle.md](reference/claim-lifecycle.md) — Formal reference for the `Claim` verification state machine: states, every transition and its trigger, and the side effects applied on each transition.

## Design

These are design and rationale records. They preserve the intended design and the author's status annotations, so **they may describe parts that were never built** or that differ from the shipped code; for current behavior, follow the architecture docs.

- [methodology.md](design/methodology.md) — Faithful rendering of the original `METHODOLOGY_v2` design record: why v2 exists, the core principle, the blackboard architecture, executor contracts, the loop, direction selection, the two-pool budget, and termination (design record, not as-built).
- [promotion-redesign.md](design/promotion-redesign.md) — The promotion/verification redesign (`DESIGN_promotion_v3.md`): the three defects of the old hard-floor promotion and the seven components (A–G) that replace it, each with its implemented/deferred status.
- [algorithm-spec.md](design/algorithm-spec.md) — Prose-and-table rendering of the formal specification in `METHODOLOGY_v2_algorithm.tex`: notation, the parameter table, and every algorithm block from the main loop through the cost model.

## Documentation map

For how these pages cross-reference one another — the full link graph and the coherence checks that keep them consistent — see [_coherence.md](_coherence.md).
