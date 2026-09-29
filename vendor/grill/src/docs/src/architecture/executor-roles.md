# The executor roles (codex as a pure function)

This page covers the LLM layer: how `methodology_v2` uses `codex` as a set of stateless, schema-constrained *pure functions*. The orchestrator owns all state (the belief ledger, the budget, the frontier); each executor is a single call that takes a slice of that state, returns validated JSON plus the USD it cost, and never sees the loop.

Related: [executors.py](../modules/executors.md) · [Executor output schemas (reference)](../reference/schemas-reference.md) · [The orchestration loop](./orchestration-loop.md) · [The belief ledger](./belief-ledger.md) · [System overview](./overview.md)

## The pure-function contract

Every executor in `executors.py` is a thin wrapper that builds a prompt string, calls `codex_exec.run_task(task_dir, prompt, schema, mode=...)`, and returns `(data, usd)`. There is no hidden conversation state: codex is invoked fresh each time, its FINAL message is forced to match a JSON schema (via `codex exec --output-schema`), and the result is a plain dict. The orchestrator decides what to do with that dict — the model "never sees the loop" (`executors.py:13`).

```
   orchestrator state                 executor (pure fn)              codex process
   ┌──────────────────┐   slice of    ┌───────────────────┐  prompt  ┌──────────────┐
   │ ledger / budget / │─────state────▶│ build prompt      │─────────▶│ one call,    │
   │ frontier / config │               │ run_task(schema)  │          │ schema-bound │
   └──────────────────┘◀──(data,usd)──└───────────────────┘◀──JSON───└──────────────┘
          │  charges usd to a pool, ingests data, updates its own state
          ▼
   (model has no memory across calls; all continuity lives in the orchestrator)
```

Two structural facts follow from this contract:

- **One shared model.** Every executor runs on the same model, `Config.model` (default `"gpt-5.4"`, `orchestrator.py:89`), threaded in through `Orchestrator._kw()` (`orchestrator.py:224`). There is no per-role model routing.
- **Two sandbox modes, chosen per role.** `run_task` (`codex_exec.py:204`) forwards a `mode` argument through `**kw`; the explicit `mode` parameter is declared on the `_run_task_once` helper (`codex_exec.py:217`). `mode="research"` runs codex with `--sandbox workspace-write`, network access, and codex's native `web_search` (`codex_exec.py:246`); `mode="reason"` runs `--sandbox read-only` with no web (`codex_exec.py:260`). "Reason" roles work only from the state the orchestrator hands them; "research" roles go read real sources.

## Roles actually wired into the loop

Nine executor functions are invoked by the orchestrator. Each row below gives the mode, the call site, and the slice of state the call receives.

| Role | Mode | Output schema | Called at | Phase |
|------|------|---------------|-----------|-------|
| `fields` (`executors.py:38`) | reason | `REQUIRED_FIELDS` | `orchestrator.py:235` | INIT |
| `prior` (`executors.py:49`) | reason | `PRIOR` | `orchestrator.py:236` | INIT |
| `ground` (`executors.py:79`) | research | `GROUND` | `orchestrator.py:255` | INIT |
| `verify` (`executors.py:148`) | research | `VERIFY` | `orchestrator.py:287` (prior probe), `orchestrator.py:569` (verify pool) | INIT + LOOP |
| `explore` (`executors.py:95`) | research | `EXPLORE` | `orchestrator.py:350` | LOOP |
| `rerank` (`executors.py:64`) | reason | `RERANK` | `orchestrator.py:406` | LOOP (frontier select) |
| `judge_coverage` (`executors.py:274`) | reason | `JUDGE_COVERAGE` | `orchestrator.py:607` | LOOP (checkpoint) + FINAL |
| `patterns` (`executors.py:219`) | reason | `PATTERNS` | `orchestrator.py:637` (stall), `orchestrator.py:663` (final) | LOOP + FINAL |
| `finalize_report` (`executors.py:238`) | reason | `FINALIZE` | `orchestrator.py:670` | FINAL |

Full field-by-field schemas for each output live in [Executor output schemas (reference)](../reference/schemas-reference.md).

### Where the roles fire across a run

```
INIT ──▶ fields ─┐
        prior  ─┴─▶ ground (key terms) ─▶ verify (prior probe)
LOOP ──▶ rerank (pick frontier) ─▶ explore (a wave) ─▶ [promotion] ─▶ verify (drain pool)
          └─ checkpoint: judge_coverage ─▶ (if stalled) patterns
FINAL ─▶ verify (drain) ─▶ patterns (if none) ─▶ finalize_report ─▶ judge_coverage
```

## What each role sees — and does not see

The discipline of this design is that each call gets the *minimum* state it needs. The key distinction is between roles that see nothing but their explicit inputs and roles that see a *digest* of the ledger.

| Role | Sees | Does NOT see |
|------|------|--------------|
| `fields` | the raw question string only | the ledger, priors, any findings |
| `prior` | the raw question string only; no tools (read-only, no web) | the ledger, the loop, the web |
| `ground` | one term + the question + an optional budget hint | the ledger, other terms, prior claims |
| `rerank` | the question + a list of `(id, text)` open directions | claim texts, evidence, confidences, the ledger |
| `explore` | one `Direction` (`question_text` + `rationale`), a *selected* context slice of related claims, the question, budget | the full ledger; unrelated claims; the frontier; the budget pools |
| `verify` | one `Claim` (text, numbers, and its FIRST evidence source as an anchor) + budget | the question, the ledger, other claims, the direction it came from |
| `judge_coverage` | the question + the parsed `required_fields` + a grounded-claims digest | unsourced claims; per-claim confidences; directions |
| `patterns` | the question + a grounded-findings digest | the frontier; unsourced claims; the report |
| `finalize_report` | the question + `required_fields` + the glossary + distilled patterns + the full grounded-findings digest | ungrounded claims; the budget; the loop history |

Notes on the digests (these bound what "the ledger" means to a role):

- **`explore` context** is not the whole ledger. The orchestrator calls `measure.select_context(...)` to pick claims related to the direction, then `_slice_for` (`executors.py:25`) renders each as `[verification] text (src: loc)`. The prompt frames these as "ALREADY KNOWN (do not repeat; extend or contradict)."
- **`verify` is deliberately blind to the ledger.** It receives one claim and its cited anchor source (`executors.py:150`) and is told to search the literature independently rather than trust the anchor. It cannot see corroborating or contradicting claims already in the ledger; corroboration is handled separately by the orchestrator's embedding pass, not by this call.
- **The grounded-findings digests differ by role.** `judge_coverage` uses `_claim_digest(grounded_only=True, limit=80)` (`executors.py:188`) — a terse `[state] text (aspects)` list. `patterns` uses `_finalize_digest(limit=150)` and `finalize_report` uses `_finalize_digest` at its default `limit=220` (`executors.py:198`) — numbered, source-attributed rows with numbers and citations. All three see only *graduated* (sourced) claims, never the raw unsourced backlog.

## reason vs research, at a glance

```
 reason  (read-only, no web)     research (workspace-write + web_search)
 ───────────────────────────     ──────────────────────────────────────
 fields   prior                  ground
 rerank   judge_coverage         explore
 patterns finalize_report        verify
```

The research roles are exactly the three that must touch real sources — `ground` (find one authoritative definition + a `SourceRef`), `explore` (read sources and emit grounded claims), and `verify` (adversarially fetch and refute). Everything else reasons over state the orchestrator already holds.

## Two executors that are defined but never called

`executors.py` defines two more functions that the orchestrator never invokes:

| Role | Defined at | Schema | Status |
|------|-----------|--------|--------|
| `evaluate` | `executors.py:307` | `EVALUATE` (`schemas.py:266`) | Dead: no call site. A Reflexion-style draft evaluator (per-axis intrinsics, weakest axis, corrective directions). |
| `judge_forward` | `executors.py:292` | `JUDGE_FORWARD` (`schemas.py:246`) | Dead: no call site. An LLM scorer for `q(d)` — how testable/non-obvious each open direction is. |

Both are fully implemented and have live schemas, but a grep of the codebase finds no `executors.evaluate(` or `executors.judge_forward(` call anywhere in the loop; the only occurrences of "evaluate" in `orchestrator.py` are three non-call mentions: two comments about reserving budget for such calls (`orchestrator.py:78`, `orchestrator.py:315`) and a stale module-docstring line (`orchestrator.py:7`) asserting a "periodic EVALUATE checkpoint" that is never wired — which only reinforces the point. Frontier scoring is instead done by `rerank` plus embedding promise (`orchestrator.py:384`), and there is no draft-evaluation checkpoint — the checkpoint runs `judge_coverage` and, on a stall, `patterns` (`orchestrator.py:623`). Treat `evaluate` and `judge_forward` as scaffolding for a Reflexion loop that was not wired.

## A note on stale headers

Two source comments undercount the roles and should not be read as authoritative:

- The `executors.py` module docstring lists six tasks (PRIOR, FIELDS, GROUND, EXPLORE, VERIFY, EVALUATE) and omits `rerank`, `judge_coverage`, `patterns`, and `finalize_report`, while listing the dead `EVALUATE` (`executors.py:1`).
- The `schemas.py` docstring opens "Strict JSON schemas for the five codex executor tasks" (`schemas.py:1`), though the file defines eleven output schemas.

The wired-role table above reflects what the orchestrator actually calls; the reference pages ([executors.py](../modules/executors.md), [schemas-reference](../reference/schemas-reference.md)) enumerate the rest.
