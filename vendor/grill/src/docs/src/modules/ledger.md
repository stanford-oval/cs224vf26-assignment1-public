# ledger.py

Low-level reference for `src/ledger.py`, the belief ledger: the typed, in-memory blackboard that the orchestrator owns and mutates deterministically (no model call happens inside this file). This page walks the module top to bottom — the four dataclasses, the module-level constants and helpers, the `Ledger` container, and every method — with `file:line` citations and honest notes on which helpers the orchestration loop never calls.

Related: [The belief ledger](../architecture/belief-ledger.md) · [orchestrator.py](./orchestrator.md) · [schemas.py](./schemas.md) · [Claim lifecycle](../reference/claim-lifecycle.md) · [Promotion and verification](../architecture/promotion-and-verification.md) · [docs index](../README.md)

---

## 1. What lives here

The module docstring (`ledger.py:1-11`) states the contract: the orchestrator owns this state; the LLM never holds it, and every mutation is deterministic Python. Two objects are first-class — `Direction` (the frontier) and `Claim` (grounded findings) — plus `SourceRef` for provenance. There is deliberately **no** `Entity` type; grouping is done with free-form `aspects[]` string tags (`ledger.py:7-10`).

Nothing in this file makes a network call, an embedding call, or a codex call. Cosine similarity, when needed, is passed *in* by the caller (`same_assertion`, `find_corroborators`) so the ledger stays embedding-agnostic and offline-testable (`ledger.py:280-282`).

## 2. Module-level constants

| Constant | Value | Domain | `ledger.py` |
|---|---|---|---|
| `OPEN` | `"OPEN"` | Direction status | :20 |
| `EXPLORING` | `"EXPLORING"` | Direction status | :20 |
| `CLOSED` | `"CLOSED"` | Direction status | :20 |
| `EXPLORED` | `"EXPLORED"` | Direction status | :20 |
| `PROMOTED` | `"PROMOTED"` | Direction status | :20 |
| `UNVERIFIED` | `"unverified"` | Claim verification state | :22 |
| `CONFIRMED` | `"confirmed"` | Claim verification state | :22 |
| `REFUTED` | `"refuted"` | Claim verification state | :22 |
| `ERROR` | `"error"` | Claim verification state | :22 |

The four claim states are the three-state verdict of Component D plus `unverified` — `error` is a fixable defect, treated distinctly from a refutation (`ledger.py:21`). The ledger itself only ever **assigns** `OPEN` to a direction (`Direction.status` default at `ledger.py:92`, set on creation at `ledger.py:176`); the other four statuses are written by the orchestrator (`EXPLORING`/`CLOSED`/`EXPLORED` at `orchestrator.py:338,360,365`, `PROMOTED` at `orchestrator.py:532`).

## 3. Dataclasses

### 3.1 `SourceRef` (`ledger.py:25-58`)

Provenance for a single citation.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `title` | `str` | `""` | Source title |
| `authors` | `list[str]` | `[]` | Author list |
| `year` | `int?` | `None` | Publication year |
| `journal` | `str?` | `None` | Venue |
| `doi` | `str?` | `None` | Locator |
| `pmid` | `str?` | `None` | Locator |
| `pmc` | `str?` | `None` | Locator |
| `url` | `str?` | `None` | Locator |
| `quote` | `str?` | `None` | Supporting quote |
| `verified` | `bool` | `False` | Set true only when VERIFY checked it against the actual source |

Methods:

- `resolvable()` (`:38-40`) — true iff at least one of `doi`, `pmid`, `pmc`, `url` is present. This is the provenance gate's atom: a claim cannot graduate without a resolvable source.
- `key()` (`:42-47`) — dedup identity. Returns the first present locator (`doi` → `pmid` → `pmc` → `url`), lower-cased and stripped; falls back to the normalized `title` when no locator exists. Two sources with no locators but the same title collide.
- `from_json(d)` (`:49-58`) — classmethod constructor tolerant of missing keys; coerces `authors` to a list and `verified` to bool.

### 3.2 `Claim` (`ledger.py:61-83`)

A grounded finding.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `id` | `str` | — | Minted id `c{n}` |
| `text` | `str` | — | The assertion |
| `stance` | `str` | `"supports"` | supports / refutes / etc. |
| `aspects` | `list[str]` | `[]` | Free-form niche tags; `aspects[0]` is the primary niche |
| `numbers` | `dict[str,object]` | `{}` | Extracted metric→value pairs |
| `evidence` | `list[SourceRef]` | `[]` | Provenance |
| `verification` | `str` | `UNVERIFIED` | One of the four claim states |
| `confidence` | `float` | `0.0` | Posterior mean: LLM point belief P(true) |
| `conf_lo` | `float` | `-1.0` | Low end of ~90% credible interval; `-1` = absent |
| `conf_hi` | `float` | `-1.0` | High end; `-1` = absent |
| `direction_id` | `str?` | `None` | Direction that produced it |
| `defect` | `str` | `""` | Component D: the specific fixable defect when `verification == ERROR` |
| `correction_attempts` | `int` | `0` | How many times this claim / its lineage has been sent for correction |
| `parent_claim_id` | `str?` | `None` | Component F: the claim this one refines / re-investigates |

Methods:

- `has_evidence()` (`:78-79`) — non-empty `evidence`.
- `graduates()` (`:81-83`) — the provenance gate: has evidence **and** at least one piece is `resolvable()`. Only graduating claims appear in the confirmed body or reference list.

### 3.3 `Direction` (`ledger.py:86-97`)

A frontier node — an open question to investigate.

| Field | Type | Default | Meaning |
|---|---|---|---|
| `id` | `str` | — | Minted id `d{n}` |
| `question_text` | `str` | — | The question |
| `parent_id` | `str?` | `None` | Parent direction (tree structure) |
| `rationale` | `str` | `""` | Why this direction exists |
| `status` | `str` | `OPEN` | One of the five direction statuses |
| `promise` | `float` | `0.0` | Frontier priority score |
| `est_cost` | `float` | `0.0` | Estimated cost |
| `pool` | `str` | `"explore"` | Budget pool |
| `produced_claims` | `list[str]` | `[]` | Ids of claims this direction produced |
| `corrects_claim_id` | `str?` | `None` | Component F: the claim this direction corrects / re-investigates |

### 3.4 `Hypothesis` (`ledger.py:100-103`)

The PRIOR. Just `text: str` and `candidate_answers: list[str]`. Stored on the ledger as `self.prior`; the richer per-candidate structure (with confidence/aspect) lives separately in `self.prior_candidates` (see §5).

### 3.5 Module-level parsing helpers (`ledger.py:106-126`)

- `_numbers_to_dict(pairs)` (`:106-113`) — folds the schema's `[{metric, value}]` array into a `{metric: value}` dict, dropping rows with an empty metric.
- `_ca_text(c)` (`:116-118`) — extracts a candidate answer's text, accepting a plain string (legacy) or a `{answer, ...}` object.
- `_ca_conf(c)` (`:121-122`) — confidence, defaulting to `0.5` for a legacy string or a missing field.
- `_ca_aspect(c)` (`:125-126`) — aspect string, `""` for a legacy string.

## 4. `Ledger` container — construction and id minting

`Ledger.__init__(question)` (`ledger.py:132-143`) sets up all state:

| Attribute | Type | Purpose |
|---|---|---|
| `question` | `str` | The research question |
| `required_fields` | `list[str]` | Fields the answer must cover (set by orchestrator at `orchestrator.py:240`) |
| `glossary` | `dict[str,dict]` | Grounded term definitions (set by orchestrator at `orchestrator.py:261`) |
| `prior` | `Hypothesis` | The PRIOR hypothesis + flat candidate texts |
| `prior_candidates` | `list[dict]` | Component G: `{answer, confidence, aspect}` per candidate |
| `directions` | `dict[str,Direction]` | The frontier, keyed by id |
| `claims` | `dict[str,Claim]` | All claims, keyed by id |
| `patterns` | `list[dict]` | Cross-cutting abstractions |
| `_dir_seq`, `_claim_seq` | `int` | Monotonic id counters |
| `_source_index` | `dict[str,str]` | source key → first claim id that cited it (dedup) |

Id minting: `_new_dir_id()` (`:146-148`) returns `d1, d2, …`; `_new_claim_id()` (`:150-152`) returns `c1, c2, …`. Ids are never reused within a run.

## 5. Seeding (INIT) — `seed()` and `add_direction*`

`seed(open_questions, prior_hypothesis, candidate_answers)` (`ledger.py:155-170`) turns INIT output into initial frontier nodes:

```
seed()
 ├─ prior            ← Hypothesis(prior_hypothesis, [text of each candidate])
 ├─ prior_candidates ← [{answer, confidence, aspect}] per candidate  (Component G)
 ├─ for each open_question q:
 │     add_direction(q, promise=0.6, rationale="seed: open question from PRIOR")
 └─ for each candidate answer c:
       add_direction("Confirm or refute candidate answer: <c>",
                     promise = min(1.0, 0.5 + 0.4*conf))
```

Candidate answers may be plain strings (legacy) or `{answer, confidence, aspect}` objects; the parsing helpers normalize both (`:159-162`). Each candidate becomes a hypothesis to confirm-or-refute, with promise scaled by its self-reported prior confidence (`:168-170`).

Direction creators:

- `add_direction(question_text, *, parent_id, rationale, promise=0.5, est_cost=1.0, pool="explore", corrects_claim_id=None)` (`:172-180`) — mints an id, builds the `Direction`, stores it, returns it. The single entry point for every new frontier node.
- `add_directions(new_dirs, *, parent_id, priority_boost=0.0)` (`:182-193`) — bulk-add from schema dicts; skips rows with empty `question_text`, adds `priority_boost` to each `promise` (capped at 1.0). This is what the orchestrator calls to expand the frontier (`add_directions` is used in `orchestrator.py`; the singular `add_direction` is called only internally and in `selftest.py`).

## 6. Cross-cutting patterns

- `add_patterns(rows)` (`:196-200`) — stores rows that have a non-empty `"pattern"` key; returns the fresh ones. Called from `orchestrator.py`.
- `spawn_from_patterns(rows, promise=0.75)` (`:202-212`) — turns each pattern's `"direction"` into a new frontier `Direction`, using the pattern's `"hypothesis"`/`"abstraction"` as the rationale. This is how abstraction digs the loop deeper. Called from `orchestrator.py`.
- `patterns_md()` (`:214-224`) — renders patterns as Markdown. Called only from `selftest.py`.

## 7. Ingest (EXPLORE results) — `ingest()`

`ingest(raw_claims, direction_id=None)` (`ledger.py:227-258`) is the write path for EXPLORE output. For each raw claim dict:

```
ingest(raw_claims, direction_id)
 └─ per raw claim rc:
      skip if rc.text is empty
      evidence  = [SourceRef.from_json(s) for s in rc.evidence]
      cid       = _new_claim_id()
      Claim(text, stance, aspects (stripped, non-empty),
            numbers = _numbers_to_dict(rc.numbers),
            evidence, confidence = rc.confidence,
            conf_lo = rc.conf_low, conf_hi = rc.conf_high,
            direction_id)
      ── Component F lineage inheritance ──
      d = directions[direction_id]
      if d.corrects_claim_id in claims:
          claim.parent_claim_id      = ancestor.id
          claim.correction_attempts  = ancestor.correction_attempts   # inherit fix budget
      claims[cid] = claim
      for s in evidence: _source_index.setdefault(s.key(), cid)
      directions[direction_id].produced_claims.append(cid)
```

Note the JSON key mismatch handled here: the schema field is `conf_low`/`conf_high` but the dataclass field is `conf_lo`/`conf_hi` (`:241`). The Component-F block (`:247-251`) is what keeps a correction loop bounded across EXPLORE-regenerated refinements: a claim born on a correction direction inherits the ancestor's `correction_attempts`, not just re-verifications of the same claim id. The `_source_index` uses `setdefault`, so it records the **first** claim to cite a given source, but the ledger does not currently drop duplicate claims on that basis — dedup by source is available (`_shares_source`) but ingest keeps every non-empty-text claim. (The in-code docstring at `ledger.py:228` — "Dedups by source+text." — is stale/aspirational: `ingest` performs no dedup and appends every non-empty-text claim. Trust the behavior described here, not that docstring line.)

## 8. Claim identity helpers (Component F)

These four helpers implement claim-identity reasoning. **Only `corroborate` is on the live loop path** (see §9); the other three are exercised solely by `selftest.py` and are not called from `orchestrator.py`.

| Helper | `ledger.py` | Called by the loop? |
|---|---|---|
| `lineage(claim)` | :261-270 | **No** — only `selftest.py:145` |
| `_shares_source(a, b)` | :272-275 | Internal only (used by `same_assertion`) |
| `same_assertion(a, b, cosine, thresh=0.88)` | :277-287 | **No** — only `selftest.py:155-156` |
| `find_corroborators(claim, cosines, thresh=0.88)` | :289-302 | **No** — only `selftest.py:156` |

- `lineage(claim)` (`:261-270`) — walks `parent_claim_id` upward, nearest ancestor first, with a `seen` set to guard cycles. Intended to let a refinement carry forward its ancestor's refutation/defect as skeptical context. The orchestration loop never calls it; the lineage it relies on (`parent_claim_id`) is still populated by `ingest`, so the data exists even though this reader is dormant.
- `_shares_source(a, b)` (`:272-275`) — true iff the two claims share a resolvable source key. Non-resolvable sources are ignored.
- `same_assertion(a, b, cosine=None, thresh=0.88)` (`:277-287`) — true if same id, or shared resolvable source, or caller-supplied `cosine >= thresh`. The caller owns the embedder; `cosine=None` means "source match only." Documented as the hook for dedup and Component B re-scoring.
- `find_corroborators(claim, cosines=None, thresh=0.88)` (`:289-302`) — scans all other claims, calling `same_assertion` with the per-claim cosine from the `cosines` map. Returns claims asserting the same thing via an independent source or near-duplicate text.

**Why the loop bypasses `find_corroborators`:** the orchestrator does its own cosine ranking through the embedder and calls `corroborate` directly (`orchestrator.py:490-498`), so `find_corroborators`/`same_assertion` are never invoked at runtime. They remain as tested library surface, not dead-but-untested code.

## 9. `corroborate()` — the one live identity helper

`corroborate(claim, corroborators, per_source=0.04, cap=0.95)` (`ledger.py:304-321`) raises a claim's confidence when corroborators bring **independent** sources for the same assertion:

```
own      = {resolvable source keys already on `claim`}
new_srcs = {resolvable keys from corroborators} − own
if not new_srcs: return 0.0
before          = claim.confidence
claim.confidence = max(before, min(cap, before + per_source * len(new_srcs)))
return claim.confidence - before          # the delta actually applied
```

Only sources the claim does not already cite count; the bump has diminishing returns (linear in count but capped at `cap=0.95`) and can never lower confidence (the `max(before, …)`). Returns the delta applied.

Live use (`orchestrator.py:479-501`): after new claims arrive, the orchestrator builds a backlog of `UNVERIFIED` graduating claims, ranks each fresh claim's text against them with the embedder, and for any pair clearing `cfg.corroborate_thresh` calls `corroborate(backlog[i], [nc], per_source=cfg.corroborate_per_source)`. A positive delta counts as a "bump." This is the Component B posterior bump that drives Component C resurfacing: a weak-but-true backlog claim gains evidence, its posterior rises, and it can resurface into promotion.

Relevant config defaults (`orchestrator.py:107-109`): `corroborate_enabled=True`, `corroborate_thresh=0.88`, `corroborate_per_source=0.04`.

## 10. Verification (VERIFY results)

### 10.1 `_verdict()` (`ledger.py:324-330`)

Normalizes a VERIFY payload to one of `confirmed` / `error` / `refuted`. If the payload carries a `verdict` string in that set, it is used; otherwise it falls back to the legacy boolean `confirmed` field (true → `CONFIRMED`, false → `REFUTED`). A legacy payload can therefore never produce `ERROR`.

### 10.2 `apply_verification()` (`ledger.py:332-373`)

Routes a VERIFY result and returns an optional follow-up `Direction`. It is called from `orchestrator.py`.

Step 1 — refresh belief regardless of verdict (`:336-349`):
- `claim.confidence` ← `v.confidence` (falls back to current).
- If `v` has `conf_low`, refresh `conf_lo`/`conf_hi`.
- Merge `v.corrected_numbers` into `claim.numbers`.
- If `v.corrected_source` is a dict with a title, build a `SourceRef`, mark it `verified` only when both `author_venue_matches` and `source_resolvable` are true, and **prepend** it (removing any existing source with the same key). Otherwise, stamp `verified` on every existing source using the same two flags.

Step 2 — route on the three-state verdict:

```
verdict = _verdict(v)
├─ CONFIRMED → claim.verification = CONFIRMED;  return None   (lock, no follow-up)

claim.defect = v.defect|v.refutation           (set for BOTH non-confirmed verdicts, :355)

├─ ERROR     → correction_attempts += 1
│              if correction_attempts <= max_corrections (default 2):
│                   claim.verification = ERROR
│                   return add_direction("Correct and resubmit: <text>",
│                                        promise=0.70, corrects_claim_id=claim.id)
│              else: fall through to REFUTED   (fix budget exhausted)
└─ REFUTED   → claim.verification = REFUTED
               return add_direction("Re-investigate (refuted): <text>",
                                     promise=0.65, corrects_claim_id=claim.id)
```

`max_corrections` (default `2`, `:332`) bounds the peeking guard. The in-code note at `:357-359` is candid: this counter bounds re-verification of the **same** claim id; bounding across EXPLORE-regenerated refinements needs the lineage inheritance that `ingest` performs (`:247-251`). Both correction directions set `corrects_claim_id`, which is exactly what `ingest` reads to propagate lineage — closing the loop between §7 and here. An exhausted `ERROR` falls through and is treated as `REFUTED` (`:368-373`).

## 11. Group-level belief scoring

### 11.1 `niche_scores()` (`ledger.py:376-397`) — NOT wired

Groups claims by primary aspect (`aspects[0]`, or `"(none)"`) and tallies confirmed/refuted/unverified per niche, then computes `strength = confirmed/(confirmed+refuted)`, `thin = confirmed == 0`, and `contested = checked >= 2 and 0.34 <= strength <= 0.66`. **This method is never called** — no caller exists anywhere in the codebase; it survives only as a reference in `direction_scores`'s docstring (`:403-404`). The live hierarchy boost uses `direction_scores`, not this.

### 11.2 `direction_scores()` (`ledger.py:399-416`) — the wired hierarchy

The primary two-level hierarchy (direction → its produced claims). For each direction, gathers its `produced_claims`, counts `CONFIRMED`/`REFUTED`/`UNVERIFIED`, and returns per-direction:

| Key | Formula |
|---|---|
| `n` | number of produced claims present in `claims` |
| `confirmed` / `refuted` / `unverified` | verdict tallies |
| `strength` | `confirmed / (confirmed + refuted)`, or `0.0` if none checked |
| `thin` | `n > 0 and confirmed == 0` (explored but nothing confirmed) |
| `contested` | `checked >= 2 and 0.34 <= strength <= 0.66` |

Live use (`orchestrator.py:390-395`): when `cfg.niche_boost > 0` (default `0.15`, `orchestrator.py:113`), an open direction whose **parent** came back `thin` or `contested` gets its promise boosted — the frontier is steered toward following up inconclusive investigations.

## 12. Frontier selection and views

| Method | `ledger.py` | Called by the loop? |
|---|---|---|
| `open_directions()` | :419-420 | Yes — `orchestrator.py:323,381` |
| `top_k_open(k, score)` | :422-424 | **No** — no caller anywhere |
| `all_claims()` | :426-429 | Yes — `orchestrator.py:345` (feeds `measure.select_context`) |
| `aspect_texts()` | :431-436 | **No** — no caller anywhere |
| `confirmed_claims()` | :439-440 | Internal (§13) + `metrics.py` |
| `graduated_claims()` | :442-443 | Internal (§13) + `executors.py` |
| `aspects()` | :445-449 | **No** — no caller anywhere |
| `references_md(only_confirmed=False)` | :451-470 | Yes — `orchestrator.py:677` |
| `unverified_graduated()` | :472-476 | Internal via `synthesize` |
| `draft()` | :478-481 | **No** — no caller anywhere |

- `open_directions()` (`:419-420`) — directions with `status == OPEN`.
- `top_k_open(k, score)` (`:422-424`) — best-first: sort open directions by a `Direction→float` score fn, take top `k`. Documented as §5 frontier expansion, but **no code calls it**; the orchestrator does its own `sorted(opens, …)` (`orchestrator.py:399`).
- `all_claims()` (`:426-429`) — all claims as a list (insertion order, i.e. oldest first; the docstring says "newest first" but `dict.values()` preserves insertion order — treat the ordering note as aspirational, not enforced). Live use: called every round on the EXPLORE path (`orchestrator.py:345`, `ctx = measure.select_context(self.embedder, d, self.ledger.all_claims())`) to feed context selection — load-bearing, not dormant.
- `aspect_texts()` (`:431-436`) — union of raw, case-preserved aspect strings. Uncalled.
- `confirmed_claims()` (`:439-440`) — claims with `verification == CONFIRMED`.
- `graduated_claims()` (`:442-443`) — claims where `graduates()` is true.
- `aspects()` (`:445-449`) — lower-cased union of aspect tags. Uncalled.
- `references_md(only_confirmed=False)` (`:451-470`) — a deduped bibliography from the graduated (or, if `only_confirmed`, confirmed) claims. Dedups by source key, keeps only resolvable sources, sorts by first author, and renders numbered entries with a `✓` when `verified`. Appended to the finalize report so the reference list is guaranteed accurate.
- `unverified_graduated()` (`:472-476`) — sourced claims still `UNVERIFIED` (budget ran out before VERIFY). Surfaced by `synthesize` in a clearly labelled section, never mixed into the confirmed body.
- `draft()` (`:478-481`) — a lightweight render (`synthesize(only_confirmed=False, include_unverified=False)`), documented as the in-loop EVALUATE input. **No code calls `ledger.draft()`** — the orchestrator tracks its own `self.last_draft`, and EVALUATE's draft is fed by other means, so this method is currently dead.

## 13. Finalize — `synthesize()`

`synthesize(*, only_confirmed=True, heading="", include_unverified=True)` (`ledger.py:484-560`) is the deterministic report renderer. Called from `orchestrator.py:684` (final answer) and `selftest.py`.

```
body = confirmed & graduated claims          if only_confirmed
     = all claims                            otherwise

cite(c)          → assign each source a 1-based ref number on first sight, return "[n, m]"
render_clusters  → cluster claims by aspect, but render each claim ONCE
                   under its LARGEST cluster (primary aspect); secondary aspects
                   shown inline as "(also: …)". Non-confirmed claims tagged "(state)".
                   Members sorted by descending confidence; numbers rendered "k=v".

layout:
  # heading (or question)
  ## Prior hypothesis            (if prior.text)
  <clusters of body>   OR   "_No claims survived verification within budget._"
  if only_confirmed and include_unverified and unverified_graduated():
     --- ## Sourced findings pending verification  <clusters of those>
  ## References                  (numbered, ✓ on verified)
```

The clustering logic (`:511-534`) is the subtle part: a claim tagged with several aspects is assigned to the aspect whose cluster is largest (`primary` map at `:519-522`) and printed only once there, so multi-aspect claims are never duplicated. Confirmed claims carry no state tag; any other state is shown as `_(state)_` (`:530`). Reference numbers are allocated lazily by `cite` as claims are rendered, so `## References` lists exactly the sources actually cited, in first-cited order.

## 14. JSON (de)serialization

- `to_json()` (`ledger.py:563-573`) — serializes `question`, `required_fields`, `glossary`, `prior` (`asdict`), `prior_candidates`, `directions` (each `asdict`), `claims` (each via `_claim_json`), and `patterns`. Note: the volatile `_source_index`, `_dir_seq`, and `_claim_seq` are **not** persisted — a rehydrated ledger loses its dedup index and its id counters reset to 0, so ids minted after a reload can collide with existing `d*`/`c*` ids. In practice `from_json` is used for finalize/inspection/reuse (`:580`), not for resuming mutation.
- `save(path)` (`:575-576`) — writes `to_json()` as indented UTF-8 JSON.
- `from_json(d)` (`:578-610`) — classmethod rehydrator. Rebuilds `Hypothesis`, each `Direction`, and each `Claim` (re-reading `SourceRef`s and re-stamping their `verified` flag from the JSON). It reads the dataclass field names `conf_lo`/`conf_hi` here (`:607`) — matching what `to_json` wrote, distinct from the `conf_low`/`conf_high` schema keys that `ingest` consumes.
- `_claim_json(c)` (`:613-616`) — module-level helper: `asdict(c)` with `evidence` re-serialized as a list of `asdict(SourceRef)`.

## 15. Summary — what is live vs. dormant

| Wired into the orchestration loop | Present but never called by the loop |
|---|---|
| `seed`, `add_directions`, `add_patterns`, `spawn_from_patterns` | `add_direction` (singular; internal + selftest only) |
| `ingest` | `lineage`, `same_assertion`, `find_corroborators` (selftest only) |
| `corroborate` | `niche_scores`, `aspect_texts`, `aspects` (no caller) |
| `apply_verification`, `_verdict` | `top_k_open`, `draft`, `patterns_md` (no live caller) |
| `direction_scores`, `open_directions`, `all_claims` | |
| `references_md`, `synthesize` (which reaches `unverified_graduated`) | |
| `to_json` / `save` / `from_json` | |

The dormant identity helpers (`lineage`, `same_assertion`, `find_corroborators`) and `niche_scores` are the tested-but-unwired Component F/C surface: the data they read (`parent_claim_id`, `aspects`) is still populated on the live path, so wiring them in later requires no schema change.
