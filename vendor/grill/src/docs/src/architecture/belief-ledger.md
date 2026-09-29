# The belief ledger

This page explains the typed graph that *is* the v2 blackboard: the objects it stores, why there is no `Entity` type, the provenance gate that lets a finding "graduate," and how claims link to the frontier and to one another. It is a concept-level tour; for the code walk see [../modules/ledger.md](../modules/ledger.md), and for the claim state machine see [../reference/claim-lifecycle.md](../reference/claim-lifecycle.md).

Related: [System overview](./overview.md) · [The orchestration loop](./orchestration-loop.md) · [Promotion and verification](./promotion-and-verification.md) · [Frontier selection](./frontier-selection.md) · [ledger.py](../modules/ledger.md) · [Claim lifecycle (reference)](../reference/claim-lifecycle.md)

## What the ledger is

The `Ledger` is the single piece of durable state in the system. The orchestrator owns it and is its only writer; the LLM (codex) never holds it. Every mutation is deterministic Python — no model call — which is precisely what lets the harness *enforce provenance*, *manage the frontier*, and *never forget a surfaced hit* (`ledger.py:1-11`, `ledger.py:129-130`).

Two first-class objects — `Direction` (the frontier) and `Claim` (grounded findings) — make up the graph, plus `SourceRef` for provenance and one prior container (`ledger.py:7-8`):

| Object | Role | Key |
| --- | --- | --- |
| `Direction` | A frontier question — a place the search *could* go next | `d{n}` |
| `Claim` | A grounded finding produced by exploring a direction | `c{n}` |
| `SourceRef` | Provenance for a claim (one citation) | dedup `key()` |
| `Hypothesis` | The seeded PRIOR (text + candidate answers) | — |

```
                     Ledger (the blackboard)
   ┌──────────────────────────────────────────────────────────┐
   │  directions: {d1, d2, …}        claims: {c1, c2, …}       │
   │                                                            │
   │     Direction ──produced_claims──▶ Claim ──evidence──▶ SourceRef
   │        ▲   │                         │  ▲                  │
   │        │   └──corrects_claim_id──────┘  │                  │
   │        └────────── direction_id ────────┘                  │
   │                                                            │
   │                     Claim ──parent_claim_id──▶ Claim       │
   │                       (lineage: refinement → ancestor)     │
   └──────────────────────────────────────────────────────────┘
```

## Why there is no `Entity` type

A deliberate omission. Instead of a rigid entity/relationship schema, grouping is done with free-form `aspects[]` string tags on each claim (`ledger.py:7-10`, `ledger.py:66`). This keeps the ledger equally usable for entity-ranking tasks and for open-problem / mechanism tasks: an "entity" is just an aspect tag that happens to be a name. All the group-level belief views (`niche_scores`, and the `synthesize` clustering) are computed by bucketing claims on their aspect strings rather than by walking a typed entity table.

## Direction — the frontier

A `Direction` is an open question the search can spend budget on. The ledger stores the whole frontier; the orchestrator decides which entries to explore.

| Field (`ledger.py:86-97`) | Meaning |
| --- | --- |
| `id` | `d{n}` |
| `question_text` | The question to explore |
| `parent_id` | Direction it was spawned from |
| `rationale` | Why it exists (seed / pattern / VERIFY defect) |
| `status` | Lifecycle state (default `OPEN`) |
| `promise` | Prior score used by frontier selection |
| `est_cost` | Estimated cost |
| `pool` | `"explore"` (default) vs. other pools |
| `produced_claims` | List of claim ids this direction yielded |
| `corrects_claim_id` | Claim this direction re-investigates (Component F) |

Direction statuses are named constants (`ledger.py:20`):

| Constant | Value |
| --- | --- |
| `OPEN` | `"OPEN"` |
| `EXPLORING` | `"EXPLORING"` |
| `CLOSED` | `"CLOSED"` |
| `EXPLORED` | `"EXPLORED"` |
| `PROMOTED` | `"PROMOTED"` |

Honest note: the ledger never *transitions* statuses during the loop — `add_direction` only defaults new directions to `OPEN` (`ledger.py:172-180`) and `open_directions` only reads `OPEN` (`ledger.py:419-420`). The other four statuses are constants the **orchestrator** transitions directions through; the ledger does not manage them in-loop, though `from_json` faithfully restores whatever status was persisted (`ledger.py:592`) and `to_json` serialises it (`ledger.py:570`). See [The orchestration loop](./orchestration-loop.md).

Directions enter the ledger three ways: `seed()` from the INIT probe (open questions + one confirm/refute direction per candidate answer, `ledger.py:154-170`), `add_directions()` from EXPLORE follow-ups (`ledger.py:182-193`), and `spawn_from_patterns()`, which turns a distilled cross-cutting pattern into a deeper frontier question (`ledger.py:202-212`).

## Claim — a grounded finding

A `Claim` is what EXPLORE returns: an assertion with provenance, optional extracted numbers, and a belief.

| Field (`ledger.py:61-76`) | Meaning |
| --- | --- |
| `id` | `c{n}` |
| `text` | The assertion |
| `stance` | `"supports"` (default) / opposing |
| `aspects` | Free-form grouping tags (the entity-less grouping key) |
| `numbers` | `{metric: value}` extracted quantities |
| `evidence` | `list[SourceRef]` — the provenance |
| `verification` | State machine value (below) |
| `confidence` | Posterior mean, the LLM's `P(true)` |
| `conf_lo` / `conf_hi` | ~90% credible interval; `-1` = absent |
| `direction_id` | Direction that produced this claim |
| `defect` | The fixable defect when `verification == error` |
| `correction_attempts` | Fix-loop counter (bounds re-verification) |
| `parent_claim_id` | Ancestor claim this one refines (lineage) |

Verification is a three-state machine plus the initial state (`ledger.py:21-22`); `error` is treated as a fixable defect rather than a refutation. The transitions are driven by `apply_verification` and detailed in [../reference/claim-lifecycle.md](../reference/claim-lifecycle.md).

| State | Value | Meaning |
| --- | --- | --- |
| `UNVERIFIED` | `"unverified"` | Ingested, not yet checked (default) |
| `CONFIRMED` | `"confirmed"` | VERIFY locked it |
| `REFUTED` | `"refuted"` | Literature gave no support |
| `ERROR` | `"error"` | Core supported, claim as written has a fixable defect |

## SourceRef — provenance

A `SourceRef` is one citation. Its two behavioural methods carry the weight:

- `resolvable()` — true iff it carries at least one real locator (`doi`, `pmid`, `pmc`, or `url`) (`ledger.py:38-40`). A title alone is not provenance.
- `key()` — a stable dedup identity: the first available locator, else the normalised title (`ledger.py:42-47`). The ledger indexes sources by this key (`_source_index`) so the same paper surfacing twice is recognised.

The `verified` flag is set only by VERIFY, when the author/venue match and the source resolves (`ledger.py:344-349`).

## The provenance gate — `graduates()`

This is the rule that makes the whole system honest. A claim *graduates* only if it has evidence and at least one of those sources is resolvable (`ledger.py:81-83`):

```
graduates(claim) := claim.has_evidence()
                    AND any(s.resolvable() for s in claim.evidence)
```

No claim reaches the headline answer without a resolvable source. `synthesize(only_confirmed=True)` — the final report — bodies only `CONFIRMED` claims that also `graduates()` (`ledger.py:493-494`). Sourced-but-unverified claims (budget ran out before VERIFY) are rendered in a separate, explicitly-labelled section by `unverified_graduated()` so nothing unverified is passed off as verified (`ledger.py:472-476`, `ledger.py:544-551`).

## How claims link to directions

The link is bidirectional and set at ingest time (`ledger.py:227-258`):

```
Direction d ──produced_claims: [c17, c18]──▶  claims c17, c18
      ▲                                              │
      └───────────── c17.direction_id = d ───────────┘
```

- Each ingested claim records `direction_id` = the direction it came from.
- The producing direction appends the new claim id to `produced_claims` (`ledger.py:255-256`).

This pairing is what makes `direction_scores()` cheap: a direction is scored purely from the claims it produced.

## How claims link to each other — lineage

When VERIFY finds a claim `error` or `refuted`, `apply_verification` spawns a **correction / re-investigation** direction whose `corrects_claim_id` points back at the offending claim (`ledger.py:332-373`). When *that* direction is later explored, `ingest` reads `corrects_claim_id`, sets the new claim's `parent_claim_id` to the ancestor, and inherits its `correction_attempts` budget so the fix loop stays bounded even across EXPLORE-regenerated refinements (not just re-verifications of the same id) (`ledger.py:247-251`).

```
c5  (refuted)
  └─ spawns Direction dN  (corrects_claim_id = c5)
        └─ EXPLORE ingests c9  (parent_claim_id = c5,
                                 correction_attempts inherited from c5)
```

`lineage(claim)` walks `parent_claim_id` to return the ancestor chain, so a refinement can carry its ancestor's refutation forward as skeptical context (`ledger.py:261-270`).

Honest note: `apply_verification`'s inline NOTE still calls cross-refinement lineage "Component F, deferred" (`ledger.py:358-359`), but `ingest` already sets `parent_claim_id` (`ledger.py:247-251`) — the comment is stale relative to the code. Separately, the reader `lineage()` is **exercised only by `selftest.py`; the orchestration loop never calls it.** The lineage *links* are built; the loop does not yet consume them.

## Group-level belief views

Two aggregation views turn per-claim states into group beliefs. Both are recomputed from the claims on each call, so they track belief as evidence arrives.

| View | Groups by | Wired? |
| --- | --- | --- |
| `direction_scores()` | Direction → its `produced_claims` | Yes — called by the orchestrator (`orchestrator.py:391`) |
| `niche_scores()` | Primary aspect (`aspects[0]`) across all claims | **No caller** — defined but the loop never invokes it |

Each view computes the same three signals per group (`ledger.py:376-416`):

| Signal | Definition |
| --- | --- |
| `strength` | `confirmed / (confirmed + refuted)` pass-rate |
| `thin` | Explored but nothing confirmed yet |
| `contested` | `≥2` checked and `0.34 ≤ strength ≤ 0.66` |

`direction_scores()` is the **primary** hierarchy (direction → claims) and is what frontier selection reads to prioritise a thin/contested direction's follow-ups. `niche_scores()` is a cross-cutting aspect view that `direction_scores()`'s docstring describes as a promotion-diversity tie-breaker (`ledger.py:403-404`) — niche_scores's own docstring (`ledger.py:376-380`) does not — but no module calls it, so that tie-breaker is not currently in effect.

## Corroboration — raising a backlog claim

`corroborate()` lets independent sources for the same assertion raise a weak-but-true claim's posterior (diminishing returns, capped, never lowers confidence) so it can resurface into promotion (`ledger.py:304-321`). It **is** wired: the orchestrator does its own embedding-cosine matching and calls `ledger.corroborate` directly (`orchestrator.py:481-498`).

The ledger's own same-assertion helpers — `same_assertion()` and `find_corroborators()` (`ledger.py:277-302`) — are **not** on that path; they are exercised only by `selftest.py`. The orchestrator supplies its own matching rather than routing through them.

## Unwired helpers (honest inventory)

These methods are defined and unit-tested but the orchestration loop never calls them. Treat their behaviour as available-but-dormant, not as running policy:

| Method | `ledger.py` | Intended role | Status |
| --- | --- | --- | --- |
| `niche_scores` | 376-397 | Cross-cutting aspect belief / promotion tie-breaker | No caller |
| `same_assertion` | 277-287 | Shared-source / near-dup matcher | selftest only |
| `find_corroborators` | 289-302 | Collect corroborating claims | selftest only |
| `lineage` | 261-270 | Read ancestor chain for skeptical context | selftest only |
| `top_k_open` | 422-424 | Best-first frontier expansion helper | No caller (orchestrator selects) |
| `draft` | 478-481 | `synthesize` wrapper for in-loop EVALUATE | No caller |
| `aspect_texts` | 431-436 | Raw aspect strings for novelty embedding | No caller |
| `patterns_md` | 214-224 | Markdown of stored patterns | selftest only |

By contrast, the wired write/read path the loop actually uses is: `seed` / `add_directions` / `spawn_from_patterns` / `add_patterns` → `ingest` → `apply_verification` → `corroborate` → `direction_scores` → `synthesize` + `references_md`, with `confirmed_claims` read by [metrics.py](../modules/metrics.md) and `graduated_claims` read by [executors.py](../modules/executors.md).

## Persistence

The whole graph round-trips to JSON via `to_json()` / `from_json()` (`ledger.py:563-610`), so a run can be rehydrated for finalize, inspection, or reuse. `SourceRef.verified` and the full claim lineage are preserved across the round-trip.
