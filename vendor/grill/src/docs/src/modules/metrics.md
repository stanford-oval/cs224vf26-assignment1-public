# metrics.py

This page walks `metrics.py` top to bottom: the `PromiseWeights` tunable used by frontier selection, the two ledger-derived scores (`confab_rate`, `quality`), and the `Snapshot` dataclass plus its `build_snapshot` constructor that the orchestrator records at every checkpoint. The whole module is 93 lines and holds no state of its own — every function is a pure reducer over a `Ledger`.

Related: [ledger.py](./ledger.md), [measure.py](./measure.md), [orchestrator.py](./orchestrator.md), [selftest.py](./selftest.md), [The orchestration loop](../architecture/orchestration-loop.md), [Frontier selection](../architecture/frontier-selection.md), [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md).

## What this module is

The module docstring (`metrics.py:1-17`) states the design intent: checkpoint scoring is "deliberately SIMPLE" — two scored dimensions plus one progress signal, all plain counts driven by a single LLM judge (coverage). The three quantities are:

| Quantity | Formula (per docstring) | Meaning |
|---|---|---|
| Coverage | `asks_answered / total_asks` | share of the explicit asks a judge marks answered |
| Quality | `confirmed / (confirmed + refuted)` | VERIFY pass-rate; the unchecked claims are the backlog |
| Progress | `(Δ asks_answered + Δ confirmed) / Δ$` | are we still buying answers per dollar |
| Answeredness | `Coverage × Quality` | share of the question answered **and** verified |

The docstring's key rule (`metrics.py:12-13`): `Progress ≈ 0` means "done" only when `Coverage` is already complete; `Progress ≈ 0` with `Coverage < 1` is the stall / shallow-saturation failure, and the loop should dig deeper rather than stop. That rule is enforced in `build_snapshot`'s `stalled` flag and consumed by `orchestrator._checkpoint` (`orchestrator.py:635-644`).

The docstring also lists what was removed versus an older design (`metrics.py:15-16`): Chao1 richness, the coverage-saturation matrix, embedding recall, the forward `q(d)` judge, the composite `S` with `ω` weights, the `β` half-credit, and `Δ_t`-of-`S`. None of those exist in this file.

Imports are minimal: `dataclass`/`field` and, from `ledger`, the `Ledger` type plus the `CONFIRMED` and `REFUTED` status string constants (`metrics.py:20-22`). Those constants are the literals `"confirmed"` and `"refuted"` defined in `ledger.py:22`.

## `PromiseWeights` — frontier-selection weights (`metrics.py:25-32`)

A plain (mutable) dataclass of four float weights. Its docstring is explicit that it is **unrelated to checkpoint scoring** — it lives here only to keep direction-selection tunable in one place. It is consumed by `measure.score_frontier`, not by anything else in this module.

| Field | Default | Role in `promise(d)` |
|---|---|---|
| `w1` | `0.35` | relevance to under-covered question (embedding cosine) |
| `w2` | `0.30` | ÊIG — uncertainty the direction resolves |
| `w3` | `0.25` | novelty vs already-explored directions (embedding distance) |
| `w4` | `0.10` | cost penalty |

The consumer computes `promise(d) = w1·rel + w2·eig + w3·nov − w4·cost` (`measure.py:59`; docstring formula at `measure.py:34`). `score_frontier` takes `pw: PromiseWeights = PromiseWeights()` as a defaulted argument (`measure.py:33`), so with the shipped defaults relevance is weighted highest and cost is a light subtractive penalty. Nothing in the repository overrides these weights — the default instance is the only one constructed.

## `confab_rate(ledger) -> float` (`metrics.py:35-42`)

A diagnostic, not a scored quantity. It measures the fraction of *checked* claims whose cited attribution did not survive VERIFY's source re-fetch.

```
checked = claims where verification ∈ {CONFIRMED, REFUTED}      (metrics.py:38)
if no checked claims → return 0.0                                (metrics.py:39-40)
bad     = count of checked claims with ANY evidence ref s.verified == False   (metrics.py:41)
return bad / len(checked)                                        (metrics.py:42)
```

`s.verified` is the per-source boolean that VERIFY sets from `author_venue_matches AND source_resolvable` (`ledger.py:36`, `ledger.py:345`, `ledger.py:349`). So a claim counts as a confabulation if the loop graded it (CONFIRMED or REFUTED) yet at least one of its cited sources failed source re-fetch. `confab_rate` is called from the orchestrator in two places: the VERIFY-drain log line (`orchestrator.py:603`) and inside `build_snapshot`, which stores it on the snapshot's `confab` field.

## `quality(ledger) -> float` (`metrics.py:45-50`)

The VERIFY pass-rate — of the claims adversarially checked, what fraction held up.

```
conf = count of claims with verification == CONFIRMED            (metrics.py:48)
ref  = count of claims with verification == REFUTED              (metrics.py:49)
return conf / (conf + ref) if (conf + ref) else 0.0             (metrics.py:50)
```

The docstring notes the boundary case: `0.0` when nothing has been checked yet, because correctness is still unknown (the unchecked population is the backlog, tracked separately). Unverified and error-state claims are excluded from both numerator and denominator, so quality is strictly a ratio over the graded population. `selftest.py:65` asserts `quality(L) == 1.0` for an all-confirmed ledger.

## `Snapshot` — one checkpoint's recorded metrics (`metrics.py:53-70`)

A plain dataclass; one instance is appended to `orchestrator.snapshots` (typed `list[metrics.Snapshot]`, `orchestrator.py:164`) at each checkpoint. Fields, in declaration order:

| Field | Type | Meaning |
|---|---|---|
| `cost` | `float` | cumulative spend at this checkpoint (`budget.spent`) |
| `coverage` | `float` | asks answered / total asks (from the coverage judge) |
| `quality` | `float` | confirmed / (confirmed + refuted) |
| `answeredness` | `float` | `coverage * quality` |
| `progress` | `float` | (Δ covered + Δ confirmed) / Δ cost; 0 at the first checkpoint |
| `backlog` | `int` | promoted-but-not-yet-checked claims (the verify queue length) |
| `new_claims` | `int` | claims added since the previous checkpoint |
| `n_claims` | `int` | total claims in the ledger |
| `n_confirmed` | `int` | count CONFIRMED |
| `n_refuted` | `int` | count REFUTED |
| `n_covered` | `int` | asks answered, as a count (`round(coverage * n_asks)`) |
| `n_asks` | `int` | total required-field asks |
| `n_open` | `int` | directions with `status == "OPEN"` |
| `confab` | `float` | `confab_rate(ledger)` |
| `stalled` | `bool` (default `False`) | progress ≈ 0 **and** coverage < 1 → shallow saturation |
| `uncovered` | `list` (default `[]`) | the asks still unanswered |

Only `stalled` and `uncovered` carry defaults (`metrics.py:69-70`); every other field is required positionally/by keyword from `build_snapshot`.

## `build_snapshot(...) -> Snapshot` (`metrics.py:73-93`)

The single constructor for `Snapshot`. Signature (`metrics.py:73-75`):

```
build_snapshot(ledger, cost, *, coverage, uncovered, backlog,
               prev: Snapshot | None, new_claims, progress_eps) -> Snapshot
```

`coverage`/`uncovered` are supplied by the caller (not computed here); `prev` is the previous snapshot or `None` at the first checkpoint; `progress_eps` is the stall threshold from config.

Data flow inside the function:

```
n_conf ← len(ledger.confirmed_claims())                          (metrics.py:76)
n_ref  ← count claims with verification == REFUTED               (metrics.py:77)
q      ← quality(ledger)                                         (metrics.py:78)
n_asks ← len(ledger.required_fields)                             (metrics.py:79)
n_cov  ← round(coverage * n_asks)          # coverage → integer  (metrics.py:80)

progress:                                                        (metrics.py:81-84)
   if prev is not None AND cost > prev.cost:
        ((n_cov − prev.n_covered) + (n_conf − prev.n_confirmed)) / (cost − prev.cost)
   else:
        +inf  if prev is None           (first checkpoint: unknown → treat as progressing)
        0.0   otherwise                 (prev exists but no spend since → no progress)

stalled ← (progress <= progress_eps) AND (coverage < 0.999)      (metrics.py:85)
```

Two subtleties worth calling out:

- **First-checkpoint progress is `+inf` internally but stored as `0.0`.** Line 84 sets `progress = float("inf")` when `prev is None`, and line 88 rewrites it to `0.0` before it lands on the `Snapshot` (`progress=(0.0 if progress == float("inf") else progress)`). The `+inf` exists only so the `stalled` test on line 85 evaluates `False` at the first checkpoint (`inf <= progress_eps` is false) — the loop is never declared stalled before it has spent anything. The recorded `progress` value is nonetheless `0.0`.
- **`coverage < 0.999`** (line 85) is the "not fully covered" test; the mirror `coverage >= 0.999` gate is what the orchestrator uses for convergence (`orchestrator.py:649`). The `0.999` fudge avoids float-equality against `1.0`.

The returned `Snapshot` (`metrics.py:86-93`) fills the remaining count fields directly: `n_claims = len(ledger.claims)`, `n_open` counts directions whose `status == "OPEN"` (`metrics.py:91`), and `confab = confab_rate(ledger)` (`metrics.py:92`). `uncovered` is defensively copied via `list(uncovered)`.

### How the orchestrator drives it

`build_snapshot` is called once per checkpoint from `orchestrator._measure` (`orchestrator.py:614-617`). The orchestrator first runs the `judge_coverage` executor, reduces its JSON to `(cov, uncovered)` via `measure.coverage_from_judge` (`orchestrator.py:611`), then passes `coverage=cov`, `backlog=len(self.verify_queue)`, `prev=self.snapshots[-1] if self.snapshots else None`, `new_claims=self._new_claims`, and `progress_eps=self.cfg.progress_eps`. The snapshot is appended to `self.snapshots` and `self._new_claims` is reset to 0 (`orchestrator.py:618-619`).

The `stalled` flag is consumed at `orchestrator.py:635`: when stalled and explore budget remains, the loop runs the `patterns` executor to distil cross-cutting abstractions and spawn deeper frontier directions rather than converging. Convergence (`orchestrator.py:648-650`) requires `required_fields` non-empty, `coverage >= 0.999`, `backlog == 0`, and `progress <= progress_eps` together — `progress ≈ 0` alone never converges, matching the module docstring's key rule.

`selftest.py:76` exercises `build_snapshot` directly with a synthetic ledger, confirming the constructor is covered by the self-test.

## Wiring summary

| Symbol | Defined | Called by | Live? |
|---|---|---|---|
| `PromiseWeights` | `metrics.py:25` | `measure.score_frontier` default arg (`measure.py:33`) | yes (defaults only; never overridden) |
| `confab_rate` | `metrics.py:35` | `orchestrator.py:603`, `build_snapshot` (`metrics.py:92`) | yes |
| `quality` | `metrics.py:45` | `build_snapshot` (`metrics.py:78`), `selftest.py:65` | yes |
| `Snapshot` | `metrics.py:53` | `orchestrator.snapshots` (`orchestrator.py:164`); returned by `build_snapshot` | yes |
| `build_snapshot` | `metrics.py:73` | `orchestrator._measure` (`orchestrator.py:614`), `selftest.py:76` | yes |

Every function in the module is reached by the running loop; there is no dead code here.
