# Claim lifecycle (reference)

Formal reference for the `Claim` verification state machine: its states, every
transition and its trigger, and the exact side effects the orchestrator and ledger
apply on each transition. All logic lives in `ledger.py` (`Claim`,
`Ledger.apply_verification`, `Ledger.corroborate`) and `orchestrator.py`
(`_promote`, `_drain_verify_pool`, `_rescore_corroboration`).

Related: [Promotion and verification](../architecture/promotion-and-verification.md) · [The belief ledger](../architecture/belief-ledger.md) · [ledger.py](../modules/ledger.md) · [Config knobs (reference)](./config-reference.md) · [Executor output schemas (reference)](./schemas-reference.md)

## States

Verification states are string constants defined at `ledger.py:22`
(`UNVERIFIED, CONFIRMED, REFUTED, ERROR`). They live on `Claim.verification`
(`ledger.py:69`, default `UNVERIFIED`).

| State | Constant / literal | Meaning | Terminal? | Re-verifiable? | In promotion pool? |
|-------|-------------------|---------|-----------|----------------|--------------------|
| unverified | `UNVERIFIED = "unverified"` | Ingested from EXPLORE, not yet checked by VERIFY. Initial state of every claim. | No | n/a (awaiting first verify) | Yes, if `graduates()` |
| confirmed | `CONFIRMED = "confirmed"` | VERIFY found literature support; source-verified. Headline-answer eligible. | **Yes (locked)** | No | No |
| error | `ERROR = "error"` | Literature supports the core but the claim as written has a fixable defect (`Claim.defect`). Transient. | No (until fix budget exhausted) | Via a spawned correction direction that regenerates a *new* claim | No (the `error` claim itself is not re-pooled) |
| refuted | `REFUTED = "refuted"` | Literature gives no support / contradicts, OR the error fix budget was exhausted. | Effectively terminal for this claim id | Only through a spawned re-investigation direction producing a new claim | No |

`PROMOTED` is a **direction** status (`ledger.py:20`), not a claim state. It is set
on a `Direction` when one of its claims is pushed onto the verify queue
(`orchestrator.py:530-532`). It is listed here only to disambiguate: promotion is a
transition of the *direction*, while verification transitions the *claim*.

### Promotion (pre-state, not a verification state)

A claim is *promoted* (moved from the resurfacing pool onto `verify_queue`) by
`Orchestrator._promote` (`orchestrator.py:504`). The eligible pool
(`_promotable_pool`, `orchestrator.py:469`) is exactly:

- `verification == UNVERIFIED`, **and**
- `graduates()` is true (`has_evidence()` and at least one `resolvable()` source;
  `ledger.py:81`), **and**
- not already on `verify_queue`.

Side effect on promotion: for each promoted claim, the producing direction's status
is set to `PROMOTED` (`orchestrator.py:531-532`). No claim field changes at
promotion time; `verification` stays `UNVERIFIED` until VERIFY returns.

## State diagram

```
                      ingest (EXPLORE result)
                              │
                              ▼
                     ┌───────────────┐
   corroboration ───▶│  UNVERIFIED   │◀── initial state (Claim.verification default)
   bump (conf only,  └───────┬───────┘
   never lowers)             │  promote → verify_queue (direction → PROMOTED)
                             │  apply_verification(v)
              ┌──────────────┼───────────────────────────┐
              │              │                            │
      verdict=confirmed  verdict=error               verdict=refuted
              │              │                            │
              ▼              ▼                            ▼
        ┌──────────┐   attempts += 1                ┌──────────┐
        │CONFIRMED │   ┌───────────────┐            │ REFUTED  │
        │ (locked, │   │ attempts ≤ 2? │            │ spawn    │
        │ terminal)│   └──┬─────────┬──┘            │ "Re-     │
        └──────────┘      │yes      │no             │ investi- │
                          ▼         ▼               │ gate"    │
                     ┌────────┐  falls through      │ direction│
                     │ ERROR  │  to REFUTED  ──────▶│(promise  │
                     │ spawn  │                     │ 0.65)    │
                     │"Correct│                     └────┬─────┘
                     │ and    │                          │
                     │resubmit"│  corrects_claim_id       │ corrects_claim_id
                     │direction│─────────┐                │
                     │(promise │         │                │
                     │ 0.70)   │         ▼                ▼
                     └─────────┘   EXPLORE re-runs the correction/re-investigation
                                   direction → ingest() mints a NEW claim that
                                   inherits parent_claim_id + correction_attempts,
                                   starting again at UNVERIFIED.
```

Note: the correction/re-investigation loop does **not** re-verify the same claim
object. It spawns a direction; when EXPLORE runs it, `ingest` creates a *new*
`UNVERIFIED` claim linked to the ancestor (`parent_claim_id`) and carrying forward
its `correction_attempts` (`ledger.py:247-251`).

## `Claim` fields touched by the lifecycle

Full dataclass at `ledger.py:61-83`.

| Field | Type / default | Set at | Mutated by |
|-------|----------------|--------|-----------|
| `verification` | str = `UNVERIFIED` (`ledger.py:69`) | ingest | `apply_verification` (`ledger.py:353,362,369`) |
| `confidence` | float = 0.0 (`ledger.py:70`) | ingest (from EXPLORE) | **overwritten** by VERIFY (`ledger.py:336`); bumped by `corroborate` (`ledger.py:320`) |
| `conf_lo` / `conf_hi` | float = -1.0 (`ledger.py:71-72`) | ingest | refreshed by VERIFY if `conf_low` present (`ledger.py:337-338`) |
| `numbers` | dict (`ledger.py:67`) | ingest | `.update()`d with `corrected_numbers` from VERIFY (`ledger.py:339-341`) |
| `evidence` | list[SourceRef] (`ledger.py:68`) | ingest | replaced/marked `verified` by VERIFY (`ledger.py:342-349`) |
| `defect` | str = "" (`ledger.py:74`) | — | set from VERIFY `defect`/`refutation` on error or refuted (`ledger.py:355`) |
| `correction_attempts` | int = 0 (`ledger.py:75`) | inherited on ingest (`ledger.py:251`) | `+= 1` on each error verdict (`ledger.py:360`) |
| `parent_claim_id` | Optional[str] (`ledger.py:76`) | set on ingest from a correction direction (`ledger.py:250`) | — |
| `direction_id` | Optional[str] (`ledger.py:73`) | ingest (`ledger.py:242`) | — |

## Transitions

The single transition function is `Ledger.apply_verification(claim, v, max_corrections=2)`
(`ledger.py:332`). It is called from `Orchestrator._drain_verify_pool`
(`orchestrator.py:578`) and from the INIT prior probe via `_probe_apply`
(`orchestrator.py:302`), both passing `max_corrections=cfg.correction_max_attempts`
(default **2**, `orchestrator.py:101`). The verdict is parsed by `_verdict`
(`ledger.py:324-330`): it reads `v["verdict"]` if it is one of
`confirmed/error/refuted`, otherwise falls back to the legacy boolean
`v["confirmed"]` (→ `confirmed` else `refuted`).

**Side effects applied to every verdict, before branching** (`ledger.py:336-349`):

1. `confidence` is **overwritten** with `v["confidence"]` (falls back to the current
   value if absent) — `ledger.py:336`. This replaces the EXPLORE self-report with
   VERIFY's posterior mean. The pre-overwrite raw value is captured by the caller
   first as the calibration label (`orchestrator.py:575`).
2. `conf_lo`/`conf_hi` refreshed from `v["conf_low"]`/`v["conf_high"]` if `conf_low`
   is present (`ledger.py:337-338`).
3. `numbers` updated with `_numbers_to_dict(v["corrected_numbers"])` (`ledger.py:339-341`).
4. Evidence: if `v["corrected_source"]` is a dict with a title, it is prepended and
   its `verified` flag set from `author_venue_matches AND source_resolvable`
   (`ledger.py:342-346`); otherwise every existing source's `verified` flag is set
   from the same two booleans (`ledger.py:347-349`).

| # | From | Trigger (parsed verdict) | To | Spawned direction | Direction promise / pool / `corrects_claim_id` | Other side effects |
|---|------|--------------------------|----|--------------------|-----------------------------------------------|--------------------|
| T1 | unverified | `verdict == confirmed` (`ledger.py:352`) | **confirmed** | none — returns `None` (`ledger.py:354`) | — | `verification = CONFIRMED` (`ledger.py:353`); claim is now locked/terminal |
| T2 | unverified | `verdict == error` **and** `correction_attempts ≤ max_corrections` (`ledger.py:356-361`) | **error** | `"Correct and resubmit: {text}"` (`ledger.py:364-367`) | promise **0.70**, pool `explore`, `corrects_claim_id = claim.id`, `parent_id = claim.direction_id` | `correction_attempts += 1` (`ledger.py:360`); `defect` set (`ledger.py:355`); `verification = ERROR` (`ledger.py:362`) |
| T3 | unverified | `verdict == error` **and** `correction_attempts > max_corrections` (fix budget exhausted; falls through, `ledger.py:368-369`) | **refuted** | `"Re-investigate (refuted): {text}"` (`ledger.py:371-373`) | promise **0.65**, pool `explore`, `corrects_claim_id = claim.id`, `parent_id = claim.direction_id` | `correction_attempts` already incremented at `ledger.py:360`; `verification = REFUTED` (`ledger.py:369`) |
| T4 | unverified | `verdict == refuted` (`ledger.py:369`) | **refuted** | `"Re-investigate (refuted): {text}"` (`ledger.py:371-373`) | promise **0.65**, pool `explore`, `corrects_claim_id = claim.id`, `parent_id = claim.direction_id` | `defect` set (`ledger.py:355`); `verification = REFUTED` (`ledger.py:369`) |

The spawned `Direction` is returned to the caller. In `_drain_verify_pool` the
returned corrective direction gets an extra promise bump of `+0.1`
(`orchestrator.py:586-587`).

### Inherited correction budget (bounding the fix loop across regenerations)

When EXPLORE runs a correction/re-investigation direction (one whose
`corrects_claim_id` points at an existing claim), `ingest` links the new claim to
the ancestor and **inherits its `correction_attempts`** (`ledger.py:247-251`):

```
claim.parent_claim_id      = ancestor.id
claim.correction_attempts  = ancestor.correction_attempts
```

So the error→correct→re-verify loop is bounded not only for a single claim id
(via the `≤ max_corrections` guard in `apply_verification`) but across
EXPLORE-regenerated refinements: each regeneration carries the running attempt
count forward, so after `correction_max_attempts` (default 2) total error verdicts
across the lineage, the next error verdict routes to refuted (T3). The `lineage`
helper (`ledger.py:261-270`) walks `parent_claim_id` for skeptical context but is
not itself part of the transition machinery.

## Terminal locking of `confirmed`

Once `verification == CONFIRMED`, the claim is never re-promoted, re-verified, or
re-scored:

- `_promotable_pool` only returns `UNVERIFIED` claims (`orchestrator.py:475`), so a
  confirmed claim cannot re-enter promotion.
- `_rescore_corroboration` filters its backlog to `UNVERIFIED` claims
  (`orchestrator.py:485-486`), so corroboration never touches a confirmed claim.
- `apply_verification` on a `confirmed` verdict returns `None` (`ledger.py:354`),
  spawning no follow-up direction.

`error` and `refuted` claims are likewise excluded from `_promotable_pool` (it
requires `UNVERIFIED`), so they are never directly re-promoted; their only path
forward is the spawned direction that mints a fresh `UNVERIFIED` claim.

## Corroboration bumps (unverified only)

`Ledger.corroborate(claim, corroborators, per_source=0.04, cap=0.95)`
(`ledger.py:304-321`) raises a claim's `confidence` when independent sources back the
same assertion:

| Property | Value / rule | Citation |
|----------|--------------|----------|
| Bump per new independent source | `+per_source` (default **0.04**, `Config.corroborate_per_source`, `orchestrator.py:109`) | `ledger.py:320` |
| Only counts sources the claim does not already cite | `s.key() not in own` and `resolvable()` | `ledger.py:311-316` |
| Ceiling | `cap` = **0.95** | `ledger.py:320` |
| Monotonic | `max(before, …)` — never lowers confidence; returns 0.0 if no new sources | `ledger.py:317-321` |
| Applies to | **unverified backlog only** — the driver filters `verification == UNVERIFIED and graduates()` | `orchestrator.py:485-486` |
| Corroborator match | text cosine `≥ corroborate_thresh` (default **0.88**) — the driver matches on embedding cosine only | `orchestrator.py:494-495` |

The driver `_rescore_corroboration` (`orchestrator.py:477`) runs once per EXPLORE
wave, gated by `Config.corroborate_enabled` (default true, `orchestrator.py:107`). It
is the resurfacing mechanism: a weak-but-true backlog claim gains confidence as new
independent evidence arrives, raising its promotion score so it can be promoted in a
later wave. Because it is restricted to `UNVERIFIED` claims, a confirmed or refuted
claim's confidence is never bumped this way.

The ledger also exposes `same_assertion`/`find_corroborators` (`ledger.py:277-302`),
which additionally match on a shared resolvable source, but these are **not wired into
the corroboration driver** (only into `selftest.py`); the driver's match is cosine
only.

## Verdict-state accounting

Two scoring views tally claims by terminal verdict; both count only `CONFIRMED` and
`REFUTED` (never `ERROR` or `UNVERIFIED`) toward pass rate:

| Method | Grouping | `strength` | `thin` | `contested` | Citation |
|--------|----------|-----------|--------|-------------|----------|
| `direction_scores` | direction → its produced claims | `confirmed/(confirmed+refuted)` | `n>0 and confirmed==0` | `checked≥2 and 0.34≤strength≤0.66` | `ledger.py:399-416` |
| `niche_scores` | primary aspect | same | `confirmed==0` | `checked≥2 and 0.34≤strength≤0.66` | `ledger.py:376-397` |

`direction_scores` feeds the frontier hierarchy boost (`orchestrator.py:390-395`);
`niche_scores` is described as a promotion-diversity tie-breaker but is not consumed
by the main loop (only `direction_scores` is called in `orchestrator.py`).

## Calibration labels (side channel, not a state change)

On each terminal verdict the loop appends a calibration tuple
`(raw_confidence, stated_interval_width, outcome)` where `outcome = 1.0` for
`CONFIRMED` else `0.0` — only for terminal `CONFIRMED`/`REFUTED`, never for the
transient `ERROR` (`orchestrator.py:584-585`; prior-probe path
`orchestrator.py:304-305`). This does not alter the claim's state; it feeds the
Component B calibrator. Note the FDR wealth settle (`orchestrator.py:580-581`) fires on
**every** verify outcome — including the transient `ERROR` — not just the terminal
`CONFIRMED`/`REFUTED` that gate the calibration-label append.
