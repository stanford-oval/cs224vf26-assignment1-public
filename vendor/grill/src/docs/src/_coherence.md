# Coherence audit — methodology_v2 docs

An honest meta-check that the `methodology_v2` documentation set is complete (every source file and subsystem is covered) and truthful (where the design docs describe behavior the shipped code does not yet wire, this page says so and points to the doc that carries the caveat). Everything below is grounded in a source extraction dated 2026-07-13.

## Coverage

**Module docs — one per source file.** All 15 `.py` files under `src/` (excluding `docs/`) have a module reference page. Two HTML inspectors share one page, and `__init__.py` is the empty package marker with nothing to document.

| Source file | Module doc |
|---|---|
| `orchestrator.py` | `modules/orchestrator.md` |
| `ledger.py` | `modules/ledger.md` |
| `executors.py` | `modules/executors.md` |
| `codex_exec.py` | `modules/codex_exec.md` |
| `schemas.py` | `modules/schemas.md` |
| `metrics.py` | `modules/metrics.md` |
| `measure.py` | `modules/measure.md` |
| `embed.py` | `modules/embed.md` |
| `calibration.py` | `modules/calibration.md` |
| `cli.py` | `modules/cli.md` |
| `selftest.py` | `modules/selftest.md` |
| `stage_to_portal.py` | `modules/stage_to_portal.md` |
| `build_trajectory_html.py` | `modules/html-inspectors.md` |
| `build_explore_html.py` | `modules/html-inspectors.md` |
| `__init__.py` | — (empty package marker) |

**Architecture docs — one per subsystem.** Each of the eight functional subsystems has a concept-level page, plus a top-level overview:

| Subsystem | Architecture doc |
|---|---|
| System overview / blackboard | `architecture/overview.md` |
| Belief ledger (state) | `architecture/belief-ledger.md` |
| Control loop | `architecture/orchestration-loop.md` |
| Frontier selection | `architecture/frontier-selection.md` |
| Promotion & verification | `architecture/promotion-and-verification.md` |
| Calibration & uncertainty | `architecture/calibration-and-uncertainty.md` |
| Budget, cost, FDR brake | `architecture/budget-cost-fdr.md` |
| Executor / LLM layer | `architecture/executor-roles.md` |

**Design + reference.** Design rationale is preserved in `design/methodology.md` (renders `METHODOLOGY_v2`), `design/promotion-redesign.md` (renders `DESIGN_promotion_v3.md`), and `design/algorithm-spec.md` (renders the LaTeX spec). Field-level references live in `reference/config-reference.md`, `reference/schemas-reference.md`, and `reference/claim-lifecycle.md`.

## Design vs implementation gaps

Items the design docs describe but the shipped orchestration loop does **not** call. Each row names the doc(s) that a reader must consult to see the caveat. "Defined" means the function/method exists and is exercised by `selftest.py`; "unwired" means no call site in `orchestrator.py`'s run loop.

| Feature | Status in code | Where documented / caveated |
|---|---|---|
| `executors.evaluate` — the EVALUATE reflection checkpoint (draft-vs-prev-draft rubric scoring) | Defined in `executors.py:307`; **never called** from `orchestrator.py` | `architecture/orchestration-loop.md`, `architecture/executor-roles.md`, `modules/executors.md`, `modules/schemas.md`, `reference/schemas-reference.md`, `design/methodology.md` |
| `executors.judge_forward` — forward-looking direction judge | Defined in `executors.py:292`; **never called** (loop uses `judge_coverage` at `orchestrator.py:607`) | `architecture/orchestration-loop.md`, `architecture/executor-roles.md`, `modules/executors.md`, `modules/schemas.md`, `reference/schemas-reference.md` |
| `ledger.niche_scores` | Defined; **no caller in loop** | `architecture/frontier-selection.md`, `architecture/belief-ledger.md`, `modules/ledger.md`, `design/promotion-redesign.md` |
| `ledger.lineage` | Defined (covered by `selftest.py`); **no caller in loop** | `architecture/belief-ledger.md`, `architecture/promotion-and-verification.md`, `modules/ledger.md`, `reference/claim-lifecycle.md`, `design/algorithm-spec.md` |
| `ledger.same_assertion` | Defined (self-tested); **no caller in loop** | `architecture/belief-ledger.md`, `architecture/promotion-and-verification.md`, `modules/ledger.md`, `reference/claim-lifecycle.md` |
| `ledger.find_corroborators` | Defined (self-tested); **no caller in loop** (loop calls `ledger.corroborate` directly) | `architecture/belief-ledger.md`, `architecture/promotion-and-verification.md`, `modules/ledger.md` |
| `ledger.top_k_open` | Defined; **no caller in loop** | `architecture/frontier-selection.md`, `architecture/belief-ledger.md`, `modules/ledger.md`, `design/methodology.md` |
| `ledger.aspect_texts` | Defined; **no caller in loop** | `architecture/belief-ledger.md`, `modules/ledger.md` |
| Isotonic calibration (`calibration.py`) | **No-op until `calibrate_min_labels` (12) VERIFY labels accrue** (`calibration.py:73`, `:83`); below that threshold it passes confidence through unchanged | `architecture/calibration-and-uncertainty.md`, `modules/calibration.md`, `reference/config-reference.md`, `design/promotion-redesign.md` |
| True k-sample promotion posterior | **Unbuilt** — the promotion posterior falls back to the fixed `promote_kappa` (8.0) pseudo-count rather than a per-claim k-sample posterior | `architecture/calibration-and-uncertainty.md`, `architecture/promotion-and-verification.md`, `modules/orchestrator.md`, `reference/config-reference.md`, `design/promotion-redesign.md` |

For the loop's actual call set, the wired executors are `fields`, `prior`, `ground`, `verify`, `explore`, `rerank`, `judge_coverage`, `patterns`, and `finalize_report`; the wired ledger methods are `direction_scores`, `corroborate`, and `synthesize`.

## Deprecated / legacy knobs

| Knob | Default | Status |
|---|---|---|
| `Config.promote_tau` | `0.6` | **Retained for CLI back-compat, unused.** No longer reads a hard promotion floor; the promotion redesign replaced the hard-floor successive-halving gate with the Thompson/beam lottery. Kept so existing CLI invocations that pass `--promote-tau` do not error. Caveated in `reference/config-reference.md` and `modules/orchestrator.md`. |

Live knobs that *look* legacy but are not: `promote_kappa` (8.0) is still the active fallback pseudo-count for the promotion posterior (see the k-sample gap above), and `calibrate_min_labels` (12) / `calibrate_refit_every` (6) gate the isotonic recalibrator that *is* wired but dormant until enough labels accrue.

## Known doc caveats

- **"Defined" is not "run."** Several features are fully implemented and exercised by `selftest.py` (lineage propagation, corroboration re-scoring, `same_assertion`, `find_corroborators`) yet are never invoked by the live `orchestrator.py` run loop. A reader who greps only the module docs will see these described in the present tense; the gap table above is the authority on what actually executes in a run.
- **Calibration reads as active but is usually dormant.** In a typical run the number of VERIFY confirm/refute labels stays below `calibrate_min_labels` (12), so the isotonic recalibrator is a pass-through and confidences are the LLM's raw self-reported numbers. The estimator (scorer model + prompt) must stay fixed for the fitted step functions to be valid.
- **Promotion posterior is an approximation.** Where the design docs describe a per-claim k-sample Beta posterior, the code uses a single fixed-`kappa` pseudo-count. Treat design-doc claims about posterior *sharpness* as aspirational.
- **Design docs mix implemented and deferred status.** `design/promotion-redesign.md` (Components A–G) and `design/methodology.md` render the original design records verbatim, including features marked "deferred" there. They are faithful to the *design*, not necessarily to the shipped loop — cross-check against the module docs and this audit.
- **Line numbers drift.** All `file:line` citations in the docs and in this audit are pinned to the 2026-07-13 source extraction. Any edit to `orchestrator.py`, `ledger.py`, or `executors.py` can shift them; re-run the extraction before trusting an exact line.
