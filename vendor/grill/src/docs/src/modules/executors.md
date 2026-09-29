# executors.py

Low-level walkthrough of `executors.py`: three digest helpers plus eleven executor functions. Each executor is a thin wrapper that builds a prompt string, calls `codex_exec.run_task` with a fixed schema and mode, and returns `(validated_json, usd)`. None of them own state — the orchestrator holds the ledger and decides what to do with each result.

Related: [../architecture/executor-roles.md](../architecture/executor-roles.md), [./codex_exec.md](./codex_exec.md), [./orchestrator.md](./orchestrator.md), [./schemas.md](./schemas.md), [../reference/schemas-reference.md](../reference/schemas-reference.md)

## What this module is

The module docstring (`executors.py:1-14`) frames each function as "a pure schema-constrained call" (Methodology §3). Every executor calls `run_task(task_dir, prompt, schema, mode=..., **kw)` from `codex_exec` (`executors.py:21`), which enforces the JSON schema and returns the validated dict plus the USD the call cost. On a soft codex failure `run_task` returns `(None, usd)` after retrying (`codex_exec.py:204`), so several executors defensively coerce `None` into an empty result.

Imports are minimal (`executors.py:15-22`): `json`, `Path`, the `schemas` module, `run_task`, and three ledger types (`Claim`, `Direction`, `Ledger`).

The docstring carries a role/mode table (`executors.py:3-10`). Note it lists only six roles (PRIOR, FIELDS, GROUND, EXPLORE, VERIFY, EVALUATE) and is not exhaustive — `rerank`, `patterns`, `finalize_report`, `judge_coverage`, and `judge_forward` are not in it.

## Two codex modes

`mode` is passed straight through to `codex_exec` (`codex_exec.py:9`):

| mode | Sandbox | Used by |
|----------|-------------------------|---------------------------------------------------------------|
| `reason` | read-only, no web | `fields`, `prior`, `rerank`, `patterns`, `finalize_report`, `judge_coverage`, `judge_forward`, `evaluate` |
| `research` | web/tools enabled | `ground`, `explore`, `verify` |

Only the three `research`-mode executors actually read sources; the rest reason over text already in the prompt.

## Executor roles at a glance

| Function | mode | Schema | Called by orchestrator? | Return shape |
|-------------------|------------|-----------------------|-------------------------|--------------|
| `fields` | reason | `REQUIRED_FIELDS` | yes (`orchestrator.py:235`) | `(list[str], usd)` |
| `prior` | reason | `PRIOR` | yes (`orchestrator.py:236`) | `(dict, usd)` |
| `rerank` | reason | `RERANK` | yes (`orchestrator.py:406`) | `({id: score}, usd)` |
| `ground` | research | `GROUND` | yes (`orchestrator.py:255`) | `(dict, usd)` |
| `explore` | research | `EXPLORE` | yes (`orchestrator.py:350`) | `(dict, usd)` |
| `verify` | research | `VERIFY` | yes (`orchestrator.py:287`, `569`) | `(dict, usd)` |
| `patterns` | reason | `PATTERNS` | yes (`orchestrator.py:637`, `663`) | `(dict, usd)` |
| `finalize_report` | reason | `FINALIZE` | yes (`orchestrator.py:670`) | `(dict, usd)` |
| `judge_coverage` | reason | `JUDGE_COVERAGE` | yes (`orchestrator.py:607`) | `(dict, usd)` |
| `judge_forward` | reason | `JUDGE_FORWARD` | **NO — dead code** | `(dict, usd)` |
| `evaluate` | reason | `EVALUATE` | **NO — dead code** | `(dict, usd)` |

**Unwired executors.** `judge_forward` (`executors.py:292`) and `evaluate` (`executors.py:307`) are fully defined but the orchestrator never calls either — a repo-wide grep for `executors.judge_forward` / `executors.evaluate` finds no call site. Their schemas (`schemas.JUDGE_FORWARD`, `schemas.EVALUATE`) exist and the docstrings claim they replace older proxies (`q(d)` scoring; a Reflexion checkpoint), but that path is not implemented in the running loop. Several comments and the HTML inspectors still describe an "EVALUATE checkpoint" (`orchestrator.py:7`, `ledger.py:479`, `build_trajectory_html.py:269,429`), which is aspirational, not live. Treat both functions as dead code when reasoning about actual behavior.

## Digest helpers

Three private helpers render ledger claims into prompt-ready text. They are the only place the executor prompts touch ledger internals.

### `_slice_for(d, ctx)` — `executors.py:25-33`

Renders the "already known" context passed into an `explore` call. `ctx` is a list of `Claim`; it does not actually use the `Direction` argument `d`. For each claim it takes the first evidence SourceRef and picks a locator in priority order `doi → pmid → pmc → url` (`executors.py:31`), then emits one line `- [<verification>] <text>  (src: <loc>)`. Empty context returns the literal `"(no related findings in the ledger yet)"`.

### `_claim_digest(ledger, grounded_only=True, limit=80)` — `executors.py:188-195`

Used by `judge_coverage`. Selects `ledger.graduated_claims()` when `grounded_only` (the default), else all claims; sorts by descending `confidence`; truncates to `limit`. Each row is `- [<verification>] <text>  (aspects: <asp>)`. Falls back to `"(no grounded claims yet)"`.

### `_finalize_digest(ledger, limit=220)` — `executors.py:198-216`

The richer, numbered digest used by `patterns` and `finalize_report`. It takes only graduated (sourced) claims and sorts with a two-key comparator (`executors.py:202`): `confirmed` claims first, then by descending confidence. For each it builds a locator (`doi → PMID:<pmid> → pmc → url`), a first-author string with "et al." when there is more than one author (`executors.py:208`), a joined `numbers` string, and a state tag where `confirmed` is upper-cased to `CONFIRMED`. Rows are `[F<i>] (<TAG>) <text> | numbers: ... | aspects: ... | SOURCE: <author> (<year>) <title> <loc>`. Fallback: `"(no grounded findings)"`.

## INIT executors

These run once at run start to seed the ledger.

### `fields(question, task_dir, **kw)` — `executors.py:38-46`

Parses the EXPLICIT, separable asks from the question — "Be literal — do not invent asks the question did not make." Returns `(list[str], usd)`, extracting `data["required_fields"]` and coercing a `None` result (codex failure) to `[]` (`executors.py:46`). The orchestrator stores this in `ledger.required_fields`, which later drives coverage judging and the finalize outline.

### `prior(question, task_dir, **kw)` — `executors.py:49-61`

Domain-expert cold start "from your own knowledge ONLY (no tools)." Returns the raw `(dict, usd)`. The requested JSON has `knowledge`, `prior_hypothesis`, `candidate_answers` (each `{answer, confidence∈[0,1], aspect}`), `key_terms`, and `open_questions` (`executors.py:55-59`). The candidate answers become claims the loop later probes with `verify`; `key_terms` feed `ground`; `open_questions` seed initial directions.

### `ground(term, question, task_dir, budget_hint=None, **kw)` — `executors.py:79-90`

`research`-mode. Defines one `term` in the question's context, requiring the model to search, READ an authoritative source, and return a definition plus a single resolvable `SourceRef` — "Do not invent author names — copy them from the source." When `budget_hint` is set it appends a one-line budget note (`executors.py:87-88`). Returns `(dict, usd)`. The orchestrator fans these out per key term (`orchestrator.py:255`) and stores results in `ledger.glossary`.

## MAIN-LOOP executors

### `rerank(question, items, task_dir, **kw)` — `executors.py:64-76`

An LLM reranker with no tools. `items` is a list of `(id, text)`; it scores each candidate direction's value-to-pursue-next in `[0,1]`. It formats the candidates, calls `run_task` with `schemas.RERANK`, then reduces `data["rankings"]` (a list of `{id, score}`) into a `{id: float(score)}` dict, coercing missing scores to `0.0` and a `None` result to `{}` (`executors.py:76`). Docstring notes it is used as a sharper ranker than raw embedding cosine on small or pre-filtered candidate sets; the orchestrator calls it during frontier selection (`orchestrator.py:406`).

### `explore(d, ctx, question, task_dir, budget_hint=None, **kw)` — `executors.py:95-126`

The core research executor: investigate ONE `Direction` for the overall question, reading real sources via codex's own `web_search`. The prompt is assembled from an optional budget fragment plus a fixed body:

```
prompt = <base instruction>
         + cap      (budget note, if budget_hint)
         + <body: question, direction, already-known slice, return-schema spec>
```

- **`cap`** (`executors.py:98-101`) — appended only when `budget_hint` is set; tells the model to do a focused search and EMIT JSON before the budget is exhausted because "a killed task returns nothing."
- **body** — injects the overall question, `d.question_text`, `d.rationale`, and `_slice_for(d, ctx)` as the already-known context, then specifies the return JSON.

Requested return fields:

| Field | Meaning |
|-----------------|---------|
| `claims` | atomic findings, each `{text, stance (supports/refutes/neutral), aspects (1-3 tags), numbers (metric/value pairs), evidence (≥1 resolvable SourceRef), confidence, conf_low, conf_high}` — a posterior point probability plus a ~90% credible interval whose width reflects evidence strength |
| `new_directions` | follow-up sub-questions, each with self-estimated `promise∈[0,1]` and `est_cost` (USD) |
| `dead_end` | bool — nothing more worth pursuing |

The prompt warns that "A claim with no resolvable source will be DISCARDED." It calls `run_task` with `schemas.EXPLORE`, `mode="research"` (`executors.py:126`). Returns `(dict, usd)`.

### `verify(claim, task_dir, budget_hint=None, **kw)` — `executors.py:148-185`

Adversarial fact-checker. It serializes the claim's first evidence SourceRef into a JSON block (`executors.py:151-156`) and a comma-joined `numbers` string (`executors.py:157`), then instructs the model to SEARCH THE LITERATURE — using the cited source only as an anchor — and:

1. search and read the strongest sources,
2. run anchor checks setting `source_resolvable`, `author_venue_matches`, `corrected_numbers`, `corrected_source`,
3. decide a three-state `verdict`:

| verdict | Meaning |
|-------------|---------|
| `confirmed` | literature genuinely supports the claim as written |
| `error` | core assertion supported but a FIXABLE defect exists (wrong author/venue/numbers, overstated scope, mis-cited anchor); the precise defect goes in `defect` |
| `refuted` | no support or active contradiction; explained in `refutation` |

It also sets `confirmed = (verdict == "confirmed")` for back-compat and emits an updated posterior (`confidence`, `conf_low`, `conf_high`). A `budget_hint` appends a proportional-search note (`executors.py:181-183`). Returns `(dict, usd)`. The orchestrator invokes `verify` in two places: probing prior candidate answers (`orchestrator.py:287`) and the main verification pass (`orchestrator.py:569`).

### `patterns(ledger, task_dir, **kw)` — `executors.py:219-235`

Distills CROSS-CUTTING abstract patterns over grounded findings (the fixed 8-field "patterns" table carried over from the v1 agent). It renders findings via `_finalize_digest(ledger, limit=150)` and asks for the strongest 4-8 patterns, each with `pattern`, `abstraction`, `instance`, `direction`, `support`, `sources`, `hypothesis`, `novelty` (`executors.py:226-230`). `reason` mode, `schemas.PATTERNS`. Called during checkpoints and finalize (`orchestrator.py:637,663`); its rows feed `finalize_report`.

### `finalize_report(question, ledger, patterns_rows, task_dir, **kw)` — `executors.py:238-271`

Outline-then-fill report writer. It pre-renders three prompt inputs: the explicit asks from `ledger.required_fields` (`executors.py:243`), up to 8 `patterns_rows` formatted as PATTERN blocks (`executors.py:245-247`), and a glossary line per `ledger.glossary` entry (`executors.py:248`). The prompt has two mandated steps returned together:

- **STEP 1 — OUTLINE**: `outline = [{heading, intent}]` that must cover every explicit ask, and must include an explicit ranked section when the question asks to rank items.
- **STEP 2 — FILL**: `report_markdown` following the outline, using ONLY the grounded findings from `_finalize_digest(ledger)` (default limit 220), citing inline, preferring CONFIRMED findings and marking others preliminary, and preferring tables for per-item attributes.

`reason` mode, `schemas.FINALIZE`, returns `(dict, usd)` shaped `{outline, report_markdown}`. Called once at `orchestrator.py:670`.

### `judge_coverage(ledger, task_dir, **kw)` — `executors.py:274-289`

LLM judge for `covered(field)` — the docstring says it replaces the older lexical faithfulness/coverage proxy. For each explicit ask (from `ledger.required_fields`, rendered at `executors.py:277`) it decides whether at least one grounded finding genuinely ANSWERS it, using `_claim_digest(ledger, grounded_only=True)` as the evidence. Returns JSON `fields`, one entry per ask with `covered` (bool) and `contributing_aspects`, with an instruction to "Be strict." `reason` mode, `schemas.JUDGE_COVERAGE`. Called at `orchestrator.py:607`; the result is consumed by the judge reducer in `measure.py:63`.

### `judge_forward(ledger, directions, task_dir, **kw)` — `executors.py:292-304` — UNWIRED

Intended LLM judge for `q(d)`: score each OPEN direction as testable AND non-obvious in `[0,1]`. Renders `id=<d.id>: <d.question_text>` lines and asks for `directions = [{id, score}]`. `reason` mode, `schemas.JUDGE_FORWARD`. **Never called by the orchestrator** — see "Unwired executors" above.

### `evaluate(draft, prev_draft, ledger, rubric, task_dir, **kw)` — `executors.py:307-323` — UNWIRED

Intended Reflexion-style run evaluator: compare the current draft to the previous one, score each rubric axis intrinsically in `[0,1]` "for steering only," and propose corrective directions for the weakest axis. Requested JSON: `per_axis_intrinsics` (correctness/completeness/forward_looking/faithfulness, each `{score, note}`), `weakest_axis`, `corrective_directions` (each with `promise`+`est_cost`), and `regressions`. `reason` mode, `schemas.EVALUATE`. **Never called by the orchestrator** — see "Unwired executors" above.

## Data flow summary

```
question
   │
   ├─ fields ──────────────► ledger.required_fields ──┐
   ├─ prior ──► candidate_answers ─► verify (probe) │  │
   └─ ground (per key_term) ─► ledger.glossary       │  │
                                                       │  │
  main loop                                            │  │
   ├─ rerank(open directions) ─► frontier pick         │  │
   ├─ explore(direction) ─► claims + new_directions ──►│  │  ledger
   ├─ verify(claim) ─► verdict + posterior ───────────►│  │
   ├─ judge_coverage ◄── required_fields, grounded ────┘  │
   └─ patterns ◄── _finalize_digest ──┐                   │
                                        ▼                  │
  finalize                    finalize_report ◄── patterns_rows,
                                required_fields, glossary, findings
```

Everything above the "finalize" band runs inside the orchestration loop; `judge_forward` and `evaluate` are absent from this graph because nothing calls them.
