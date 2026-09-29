# measure.py

This page walks `measure.py` top to bottom: the semantic-instrument layer that turns embeddings and LLM-judge output into the scalar terms the orchestrator needs — the EXPLORE context slice, the frontier promise function, and the coverage reducer. Nothing here does token matching; every "does this text mean the same thing" question is answered by an embedding cosine (`measure.py:1-7`).

Related: [embed.py](./embed.md), [metrics.py](./metrics.md), [orchestrator.py](./orchestrator.md), [ledger.py](./ledger.md), [Frontier selection](../architecture/frontier-selection.md), [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md)

## What the module is

The docstring frames it as the layer "that replaces every lexical proxy" (`measure.py:1`). Two instrument families feed it:

| Instrument | Source | Supplies |
|---|---|---|
| Embeddings | `embed.Embedder` | `cos(emb(·), emb(·))` terms: context selection, frontier relevance/novelty (`measure.py:3-5`) |
| LLM judges | `executors.judge_*` | discrete `covered(f)` / `q(d)` terms; their reducers live here (`measure.py:5-6`) |

Imports are minimal: `math`, plus `Embedder`, the ledger types (`Claim`, `Direction`, `Ledger`), and `PromiseWeights` from `metrics` (`measure.py:10-14`). The file is four functions and no classes.

## `select_context` — the EXPLORE context slice

Signature: `select_context(emb, direction, claims, limit=12) -> list[Claim]` (`measure.py:19-20`).

It returns the `limit` claims most relevant to a direction, ranked by embedding cosine of each claim's `text` against the direction's `question_text`:

- If `len(claims) <= limit`, return the list unchanged — no ranking, "no judgment needed" (`measure.py:23`).
- Otherwise call `emb.rank(direction.question_text, [c.text for c in claims])`, which returns `(index, cosine)` pairs sorted by similarity descending (`measure.py:25`, `embed.py:91-99`), and keep the top `limit` claims by index (`measure.py:26`).

```
claims (all) ──rank by cos(claim.text, direction.question_text)──▶ top-12 slice
```

Caller: `orchestrator.py:345` passes `self.ledger.all_claims()` and takes the default `limit=12` (it does not override it), then hands the slice to `executors.explore` as its context window (`orchestrator.py:350-351`). This is the mechanism that keeps a stateless EXPLORE call focused on the ledger claims that bear on its assigned direction rather than dumping the whole ledger.

## `score_frontier` — the promise function

Signature: `score_frontier(emb, ledger, open_dirs, explored_texts, under_covered, pw=PromiseWeights()) -> dict[str, float]` (`measure.py:31-33`). Returns a `direction.id -> promise` map.

The scored quantity (`measure.py:34`, `measure.py:59`):

```
promise(d) = w1·rel + w2·eig + w3·nov − w4·cost
```

Weights come from `PromiseWeights` (`metrics.py:26-32`), defaulting to:

| Weight | Default | Term |
|---|---|---|
| `w1` | 0.35 | relevance to the (under-covered-biased) question |
| `w2` | 0.30 | expected information gain |
| `w3` | 0.25 | novelty vs already-explored directions |
| `w4` | 0.10 | cost penalty |

### Setup (`measure.py:41-47`)

- Empty `open_dirs` short-circuits to `{}` (`measure.py:41-42`).
- The relevance query is biased toward gaps: `ledger.question`, with `"\nUnder-covered asks: " + "; ".join(under_covered)` appended only when `under_covered` is non-empty (`measure.py:43-44`). It is embedded once into `q_vec` via `emb.one` (`measure.py:45`).
- `explored_texts` is batch-embedded into `expl_vecs` (empty list when there are none), and every open direction's `question_text` into `d_vecs` (`measure.py:46-47`).

### Per-direction terms (`measure.py:50-59`)

| Term | Computation | Line |
|---|---|---|
| `rel` | `_cos(dv, q_vec)` — cosine of the direction vector to the biased question | `measure.py:51` |
| `eig` | mean of `1 − c.confidence` over the direction's produced claims; if it has none, fall back to its self-reported `d.promise` clamped to `[0,1]` | `measure.py:52-56` |
| `nov` | `1 − max cos(dv, ev)` over explored vectors; `default=0.0` (so `nov=1.0`) when nothing has been explored | `measure.py:57` |
| `cost` | `1 − exp(−max(0, d.est_cost) / 5.0)` — a saturating penalty in `[0,1)` | `measure.py:58` |

The EIG branch is the key nuance: a **visited** direction is scored by how uncertain its own claims still are (`1 − confidence`), so directions that produced confidently-settled claims lose promise; an **unvisited** direction has no claims yet, so it trusts the self-reported `d.promise` (`measure.py:53-56`). The `min(1.0, max(0.0, d.promise))` clamp guards against out-of-range self-reports.

The claim lookup filters to ids still present in the ledger: `[ledger.claims[cid] for cid in d.produced_claims if cid in ledger.claims]` (`measure.py:52`). `Direction.produced_claims`, `Direction.promise`, and `Direction.est_cost` are the ledger fields consumed here (`ledger.py:93-96`); `Claim.confidence` is the posterior mean belief (`ledger.py:70`).

Caller: `orchestrator._select_batch` calls `score_frontier(self.embedder, self.ledger, opens, self.explored_texts, self.uncovered_fields)` — note the positional `under_covered` argument is the orchestrator's `uncovered_fields` — and does not pass `pw`, so `PromiseWeights()` defaults apply (`orchestrator.py:384-385`). The resulting map is then optionally adjusted by a niche/hierarchy boost before batch selection (`orchestrator.py:388-395`).

## `coverage_from_judge` — the judge reducer

Signature: `coverage_from_judge(judge_fields, required_fields) -> tuple[float, list[str]]` (`measure.py:65`). It reduces the JSON that `executors.judge_coverage` emits into a coverage fraction plus the list of still-uncovered asks.

Logic (`measure.py:66-72`):

- `F = required_fields`. If `F` is empty, return `(1.0, [])` — vacuously fully covered (`measure.py:68-69`).
- `covered` = entries in `judge_fields` whose `"covered"` is truthy (`measure.py:70`).
- `uncovered` = the `"field"` string of each entry that is not covered, defaulting to `""` (`measure.py:71`).
- Return `(len(covered) / len(F), uncovered)` (`measure.py:72`).

Note the denominator is `len(required_fields)`, not `len(judge_fields)`: coverage is measured against the required asks, so a judge that omits a required field simply lowers the fraction rather than being ignored. Both `judge_fields` and its filtered comprehensions guard against `None` via `(judge_fields or [])` (`measure.py:70-71`).

Callers:
- `orchestrator._measure` calls it as `measure.coverage_from_judge(cj.get("fields"), self.ledger.required_fields)`, then stores the returned `uncovered` list into `self.uncovered_fields` — which is exactly what later feeds back into `score_frontier`'s bias term (`orchestrator.py:608-612`). Before the call it seeds `cov, uncovered = 0.0, list(self.ledger.required_fields)` so a failed judge (`cj is None`) leaves coverage at 0 with everything uncovered (`orchestrator.py:609-610`).
- `selftest.py:68` exercises it directly.

```
judge_coverage JSON ─▶ coverage_from_judge ─▶ (coverage float, uncovered[]) ─▶ self.uncovered_fields ─▶ score_frontier bias
```

## `_cos` — the cosine helper

`_cos(a, b)` (`measure.py:75-81`) is the standard dot / (‖a‖·‖b‖) cosine, returning `0.0` when either vector is falsy (empty/`None`) or when either norm is zero (`measure.py:76-77`, `measure.py:81`). It is the only similarity primitive `score_frontier` uses (`measure.py:51`, `measure.py:57`).

Worth flagging: `_cos`'s body is byte-for-byte identical to `embed.cosine` (`embed.py:102-108`) — the same guard, the same computation (the signatures differ in name/annotations: `_cos(a, b)` vs `cosine(a: list[float] | None, b: list[float] | None)`). `select_context`, `coverage_from_judge`, and other callers reach cosine through `Embedder` methods (`rank`, `one`, `embed`), while `score_frontier` embeds in bulk and then applies this local copy directly to the resulting vectors. The duplication is real; there is no shared helper between the two modules.

## Data-flow summary

```
                     ledger.question + uncovered_fields
                                   │  (bias)
                                   ▼
 open_dirs ─embed─▶ d_vecs ──▶ score_frontier ──▶ promise{d.id: float}
 explored_texts ─embed─▶ expl_vecs ▲                       │
                                   │                        ▼
                          (per-dir: rel/eig/nov/cost)   _select_batch → EXPLORE batch
                                                             │
 all_claims ──▶ select_context ──(top-12 slice)──▶ executors.explore
                                                             │ produces claims
 judge_coverage JSON ──▶ coverage_from_judge ──▶ uncovered_fields (loops back to bias)
```

Every arrow crossing a "meaning" boundary is an embedding cosine or a judge reducer — never a keyword match.
