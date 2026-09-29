# Interactive Methodology — human-in-the-loop steering

**Status:** implemented (Phases 1–5). Offline-tested in `python3 -m src.selftest`.
**Goal:** let a human watch a live run and steer it — supply *directions*, *scope*, and
*assumptions* mid-flight — without breaking the harness's ownership of state or its determinism.

**Where it lives:** `src/steer.py` (`SteerEvent` + `SteerSource`), the steering hooks in
`src/orchestrator.py` (`_drain_steer` / `_apply_steer` / `_apply_human_verdict` / `_write_digest` /
`resume`), scope/assumption threading in `src/executors.py`, and the console in
`src/steer_server.py` + `src/ui/steer.html`. CLI: `--steer-inbox`, `--interactive`, `--resume`.

---

## 1. The core insight

The agent is already built for this. Three existing properties make human-in-the-loop nearly free:

1. **The harness owns all belief state; the LLM is stateless.** Every model call is
   `f(task, context) → JSON` (`executors.py`). The model never holds the ledger, so a *human*
   can be another writer to that ledger between rounds without racing the model.
2. **The ledger is fully serialized every round and rehydratable.** `Ledger.save` /
   `Ledger.from_json` (`ledger.py:575`, `:578`) already round-trip the entire belief state to
   `ledger.json`. Pausing and resuming is a matter of persisting the small amount of *runtime*
   state that lives outside the ledger.
3. **The loop has natural seams.** Top-of-round (`orchestrator.py:321`, before `_select_batch`)
   and `_checkpoint` (`:619`) are exactly where a human nudge should enter and be scored normally
   on the next wave.

**So the whole design is:** don't build a parallel "feedback system." Expose the *existing typed
mutation API* to a human, and drain human input at the loop seams that already exist.

Every kind of feedback maps onto something the code already does:

| User feedback | Existing primitive |
|---|---|
| "focus on X / explore this angle" | `add_direction(...)` with high promise (`ledger.py:172`) |
| "drop this line / dead end" | set `Direction.status = CLOSED` |
| "this matters more / less" | overwrite `Direction.promise` (frontier reranker reads it, `orchestrator.py:395`) |
| "the required fields are wrong" | edit `ledger.required_fields` (drives coverage + convergence) |
| "only post-2020 / clinical only" | **scope** → new `ledger.constraints[]`, injected into prompts |
| "assume EGFR-mutant NSCLC" | **assumption** → new `ledger.assumptions[]`, injected as a given |
| "keep going / good enough / +$20" | budget + convergence overrides |
| "I don't believe c12 / c4 is right" | `apply_verification(...)` — a **human VERIFY** (rare; gold) |

---

## 2. How humans actually steer

Observed usage (per project owner): a human **rarely runs verification**. They **give directions,
set scope, and state assumptions.** The intake therefore centers on three channels, and human
verification is a supported-but-secondary *gold* path.

The three dominant channels are distinct mechanisms — and, crucially, **scope and assumptions are
context, not claims.** They never pass through the provenance gate (`Claim.graduates()`,
`ledger.py:81`), so a human premise can never masquerade as a source-verified finding.

- **Directions** — new frontier questions or reprioritization. Become `Direction` objects with
  `origin="human"`; scored and selected by the normal frontier machinery on the next wave; never
  garbage-collected.
- **Scope** — filters on *what to search* ("only post-2020", "clinical, not preclinical"). Stored
  in `ledger.constraints[]`, injected as hard filters into the EXPLORE / VERIFY prompts and the
  coverage judge. Narrows the frontier without inventing content.
- **Assumptions** — premises to *take as given, without spending budget to verify* ("assume the
  population is EGFR-mutant NSCLC", "treat drug X as approved"). Stored in `ledger.assumptions[]`,
  injected into every executor prompt as "given — do not verify," and rendered in a **Given
  assumptions** section of the final report. Distinct from the glossary (definitions) and from
  scope (filters): assumptions shape *interpretation*, not just what is in range.

- **Verdicts (rare, gold).** When a human *does* rule on a claim, it routes through
  `apply_verification` with `origin="human"`: the claim is **pinned** (never re-verified, `$0`), and
  the `(raw LLM confidence → human outcome)` pair is fed to the calibrator as a **gold label**. This
  injects the real *negative* labels the mini-verifier almost never produces — directly relieving the
  "mini confirms everything → calibration is vacuous" problem tracked in
  [`FIX_PLAN_post_review.md`](../FIX_PLAN_post_review.md). Interactivity and calibration honesty
  reinforce each other.

---

## 3. Design principles

1. **Feedback is ledger mutations through the typed API** — never a second representation. A human
   direction is a `Direction`; a human verdict flows through `apply_verification`.
2. **Provenance + pinning.** Add `origin: "agent" | "human"` to `Direction`/`Claim`. Human-originated
   state is (a) never overwritten by the model, (b) never re-verified (no spend), (c) usable as gold
   for calibration and evaluation.
3. **Non-blocking by default; blocking opt-in.** Real runs are long and cost real money — freezing on
   `input()` every round is hostile. The primary mode is an **async inbox** drained each round;
   `--interactive` adds true pause points for supervised sessions.
4. **Everything logged → reproducible + auditable.** Every steer event appends to `steer.log`. A run
   replayed with the same steer log is deterministic. Human input becomes part of the run record.
5. **Convergence stays honest.** A human open direction naturally re-opens the loop (the guard at
   `orchestrator.py:322` and the `coverage≥.999 ∧ backlog==0` test at `:644`), so "keep digging here"
   needs no special case. "Good enough, stop" is an explicit `control` event, logged as such.

---

## 4. Architecture additions

### 4.1 `src/steer.py` — the intake layer

```python
@dataclass
class SteerEvent:
    directions_add:   list[dict]        # [{question_text, rationale, promise}]
    directions_drop:  list[str]         # direction ids → CLOSED
    directions_boost: dict[str, float]  # id → new promise
    fields_add:       list[str]         # extend required_fields
    fields_remove:    list[str]
    constraints:      list[str]         # SCOPE — search filters
    assumptions:      list[str]         # ASSUMPTIONS — givens, not verified
    claims_verdict:   list[dict]        # [{claim_id, verdict, note}] — human VERIFY (rare, gold)
    claims_pin:       list[str]         # accept as-is, never re-verify
    budget_delta:     float             # add/remove USD from the caps
    control:          str               # "continue" | "stop_after_round" | "finalize_now"
    note:             str               # free text, logged

class SteerSource(Protocol):            # pluggable
    def poll(self) -> list[SteerEvent]: ...

# Implementations:
#   FileInbox(path)   — read + truncate a JSON inbox (primary; UI/human append anytime)
#   ConsolePrompt()   — blocking stdin at checkpoints (--interactive)
#   CallbackSteer(fn) — programmatic / portal
#   NullSteer()       — default; exactly today's behavior
```

`steer.py` owns validation (unknown ids ignored with a warning, promises clamped to `[0,1]`,
verdicts restricted to the three states) and applying an event to a `Ledger` + `Budget`. It is pure
Python — **fully offline-testable**, no codex, no spend.

### 4.2 Orchestrator hooks

- `self.steer: SteerSource` (default `NullSteer` → behavior unchanged).
- `_drain_steer(phase)` — called at the **top of the run loop** (`orchestrator.py:321`, before
  `_select_batch`) and **after `_checkpoint`**. Polls the source, applies each event as ledger/budget
  mutations, logs to `steer.log`, and honors `control`.
- `_write_digest()` — writes `steer_request.md`: top open directions (with ids), recent claims,
  coverage / backlog, and "about to do next." This is what the watching human reads before nudging.
  Written each round in live mode; blocked-on in `--interactive` mode.

### 4.3 Resumability (the one real gap)

`run.json` persists snapshots + config but **not** the full runtime state. Extend `_save`
(`orchestrator.py:690`) to also persist:

- `calib_pairs`, `_calib_last_fit`, and enough to rebuild the fitted `Calibrator`
- `fdr.wealth`
- `verify_queue` (as claim ids)
- `round`, `uncovered_fields`, `explored_texts`, cost histories

Add `Orchestrator.resume(run_dir, cfg)` that rehydrates the ledger (`from_json` already exists) plus
this runtime state and continues the loop. This unlocks **run → stop → human edits → resume** across
process boundaries and is the foundation any UI needs.

### 4.4 Constraints + assumptions threading

Add `ledger.constraints: list[str]` and `ledger.assumptions: list[str]` (persisted in `to_json` /
`from_json`). Thread both into the `executors.py` prompts:

- EXPLORE / VERIFY / GROUND (research roles): a guardrail block —
  *"Scope (hard filters): …"* and *"Given assumptions (treat as true; do NOT spend budget
  verifying): …"*.
- `judge_coverage`: constraints narrow what counts as an ask.
- `finalize_report`: render a **Given assumptions** section so the report is honest about its premises.

One prompt edit per role; no schema changes.

---

## 5. Phasing (live-steering first)

- **Phase 1 — Foundation (prerequisite for everything).** Full runtime-state persistence + 
  `Orchestrator.resume`; `origin` field + pinning on `Direction`/`Claim`; `src/steer.py` with the
  `SteerEvent` schema and `SteerSource` implementations; `steer.log` audit trail. All offline-tested.
- **Phase 2 — Live steering (the primary mode).** `--steer-inbox path.json` drained non-blocking at
  the top of each round and after each checkpoint; `_write_digest()` → `steer_request.md`;
  `--interactive` blocking checkpoints as a variant. Human open directions auto-reset convergence.
- **Phase 3 — The three channels, threaded properly.** `constraints[]` and `assumptions[]` plumbed
  into the executor + judge prompts and the final report; directions already work via the ledger API.
  This is where the dominant feedback types become fully *effective*, not just *accepted*.
- **Phase 4 — Human-verdict gold path (rare).** `claims_verdict` → `apply_verification(origin=human)`:
  pin, `$0`, recalibrate as a gold label.
- **Phase 5 — Portal UI.** A ledger view (directions/claims + coverage) on the sliders-portal with
  steer buttons that POST to the inbox. A thin frontend over Phases 1–4.

**Cross-cutting:** every steer-event type applied offline in `selftest` (no codex, no spend), matching
how the rest of the system is tested.

---

## 6. Why this is safe

Nothing here fights the architecture; it exposes seams that already exist. The harness still owns the
state, still enforces provenance, still bounds the budget, and stays deterministic given its inputs —
human steer events simply *become* part of those inputs, logged and replayable. Scope and assumptions
are context that never graduates to a verified claim; only a rare, explicit human verdict touches the
claim graph, and when it does it is the highest-quality label in the system.
