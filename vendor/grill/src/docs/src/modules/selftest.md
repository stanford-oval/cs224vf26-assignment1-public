# selftest.py

This page walks `selftest.py`, the offline correctness harness for src. It exercises the deterministic core — ledger provenance gate, promotion, three-state verification, lineage propagation, corroboration re-scoring, coverage/quality/snapshot reducers, and synthesis — with no codex calls and no embeddings, so most features that ship "offline-verified only" are checked here.

Related: [ledger.py](./ledger.md) · [orchestrator.py](./orchestrator.md) · [measure.py](./measure.md) · [metrics.py](./metrics.md) · [Promotion and verification](../architecture/promotion-and-verification.md) · [Claim lifecycle (reference)](../reference/claim-lifecycle.md)

## What it is, and what it is not

The module docstring (`selftest.py:1-7`) states the boundary explicitly: it exercises the DETERMINISTIC core (ledger provenance gate, promotion, VERIFY application, correctness counts, composite, synthesis) with no codex and no embeddings. Semantic instruments (embeddings + judges) are validated live by the real run, not here.

Concretely that means:

| Covered here (offline, deterministic) | Not covered here |
| --- | --- |
| Ledger seeding, direction creation, promise ordering | Real codex executor calls |
| Claim ingest + provenance/graduation gate | Embedding cosine (only a **caller-supplied** cosine is passed in) |
| Three-state VERIFY routing (confirmed / error / refuted) | Live judge calls (coverage/corroboration judges) |
| Correction budget, lineage, corroboration re-scoring | Orchestration loop control flow, budget/FDR brake |
| Coverage/quality/snapshot reducers | HTML inspectors, portal staging |
| Synthesis rendering (dedup, refs, confirmed-only) | Anything requiring network or a model |

There are no test classes and no assertion framework: the whole harness is one `main()` function using bare `assert` statements (`selftest.py:19-169`). Any failed assert raises `AssertionError` and aborts; a clean run prints `SELFTEST OK` and returns `0`.

## How to run

```
python3 -m src.selftest
```

Invoked as `__main__`, the module runs `raise SystemExit(main())` (`selftest.py:172-173`), so the process exit code is `main()`'s return value — `0` on success (`selftest.py:169`). On success it prints the `SELFTEST OK` banner (`selftest.py:166`) and a one-line snapshot summary (`selftest.py:167-168`):

```
SELFTEST OK
  claims=2 confirmed=1 coverage=0.67 quality=1.00 answeredness=0.67
```

Imports are relative (`from . import metrics, measure`; `from .ledger import Ledger, CONFIRMED`, `selftest.py:10-11`), so it must be run as a module inside the package, not as a bare script.

## The `_src` helper

`_src(title, author, doi=None, pmid=None)` (`selftest.py:14-16`) builds a source dict with the fields the ledger expects, filling fixed values for the rest:

| Field | Value |
| --- | --- |
| `title` | argument |
| `authors` | `[author]` (single-element list) |
| `year` | `2024` |
| `journal` | `"J"` |
| `doi` | argument (default `None`) |
| `pmid` | argument (default `None`) |
| `pmc` | `None` |
| `url` | `None` |
| `quote` | `"q"` |

A source with a `doi` is what makes a claim "sourced" and therefore able to graduate; a source with all identifiers `None` is unsourced. Both cases are used deliberately below. (The `_src` signature also accepts a `pmid`, which by its shape would presumably serve as an alternate graduation path, but no test in this file builds a `pmid`-only source, so that path is not exercised here.)

## `main()` walkthrough

The body is a straight-line script. The stages below run in file order.

```
seed ─► Component G (structured candidates) ─► ingest + provenance gate
      ─► promotion filter ─► VERIFY(confirmed) ─► quality reducer
      ─► coverage reducer ─► snapshot ─► patterns + spawn ─► synthesize
      ─► Component D (3-state routing) ─► Component F (lineage + corroboration)
      ─► print summary
```

### 1. Seeding and direction count (`selftest.py:20-27`)

A `Ledger` is constructed with a pancreatic-cancer research question and three `required_fields` (`selftest.py:22`). `L.seed(...)` is called with four seed inputs: two `open_questions`, a `prior_hypothesis`, and one `candidate_answers` entry given as a **bare string** (`"ctDNA KRAS mutations"`). The assert `len(L.directions) == 3` (`selftest.py:27`) confirms that these four inputs yield three directions — the two open questions and the candidate answer each spawn a direction, while the `prior_hypothesis` spawns none — and that the legacy string form of a candidate answer is still accepted.

### 2. Component G — structured candidate answers (`selftest.py:30-39`)

A fresh ledger `Lg` is seeded with `candidate_answers` as **dicts** carrying `answer`, `confidence`, and `aspect`. Two are supplied, confidence `0.9` and `0.1`. The directions are indexed by their generated `question_text`, which takes the form `"Confirm or refute candidate answer: <answer>"` (`selftest.py:35-36`). Assertions:

| Assert | What it proves |
| --- | --- |
| `hi.promise > lo.promise` (`:37`) | Higher prior confidence yields a higher `promise` on the spawned direction — prior confidence prioritises the seeded direction |
| `len(Lg.prior_candidates) == 2 and prior_candidates[0]["confidence"] == 0.9` (`:38`) | Structured candidates are retained on the ledger in order |
| `Ledger.from_json(Lg.to_json()).prior_candidates[0]["answer"] == "high-conf answer"` (`:39`) | `prior_candidates` survive a JSON serialization round-trip |

### 3. Ingest and the provenance gate (`selftest.py:41-52`)

Back on `L`, the first open direction is fetched via `L.open_directions()[0]` (`selftest.py:41`) and two claims are ingested against it:

- A **sourced** methylation claim with numbers `AUC=0.92`, `n=198`, and an evidence item that has a `doi` (`selftest.py:43-47`).
- An **unsourced** fragmentomics claim: empty `numbers`, empty `evidence` (`selftest.py:48-49`).

Assertions (`selftest.py:51-52`):

| Assert | What it proves |
| --- | --- |
| `len(added) == 2` | Both claims are ingested regardless of sourcing |
| `added[0].graduates() and not added[1].graduates()` | The **provenance gate**: only a claim backed by a resolvable source can graduate; the sourceless claim cannot |

### 4. Promotion filter (`selftest.py:54-55`)

Promotion is expressed as a plain comprehension: `[c for c in added if c.confidence >= 0.6 and c.graduates()]` (`selftest.py:54`). Only the sourced claim (confidence `0.8`) passes both the confidence floor and the graduation gate; the assert `len(promoted) == 1` (`selftest.py:55`) fixes that. This mirrors, in miniature, the promotion condition the orchestrator applies — see [Promotion and verification](../architecture/promotion-and-verification.md).

### 5. VERIFY application — the confirmed path (`selftest.py:57-65`)

`L.apply_verification(promoted[0], {...})` is called with a payload marking `confirmed: True`, `author_venue_matches: True`, `source_resolvable: True`, no corrected numbers, and a `corrected_source` matching the original (`selftest.py:57-60`). Assertions:

| Assert | What it proves |
| --- | --- |
| `corrective is None` (`:61`) | A confirmed verification returns **no** follow-up (corrective) direction |
| `promoted[0].verification == CONFIRMED` (`:61`) | The claim's state is set to `CONFIRMED` |
| `promoted[0].evidence[0].verified` (`:62`) | The evidence item is flagged verified |
| `abs(metrics.quality(L) - 1.0) < 1e-9` (`:65`) | `metrics.quality` computes the VERIFY pass-rate: `1 confirmed / (1 confirmed + 0 refuted) = 1.0`, with no LLM involved |

### 6. Coverage reducer (`selftest.py:67-73`)

`measure.coverage_from_judge(field_verdicts, required_fields)` is fed three per-field verdicts — two `covered: True`, one `covered: False` for `"validation readiness"` — over the three `required_fields`. It returns `(coverage_fraction, uncovered_list)`. The assert `abs(cov - 2/3) < 1e-9 and uncovered == ["validation readiness"]` (`selftest.py:73`) pins both the fraction (covered/total) and the exact uncovered-field list. See [measure.py](./measure.md).

### 7. Snapshot assembly (`selftest.py:76-80`)

`metrics.build_snapshot` is called with the live cost, the computed coverage, the uncovered list, `backlog=0`, `prev=None` (first checkpoint), `new_claims=2`, and `progress_eps=0.02` (`selftest.py:76-77`). Assertions on the returned snapshot:

| Field | Asserted value | Line |
| --- | --- | --- |
| `snap.coverage` | `== cov` (2/3) | `:78` |
| `snap.quality` | `== 1.0` | `:78` |
| `snap.answeredness` | `≈ cov * 1.0` (coverage × quality) | `:79` |
| `snap.n_confirmed` | `== 1` | `:80` |
| `snap.n_claims` | `== 2` | `:80` |
| `snap.n_covered` | `== 2` | `:80` |

The inline comment (`selftest.py:75`) notes the intended interpretation: coverage is incomplete and progress is ~0 at the first checkpoint, so the run is **not** flagged stalled at the first checkpoint. Note that no assertion actually checks a "stalled" flag here — the comment describes context, not a verified property. See [metrics.py](./metrics.md).

### 8. Patterns and frontier spawning (`selftest.py:82-90`)

`L.add_patterns([...])` stores one abstract pattern (with `direction`, `hypothesis`, `support`, `sources`, `novelty`, `abstraction` fields) as a belief and returns the created rows (`selftest.py:83-86`). `L.spawn_from_patterns(rows)` then turns those rows into new frontier directions (`selftest.py:88`). Assertions:

| Assert | What it proves |
| --- | --- |
| `len(spawned) == 1 and len(L.directions) == n_before + 1` (`:89`) | Each pattern spawns exactly one new direction (deepen) |
| `"marker fusion" in L.patterns_md() and L.references_md()` (`:90`) | `patterns_md()` renders output containing the abstraction (`"marker fusion"`); `references_md()` is only asserted non-empty (truthy), not checked to contain the abstraction |

### 9. Synthesis (`selftest.py:92-98`)

`L.synthesize(only_confirmed=True)` renders the final answer (`selftest.py:93`). Assertions verify four properties at once:

| Assert | Property |
| --- | --- |
| `"AUC=0.92" in ans and "## References" in ans` (`:94`) | Numbers render and a numbered References section is emitted |
| `"unsourced fragmentomics" not in ans` (`:95`) | Sourceless claims never leak into the answer |
| `ans.count("198-patient PDAC cohort") == 1` (`:97`) | A multi-aspect claim renders **once** (dedup), not once per aspect tag |
| `"_(also:" in ans` (`:98`) | Secondary aspects of that claim appear as inline tags |

### 10. Component D — three-state verification routing (`selftest.py:100-135`)

A separate ledger `L2` and direction `d2` are created (`selftest.py:102-103`). Two local helpers reduce boilerplate:

- `_mkclaim(tag, conf)` (`selftest.py:105-108`) ingests one sourced claim (DOI `10.9/<tag>`) at confidence `conf` and returns it.
- `_v(verdict, **kw)` (`selftest.py:110-115`) builds a VERIFY payload with the given `verdict`, `confirmed` derived as `verdict == "confirmed"`, and defaults that callers override via `**kw`.

The routing matrix this section proves:

| Verdict payload | Resulting state | Follow-up direction | Lines |
| --- | --- | --- | --- |
| `error` (within budget) | `ERROR`; `defect` carried; `correction_attempts` incremented | `"Correct and resubmit …"` (bounded) | `:118-121` |
| `error` (budget exhausted) | downgraded to `REFUTED` | — | `:123-126` |
| `refuted` | `REFUTED` | `"Re-investigate …"` | `:128-130` |
| legacy payload (no `verdict`, `confirmed: True`) | `CONFIRMED` | `None` | `:132-135` |

Detail on the correction-budget exhaustion (`selftest.py:119-126`): with `max_corrections=2`, the first `error` sets `correction_attempts == 1` and returns a corrective direction; the second sets `correction_attempts == 2` and keeps state `ERROR`; the **third** error sets `correction_attempts == 3` and flips the state to `REFUTED` ("fix budget exhausted → refuted"). The legacy branch (`selftest.py:132-135`) proves a payload lacking the `verdict` field still routes via the `confirmed` boolean. States `ERROR` and `REFUTED` are imported from `.ledger` at `selftest.py:101`.

### 11. Component F — lineage propagation and corroboration (`selftest.py:137-164`)

Same-assertion matching, lineage inheritance, and corroboration re-scoring, all on `L2`:

**Lineage across regeneration (`selftest.py:138-150`).** A `base` claim errors (attempt 1) and yields a correction direction `cdir` whose `corrects_claim_id == base.id` (`selftest.py:139-140`). A `refined` claim ingested on `cdir` inherits lineage: `refined.parent_claim_id == base.id` and `refined.correction_attempts == 1` — the attempt budget is inherited across regeneration, not reset (`selftest.py:142-144`). `L2.lineage(refined) == [base]` (`selftest.py:145`). Two further errors on `refined` tick the inherited budget to `2` and then to `REFUTED` (`selftest.py:147-150`), proving the cross-regeneration bound prevents infinite fix loops.

**Same-assertion matching (`selftest.py:152-156`).**

| Assert | Property |
| --- | --- |
| `same_assertion(s1, s2)` where `s2.evidence = list(s1.evidence)` (`:152-155`) | Two claims sharing a resolvable source are the same assertion |
| `not same_assertion(s1, ind)` (`:155`) | Different sources → not the same assertion |
| `same_assertion(s1, ind, cosine=0.95)` (`:156`) | A **caller-supplied** near-duplicate cosine also matches (no embeddings computed in-test) |
| `s2 in find_corroborators(s1)` (`:156`) | Same-source claims are found as corroborators |

**Corroboration re-scoring (`selftest.py:158-160`).** `L2.corroborate(weakc, [ind])` raises a weak claim (confidence starts at `0.30`) because `ind` brings a **new independent source**: the return is `> 0` and `weakc.confidence > 0.30` (`:159`). `L2.corroborate(weakc, [weakc])` returns `0.0` — self is not a new source, so no bump (`:160`). The inline note (`selftest.py:158`) records the intended bound: corroboration is capped and never lowers confidence.

**Serialization round-trip (`selftest.py:161-164`).** `Ledger.from_json(L2.to_json())` preserves the new lineage fields: `parent_claim_id` on the refined claim and `corrects_claim_id` on the correction direction survive (`selftest.py:162-164`).

### 12. Summary print (`selftest.py:166-169`)

On reaching the end, `main()` prints `SELFTEST OK` and a formatted snapshot line drawn from the `snap` built in stage 7 (`n_claims`, `n_confirmed`, `coverage`, `quality`, `answeredness`), then returns `0`.

## Coverage gaps to be aware of

The harness is thorough on the ledger's deterministic mechanics, but by design it does not touch:

- **Executor calls / codex** — see [The executor roles](../architecture/executor-roles.md) and [executors.py](./executors.md); these run only in a live session.
- **Embeddings** — `same_assertion` is tested only with a *caller-supplied* `cosine`; the real cosine path in [embed.py](./embed.md) is not exercised.
- **The orchestration loop, budget accounting, and the FDR brake** — none of the control flow in [orchestrator.py](./orchestrator.md) or [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md) is driven here.
- **Live judges** — coverage and corroboration are tested through their *reducers* with hand-built verdicts, not through actual judge executor output.

Because these are validated only by real runs, `selftest.py` is the last line of automated defense for everything it *does* cover; a change to the ledger, promotion, verification routing, lineage, or synthesis logic should keep this passing.
