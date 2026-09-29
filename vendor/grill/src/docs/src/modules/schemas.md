# schemas.py

This page walks `schemas.py` top to bottom: the Azure-strict JSON conventions the schemas must obey, the shared leaf objects, and each executor output schema. Every schema here is a plain Python `dict` (a JSON Schema fragment) that `executors.py` passes to `codex exec --output-schema` so the model's final message is forced to validated JSON.

Related: [executors.py](./executors.md) · [codex_exec.py](./codex_exec.md) · [ledger.py](./ledger.md) · [Executor output schemas (reference)](../reference/schemas-reference.md) · [The executor roles](../architecture/executor-roles.md)

## What this module is

`schemas.py` contains no functions and no runtime logic — it is a flat set of module-level `dict` constants (`schemas.py:1`-`290`). Each constant is a JSON Schema object. `executors.py` imports the module and hands the relevant schema to `run_task(...)`, which routes it to `codex exec` (see [codex_exec.py](./codex_exec.md)). The model is then constrained to emit exactly that shape.

For the exhaustive field-by-field tables (types, nullability, semantics of every property), see [reference/schemas-reference.md](../reference/schemas-reference.md). This page summarizes each schema and its wiring.

## The Azure-strict conventions

The module docstring (`schemas.py:1`-`15`) states the three rules the docuset Azure provider enforces for *strict* structured output. Every object in this file follows them:

| Rule | Consequence in the code |
| --- | --- |
| Every object sets `additionalProperties: false` | Present on every `{"type": "object", ...}` fragment. |
| Every declared property must appear in `required` | Optionals are not omitted — they are made nullable via a union type, e.g. `year: {"type": ["integer", "null"]}` (`schemas.py:26`), and still listed in `required` (`schemas.py:34`). |
| No `format` / `minimum` / `pattern` keywords | Numeric ranges (confidences in `[0,1]`, scores in `[0,1]`) are documented only in comments, never enforced by the schema. |

Because of these rules, dynamic maps cannot be modelled as open objects. The ledger's `numbers: dict[metric, value]` is therefore expressed as an **array of `{metric, value}` pairs** and re-folded into a dict on ingest (`schemas.py:12`-`14`; the pair object is `NUMBER_PAIR`, `schemas.py:37`).

## Leaf objects (shared building blocks)

These four objects are composed into the executor schemas below.

| Constant | Location | Purpose | Notes |
| --- | --- | --- | --- |
| `SOURCE_REF` | `schemas.py:20`-`35` | A citation: `title`, `authors`, `year`, `journal`, `doi`, `pmid`, `pmc`, `url`, `quote`. | All bibliographic fields except `title`/`authors` are nullable unions. |
| `NUMBER_PAIR` | `schemas.py:37`-`45` | One `{metric, value}` entry. | `value` is `["number", "string"]` — accepts `"12%"` or `0.12`. This is the map-as-array workaround. |
| `CLAIM` | `schemas.py:47`-`64` | One extracted claim: `text`, `stance` (enum `supports`/`refutes`/`neutral`), `aspects`, `numbers` (array of `NUMBER_PAIR`), `evidence` (array of `SOURCE_REF`), plus a Thompson-style posterior `confidence` with a `conf_low`/`conf_high` ~90% credible interval. | Comments (`schemas.py:57`-`59`) define the interval as *how sure* the model is, given evidence read: `low <= confidence <= high`, all in `[0,1]`. |
| `NEW_DIRECTION` | `schemas.py:66`-`77` | A proposed next research direction: `question_text`, `rationale`, self-reported `promise` (EIG-ish, 0..1), `est_cost` (USD), and `pool` (enum `explore`/`verify`). | Emitted by `EXPLORE` and `EVALUATE`. |

## Executor output schemas

The table maps each schema to the `executors.py` function that submits it, its codex mode, and whether the orchestration loop actually calls it. See [The orchestration loop](../architecture/orchestration-loop.md) and [orchestrator.py](./orchestrator.md) for the call sites.

| Schema | Location | Executor fn (mode) | Called by loop? |
| --- | --- | --- | --- |
| `REQUIRED_FIELDS` | `schemas.py:104` | `fields` (`executors.py:45`, reason) | Yes — INIT (`orchestrator.py:235`) |
| `PRIOR` | `schemas.py:81` | `prior` (`executors.py:61`, reason) | Yes — INIT (`orchestrator.py:236`) |
| `GROUND` | `schemas.py:113` | `ground` (`executors.py:90`, research) | Yes — INIT (`orchestrator.py:255`) |
| `EXPLORE` | `schemas.py:124` | `explore` (`executors.py:144`, research) | Yes — explore waves (`orchestrator.py:350`) |
| `RERANK` | `schemas.py:135` | `rerank` (`executors.py:75`, reason) | Yes — frontier rerank (`orchestrator.py:406`) |
| `VERIFY` | `schemas.py:148` | `verify` (`executors.py:185`, research) | Yes — prior probe + VERIFY pool (`orchestrator.py:287`, `569`) |
| `PATTERNS` | `schemas.py:198` | `patterns` (`executors.py:235`, reason) | Yes — synthesis/finalize (`orchestrator.py:637`, `663`) |
| `FINALIZE` | `schemas.py:215` | `finalize_report` (`executors.py:271`, reason) | Yes — FINALIZE (`orchestrator.py:670`) |
| `JUDGE_COVERAGE` | `schemas.py:225` | `judge_coverage` (`executors.py:289`, reason) | Yes — checkpoint (`orchestrator.py:607`) |
| `JUDGE_FORWARD` | `schemas.py:246` | `judge_forward` (`executors.py:304`, reason) | **No — defined but never called** |
| `EVALUATE` | `schemas.py:266` | `evaluate` (`executors.py:323`, reason) | **No — defined but never called** |

> Honesty note: the module docstring (`schemas.py:1`) says "five codex executor tasks", but the file declares eleven executor schemas. Two of them — `JUDGE_FORWARD` and `EVALUATE` — are wired to executor functions (`executors.py:304`, `executors.py:323`) that no code path in `orchestrator.py` invokes. A repo-wide search finds no live caller of `executors.judge_forward` or `executors.evaluate`. Their schemas and prompts exist but do not run in the current loop. Treat them as dead until the orchestrator is changed.

### PRIOR — `schemas.py:81`-`102`

Initial model-knowledge probe (no web). Fields: `knowledge`, `prior_hypothesis`, `candidate_answers` (array of `{answer, confidence, aspect}` — the Component G seed that lets the init probe verify candidates and seed the calibration map), `key_terms`, and `open_questions`. The orchestrator turns `open_questions` and `candidate_answers` into seed directions (`ledger.py:164`, `ledger.py:168`).

### REQUIRED_FIELDS — `schemas.py:104`-`111`

The smallest schema: a single `required_fields: [string]`. Parses the explicit, separable asks from the research question so coverage can be scored later. `fields(...)` returns `data["required_fields"]` or `[]` on codex failure (`executors.py:45`-`46`).

### GROUND — `schemas.py:113`-`122`

Nails one key term: `term`, `definition`, and a single `SOURCE_REF`. Runs in research mode (must touch a real source). INIT grounds `cfg.ground_terms` terms in parallel (`orchestrator.py:254`).

### EXPLORE — `schemas.py:124`-`133`

The main research-wave output: `claims` (array of `CLAIM`), `new_directions` (array of `NEW_DIRECTION`), and a `dead_end` boolean. Ingested with provenance by `Ledger.ingest` (`ledger.py:227`).

### RERANK — `schemas.py:135`-`146`

Frontier reranker output: `rankings`, an array of `{id, score}` where `score` is in `[0,1]`. The executor re-folds it into `{id: score}` (`executors.py:76`). Opt-in via `cfg.rerank_frontier` (`orchestrator.py:404`).

### VERIFY — `schemas.py:148`-`169`

The richest schema. The Component D three-state `verdict` enum drives claim routing:

| `verdict` | Meaning | Ledger action (`ledger.py:333`) |
| --- | --- | --- |
| `confirmed` | Literature supports the claim as written. | Lock the claim. |
| `error` | Core supported, but a fixable defect (attribution / numbers / scope / mis-cite). | Re-open a corrective direction (`ledger.py:366`). |
| `refuted` | No support or contradicted. | Refuted; corrective direction into the explore pool (`ledger.py:373`). |

Other fields: `defect` (nullable, for `error`), `confirmed` (legacy boolean mirror of `verdict == "confirmed"`), `author_venue_matches` (anti-confabulation gate), `corrected_numbers` (array of `NUMBER_PAIR`), `corrected_source` (`SOURCE_REF`), `source_resolvable`, `refutation` (nullable), and a post-verification posterior `confidence` / `conf_low` / `conf_high`.

### PATTERNS — `schemas.py:198`-`203`

Wraps `patterns`, an array of `_PATTERN_ROW` (`schemas.py:181`-`196`). Each row is a fixed 8-field cross-cutting pattern: `pattern`, `abstraction`, `instance`, `direction`, `support`, `sources`, `hypothesis`, `novelty`. Used to seed a synthesis / open-questions section of the final report (`executors.py:264`).

### FINALIZE — `schemas.py:215`-`223`

Two-step report contract: `outline` (array of `_OUTLINE_SECTION` = `{heading, intent}`, `schemas.py:205`-`213`) is the plan, and `report_markdown` is the filled report string.

### JUDGE_COVERAGE — `schemas.py:225`-`244`

`fields`, an array of `{field, covered (bool), contributing_aspects}` — whether at least one grounded claim answers each required field. Called at checkpoint (`orchestrator.py:607`).

### JUDGE_FORWARD — `schemas.py:246`-`264` (unwired)

`directions`, an array of `{id, score}` scoring each open direction as testable-and-non-obvious (the `q(d)` proxy meant to replace self-reported `promise`). The executor is defined (`executors.py:292`-`304`) but no orchestrator path calls it.

### EVALUATE — `schemas.py:266`-`289` (unwired)

Reflexion-style checkpoint reflection: `per_axis_intrinsics` (a fixed object of four `_AXIS` `{score, note}` entries for `correctness`, `completeness`, `forward_looking`, `faithfulness`; `_AXIS` at `schemas.py:171`-`179`), a `weakest_axis` enum over those four, `corrective_directions` (array of `NEW_DIRECTION`), and `regressions` (array of strings). The executor (`executors.py:307`-`323`) is not called by the loop.

## Ingestion contract

The map-as-array design (`schemas.py:12`) means consumers must re-fold pair arrays into dicts. `NUMBER_PAIR` arrays are the canonical case; see `Ledger.ingest` (`ledger.py:227`) and the claim-lifecycle reference for how `CLAIM.numbers` and `VERIFY.corrected_numbers` are absorbed. Nullable union fields (e.g. every optional in `SOURCE_REF`) always arrive as keys with `null` values, never absent — code should test for `None`, not `KeyError`.

## See also

- [Executor output schemas (reference)](../reference/schemas-reference.md) — exhaustive field tables.
- [executors.py](./executors.md) — the functions that submit these schemas.
- [Claim lifecycle (reference)](../reference/claim-lifecycle.md) — how `CLAIM` / `VERIFY` verdicts move a claim through states.
- [The belief ledger](../architecture/belief-ledger.md) — the in-memory structures these schemas populate.
