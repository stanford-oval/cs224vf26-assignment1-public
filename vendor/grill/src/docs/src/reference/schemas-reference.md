# Executor output schemas (reference)

This page is an exhaustive, field-by-field reference for every JSON schema defined in `schemas.py`. Each schema is the exact contract the corresponding `codex exec` call must satisfy: the schema is passed as `--output-schema`, forcing the model's final message to validated JSON.

Related: [schemas.py module notes](../modules/schemas.md) · [The executor roles](../architecture/executor-roles.md) · [executors.py](../modules/executors.md) · [Config knobs (reference)](./config-reference.md) · [Claim lifecycle (reference)](./claim-lifecycle.md)

## Strict-output rules

All schemas obey the Azure provider's *strict* structured-output constraints, documented in the module docstring (`schemas.py:1`-`15`):

| Rule | Consequence |
|---|---|
| Every object sets `additionalProperties: false` | No extra keys may appear in the output. |
| Every declared property must appear in `required` | There are no *omittable* fields. "Optional" fields are made **nullable** via a union type (e.g. `["string", "null"]`) but the key must still be present. |
| No `format` / `minimum` / `pattern` keywords | Ranges like "0..1" and "must be a URL" are documented in comments only; they are **not enforced** by the schema. The model is asked to honor them; nothing validates them. |
| Dynamic maps cannot be open objects | The ledger's `numbers: dict[metric, value]` is modelled as an array of `{metric, value}` pairs (`NUMBER_PAIR`) and re-folded into a dict on ingest. |

Because of rule 2, the "Required" column below is always "yes (present)" — the distinction that matters is whether the *value* may be null. The tables use the **Nullable** column for that.

## Wiring status

Nine of the eleven executor output schemas are reached by the orchestration loop. Two are **dead** — their executor functions are defined in `executors.py` but never called anywhere in the loop:

| Schema | Executor fn | Call site | Status |
|---|---|---|---|
| `REQUIRED_FIELDS` | `fields()` (`executors.py:38`) | `orchestrator.py:235` | live |
| `PRIOR` | `prior()` (`executors.py:49`) | `orchestrator.py:236` | live |
| `RERANK` | `rerank()` (`executors.py:64`) | `orchestrator.py:406` | live, **on by default** (`cfg.rerank_frontier=True`; opt-out) |
| `GROUND` | `ground()` (`executors.py:79`) | `orchestrator.py:255` | live |
| `EXPLORE` | `explore()` (`executors.py:95`) | `orchestrator.py:350` | live |
| `VERIFY` | `verify()` (`executors.py:148`) | `orchestrator.py:287`, `569` | live |
| `PATTERNS` | `patterns()` (`executors.py:219`) | `orchestrator.py:637`, `663` | live |
| `FINALIZE` | `finalize_report()` (`executors.py:238`) | `orchestrator.py:670` | live |
| `JUDGE_COVERAGE` | `judge_coverage()` (`executors.py:274`) | `orchestrator.py:607` | live |
| `JUDGE_FORWARD` | `judge_forward()` (`executors.py:292`) | — | **dead** (never called) |
| `EVALUATE` | `evaluate()` (`executors.py:307`) | — | **dead** (never called) |

Note: the `orchestrator.py:16` header comment references `executors.judge_*` as the semantic-judgment path, but only `judge_coverage` is actually invoked; `judge_forward` is unwired. `EVALUATE` corresponds to the design's Reflexion checkpoint (see [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md)); the schema and executor exist but the loop never calls them.

---

## Leaf objects

These are reused as sub-objects inside the executor schemas below.

### `SOURCE_REF` — `schemas.py:20`

A citation / provenance record. All bibliographic fields except `title` and `authors` are nullable.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `title` | string | no | Source title. |
| `authors` | array of string | no | Author names (may be empty array). |
| `year` | integer | yes | Publication year. |
| `journal` | string | yes | Venue / journal name. |
| `doi` | string | yes | DOI. |
| `pmid` | string | yes | PubMed ID. |
| `pmc` | string | yes | PubMed Central ID. |
| `url` | string | yes | Resolvable URL. |
| `quote` | string | yes | Supporting quote pulled from the source. |

### `NUMBER_PAIR` — `schemas.py:37`

One entry of the `metric -> value` map. Arrays of these are re-folded into dicts on ingest (see strict-output rules above).

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `metric` | string | no | Metric / quantity name. |
| `value` | number or string | no | The value (string is allowed for units, ranges, or non-numeric quantities). |

### `CLAIM` — `schemas.py:47`

A single evidence-bearing claim. Emitted inside `EXPLORE.claims`.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `text` | string | no | The claim statement. |
| `stance` | string enum | no | One of `supports`, `refutes`, `neutral` (relative to the research question). |
| `aspects` | array of string | no | Aspect / facet tags the claim addresses. |
| `numbers` | array of `NUMBER_PAIR` | no | Quantities asserted by the claim. |
| `evidence` | array of `SOURCE_REF` | no | Supporting sources. |
| `confidence` | number | no | Point belief `P(true)`, intended range [0,1] (not enforced). |
| `conf_low` | number | no | Lower bound of a ~90% credible interval on the belief. |
| `conf_high` | number | no | Upper bound of the ~90% credible interval. |

The comment at `schemas.py:57`-`59` specifies the intended invariant `conf_low <= confidence <= conf_high`, all in [0,1], with the interval width expressing how sure the model is given the evidence read (few/weak sources → wide; many/strong → narrow). This is a Thompson-sampling posterior; the schema does not enforce the ordering.

### `NEW_DIRECTION` — `schemas.py:66`

A proposed next research direction. Emitted inside `EXPLORE.new_directions` and `EVALUATE.corrective_directions`.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `question_text` | string | no | The direction phrased as a question. |
| `rationale` | string | no | Why it is worth exploring. |
| `promise` | number | no | Self-reported EIG-ish priority, intended 0..1. |
| `est_cost` | number | no | Self-reported USD to explore. |
| `pool` | string enum | no | One of `explore`, `verify` — which budget pool this belongs to. |

---

## Executor output schemas

### `REQUIRED_FIELDS` — `schemas.py:104`

Output of `fields()`. Parses the research question into the fields an answer must cover.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `required_fields` | array of string | no | The fields/aspects a complete answer must address. |

### `PRIOR` — `schemas.py:81`

Output of `prior()`. Read-only reasoning call; seeds the ledger from model knowledge before any web access.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `knowledge` | string | no | What the model already knows about the topic. |
| `prior_hypothesis` | string | no | An initial hypothesis / candidate answer narrative. |
| `candidate_answers` | array of object | no | Candidate answers, each self-scored (see sub-table). Component G: the init probe verifies these to seed the calibration map. |
| `key_terms` | array of string | no | Terms to nail down via `GROUND`. |
| `open_questions` | array of string | no | Questions that become seed directions. |

`candidate_answers[]` sub-object (`schemas.py:89`-`97`):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `answer` | string | no | A candidate answer. |
| `confidence` | number | no | Self-assessed confidence. |
| `aspect` | string | no | Which aspect this candidate answers. |

### `GROUND` — `schemas.py:113`

Output of `ground()`. Web call that pins one key term to a real source.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `term` | string | no | The term being defined. |
| `definition` | string | no | Its grounded definition. |
| `source` | `SOURCE_REF` | no | The source supporting the definition. |

### `EXPLORE` — `schemas.py:124`

Output of `explore()`. The core research call — LATS-style action generation plus a grounded-claim finder over one direction.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `claims` | array of `CLAIM` | no | Grounded claims found while researching the direction. |
| `new_directions` | array of `NEW_DIRECTION` | no | Follow-on directions spawned by the exploration. |
| `dead_end` | boolean | no | True if the direction yielded nothing worth pursuing. |

### `RERANK` — `schemas.py:135`

Output of `rerank()`. One reasoning call that re-scores a shortlist of frontier directions. **Enabled by default**: `cfg.rerank_frontier` defaults to `True` (`orchestrator.py:115`), so reranking runs unless explicitly disabled. It is invoked when `cfg.rerank_frontier` is true, the frontier is larger than one, and the remaining explore budget exceeds the per-task cap (`ground_task_usd * task_cap_mult`); it is skipped when the budget falls below that cap (`orchestrator.py:404`).

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `rankings` | array of object | no | Per-direction scores (see sub-table). |

`rankings[]` sub-object (`schemas.py:139`-`143`):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `id` | string | no | Direction id. |
| `score` | number | no | New promise score; written back to `direction.promise`. |

### `VERIFY` — `schemas.py:148`

Output of `verify()`. Adversarial re-fetch of a claim's source. Component D three-state verdict.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `verdict` | string enum | no | One of `confirmed` (literature supports), `error` (core supported but a fixable defect — attribution/numbers/scope/mis-cite), `refuted` (no support or contradicts). |
| `defect` | string | yes | For `verdict=error`: the specific fixable defect. |
| `confirmed` | boolean | no | Legacy mirror of `verdict == confirmed`. |
| `author_venue_matches` | boolean | no | Anti-confabulation gate: author/venue check. |
| `corrected_numbers` | array of `NUMBER_PAIR` | no | Corrected quantities (for the error path). |
| `corrected_source` | `SOURCE_REF` | no | The source that best supports the claim (found or echoed). |
| `source_resolvable` | boolean | no | Whether the cited source actually resolves. |
| `refutation` | string | yes | For `verdict=refuted`: why the claim fails. |
| `confidence` | number | no | Posterior point belief after verification. |
| `conf_low` | number | no | Lower bound of the ~90% credible interval post-verification. |
| `conf_high` | number | no | Upper bound of the ~90% credible interval post-verification. |

### `PATTERNS` — `schemas.py:198`

Output of `patterns()`. Cross-cutting synthesis over the gathered findings, feeding the final report.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `patterns` | array of `_PATTERN_ROW` | no | Recurring patterns across findings. |

`_PATTERN_ROW` (`schemas.py:181`), each element of `patterns`:

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `pattern` | string | no | The recurring pattern observed. |
| `abstraction` | string | no | The domain-agnostic generalization. |
| `instance` | string | no | A concrete instance from the findings. |
| `direction` | string | no | A next direction the pattern suggests. |
| `support` | string | no | How strongly the evidence supports it. |
| `sources` | array of string | no | Supporting sources. |
| `hypothesis` | string | no | A testable hypothesis it raises. |
| `novelty` | string | no | How novel / non-obvious it is. |

### `FINALIZE` — `schemas.py:215`

Output of `finalize_report()`. Two-step: plan an outline, then fill it.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `outline` | array of `_OUTLINE_SECTION` | no | Step 1: the section plan. |
| `report_markdown` | string | no | Step 2: the filled-in final report as Markdown. |

`_OUTLINE_SECTION` (`schemas.py:205`), each element of `outline`:

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `heading` | string | no | Section heading. |
| `intent` | string | no | What this section must deliver. |

### `JUDGE_COVERAGE` — `schemas.py:225`

Output of `judge_coverage()`. Per-field coverage judgment over the grounded claims.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `fields` | array of object | no | One entry per required field (see sub-table). |

`fields[]` sub-object (`schemas.py:231`-`240`; properties at `schemas.py:235`-`237`):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `field` | string | no | The required field being judged. |
| `covered` | boolean | no | True if ≥1 grounded claim answers it. |
| `contributing_aspects` | array of string | no | Aspects that contribute to coverage. |

### `JUDGE_FORWARD` — `schemas.py:246` (dead)

Schema for `judge_forward()` (`executors.py:292`), which scores directions for being testable and non-obvious. **The orchestrator never calls this executor**, so this schema is never sent.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `directions` | array of object | no | Per-direction scores (see sub-table). |

`directions[]` sub-object (`schemas.py:255`-`259`):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `id` | string | no | Direction id. |
| `score` | number | no | 0..1, testable AND non-obvious. |

### `EVALUATE` — `schemas.py:266` (dead)

Schema for `evaluate()` (`executors.py:307`), the design's Reflexion checkpoint over the working draft. **The orchestrator never calls this executor**, so this schema is never sent.

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `per_axis_intrinsics` | object | no | Per-axis scores (see sub-table); the four keys are fixed and all required. |
| `weakest_axis` | string enum | no | One of `correctness`, `completeness`, `forward_looking`, `faithfulness`. |
| `corrective_directions` | array of `NEW_DIRECTION` | no | Directions to fix the weakest axis. |
| `regressions` | array of string | no | Regressions spotted vs the prior checkpoint. |

`per_axis_intrinsics` object (`schemas.py:270`-`280`): the keys `correctness`, `completeness`, `forward_looking`, `faithfulness` are each an `_AXIS` object and all four are required.

`_AXIS` (`schemas.py:171`):

| Field | Type | Nullable | Meaning |
|---|---|---|---|
| `score` | number | no | 0..1 intrinsic score, for steering only. |
| `note` | string | no | Rationale for the score. |

---

## Schema → sub-object dependency map

```
SOURCE_REF ──┬─> CLAIM.evidence
             ├─> GROUND.source
             └─> VERIFY.corrected_source

NUMBER_PAIR ─┬─> CLAIM.numbers
             └─> VERIFY.corrected_numbers

CLAIM ─────────> EXPLORE.claims

NEW_DIRECTION ─┬─> EXPLORE.new_directions
               └─> EVALUATE.corrective_directions   (dead path)

_PATTERN_ROW ──> PATTERNS.patterns
_OUTLINE_SECTION > FINALIZE.outline
_AXIS ─────────> EVALUATE.per_axis_intrinsics.*     (dead path)
```
