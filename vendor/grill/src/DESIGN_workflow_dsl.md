# Workflow DSL — codex as a primitive, orchestration as a program

**Status:** proposed (design only; no code yet).
**Author of record:** project owner's direction — *"the workflow is basically controllable actions of codex … `for gene in genes: codex(summarize, gene)` … optionally `batch([...], batch_size=4)` … a DSL basically, for everything."*

---

## 1. Motivation

Steering today is **classification**: free text → an LLM (`classify.py`) maps it onto a fixed set of
belief-ledger mutations (directions / scope / assumptions / verdicts / budget / control). Two problems
surfaced in practice:

1. **It's the wrong abstraction for procedures.** "Write a summary for each gene" is not a belief nudge —
   it's a *program*: enumerate genes → per gene, gather + verify → emit a structured summary → assemble.
   The classifier has no channel for that (and no `required_fields`/report-shape channel at all), so it
   can only approximate it as vague new "directions."
2. **It can't express long-running, multi-step work.** Every steer channel is a point mutation scored on
   the next wave. There is no way to say "do this bounded, resumable, N-entity job to completion."

The current orchestrator loop (INIT → rounds of EXPLORE/PROMOTE/VERIFY/CHECKPOINT → FINALIZE) is itself a
*fixed* program written in Python. The proposal generalizes that: make orchestration a **first-class,
inspectable, resumable program** in a small DSL whose leaf operation is a codex task — so both the
built-in behavior and any ad-hoc researcher request are expressed the same way.

**Thesis:** `codex()` is the instruction; control flow composes instructions; a program is the unit of
work, of steering, and (eventually) of the loop itself.

---

## 2. What the DSL is (and is not)

**Is:** a *restricted* expression language — a Python-shaped subset — whose only side-effecting calls are
a whitelisted set of **primitives** (codex tasks + typed ledger ops). Programs are small, declarative,
and analyzable. They can be **hand-written** (a template or the console) or **synthesized by codex** from
a natural-language request.

**Is not:** arbitrary Python `exec`. Codex-authored code executing with real budget and file access is a
security boundary; we never `exec()` raw source. Execution goes through an **AST-allowlist interpreter**
(§6) so a program can only do what the primitives permit.

The essential shift, in one line:

```
NL request  ─▶  codex PLANS a program  ─▶  (human reviews/edits)  ─▶  sandboxed executor runs it
```

replaces

```
NL request  ─▶  classifier guesses fields  ─▶  ledger mutation
```

---

## 3. Primitives (leaves)

Every primitive is model-agnostic (reads `config.RUN_MODEL` etc. — no model name baked into a program,
honoring the "config is the single source of truth" contract) and budget-metered.

| Primitive | Signature | Notes |
|---|---|---|
| `codex(action, input, *, schema=None, model=None, reasoning=None, usd_cap=None)` | → validated JSON | One schema-constrained codex task via `codex_exec.run_task`. `action` names a registered prompt template (`summarize`, `explore`, `verify`, `ground`, `extract`, `compare`, …). Defaults from `config`. |
| `embed(texts)` | → vectors | Wraps `embed.Embedder`; for dedup/coverage. |
| `remember(claim=…, verify=…, direction=…, field=…, assumption=…)` | → id | Typed belief-ledger writes — the same typed API `SteerEvent.apply_to` already uses (provenance-tagged). |
| `recall(query)` | → list | Read the ledger: confirmed claims, entities of a field, open directions. e.g. `recall(entities="gene")`. |

Leaves are the *only* place work or spend happens. Combinators never call the model themselves.

---

## 4. Combinators (control flow)

A deliberately small set — enough to express real workflows, small enough to interpret safely.

| Form | Meaning |
|---|---|
| `x = expr`, sequence of statements | sequential binding/execution |
| `for e in xs: …` and comprehensions `[codex("summarize", g) for g in genes]` | iteration / building task lists |
| `batch(tasks, batch_size=N)` | evaluate a list of leaf-tasks with **bounded concurrency N** (maps onto the existing `ThreadPoolExecutor` + global concurrency cap). Returns results in order. |
| `gate(cond)` / `if cond: …` | conditional execution (cond is a primitive result or simple comparison) |
| `reduce(action, items, init=…)` | fold via a codex `action` (e.g. synthesize a section from per-gene summaries) |
| `retry(task, n)` | bounded retry (already in `run_task`) |

No `while` without an explicit step cap; no user-defined functions in v1 (templates cover reuse); no
attribute access, imports, comprehension-in-comprehension beyond depth 2. Kept small on purpose.

---

## 5. Execution model

- A program is parsed to an AST, then **interpreted** node-by-node (§6). Leaf calls become tasks.
- `batch(...)` schedules up to `batch_size` concurrent `codex()` leaves through the existing executor
  pool, honoring the **global concurrency cap** and the **two-pool budget** (explore/verify, ρ). Each
  leaf still gets its **per-task USD watchdog**.
- **Budget is the hard bound.** Before each leaf, check the pool; when the ceiling is hit, remaining
  leaves are *not* dropped — they're left `pending` in the journal and the program **yields**. It resumes
  when budget is added (a `budget_delta` steer) or on the next round.
- Results of leaves flow into the belief ledger via `remember(...)`, so coverage / calibration / finalize
  are unchanged downstream — the DSL is a *control layer above the existing executors*, not a replacement
  for them.

---

## 6. Execution: full Python `exec`, bounded by cost not grammar

**Decision (owner):** *allow anything in the sandbox.* Programs run as unrestricted Python, with the
primitives (§3–4) injected as the exec namespace:

```python
def run_program(source, rt):
    ns = {"codex": rt.codex, "batch": rt.batch, "recall": rt.recall,
          "remember": rt.remember, "run": rt.run, "reduce": rt.reduce}
    exec(source, ns)                 # real Python; primitives are the globals
```

**Honest scope of "codex already sandboxes this":** codex sandboxes each *leaf task's* execution, but the
orchestration program (the `for`/`batch` glue) runs in the **agent's own Python process on the host**, not
inside codex. So there is *no language-level sandbox* here by design. The guardrails are therefore
**cost/resource, not security**:

- budget ceiling + per-task USD watchdog (a runaway `while True: codex(...)` runs out of money, fast),
- max total leaves + max wall-clock per program,
- everything journaled for audit.

If host-level isolation of the glue is ever wanted, containerize the whole agent process (as the portal
already is) — orthogonal to this DSL.

### 6.1 Laziness — why `batch([codex(g) for g in genes])` parallelizes

`codex()` is **lazy**: it returns a `Task` and runs nothing on creation. If it ran eagerly inside the
comprehension, all N leaves would run *sequentially* before `batch` saw them. A Task is **forced** by
`batch(...)`, `run(...)`, or being passed into `remember(...)`; `_force` is the single choke point where
memo/resume + budget metering + the actual `codex_exec.run_task` happen. A bare `codex(...)` whose result
is never used is a lazy no-op (linted). Idiomatic per-entity forms:
`batch([codex("summarize_entity", {"gene": g}) for g in genes], batch_size=4)` or
`for g in genes: remember(claim=codex("summarize_entity", {"gene": g}))`.

### 6.2 Defining a primitive

Two registries; the **synthesizer's system prompt is generated from them**, so codex can only emit
programs over the real, self-documenting vocabulary:

- **Actions** — what `codex` can do: `{name: Action(prompt=lambda input: ..., schema=...)}`. Adding a
  capability = one entry.
- **Combinators / ledger ops** — `batch`, `run`, `reduce`, `recall`, `remember` as plain callables;
  `recall`/`remember` wrap the existing typed ledger API (same one `SteerEvent.apply_to` uses).

---

## 7. Determinism & resumability (what makes "long-running" real)

A 500-gene job is not one giant call — it's a program whose leaves complete across many rounds/restarts.

- Each `codex(action, input, model)` leaf has a **stable content key** = hash(action, canonical(input),
  model, schema). Its result + cost are written to a **journal** (`workflow_journal.jsonl`) in the run dir.
- On (re)execution, a leaf whose key is in the journal returns the cached result instantly; only new or
  changed leaves run live. Same program + same ledger ⇒ 100% cache hit. (This mirrors the run's existing
  `ledger.json`/`run.json` resume and the platform Workflow tool's journal/resume.)
- The program source is persisted (`program.dsl`) alongside the journal, so a steer that *edits* the
  program re-runs only the affected suffix.

Consequence: workflows are pausable, resumable, and survive a daemon restart — the property the current
point-mutation steering can never have.

---

## 8. Integration with steering and the loop

- **Steering becomes "supply or edit a program."** The steer inbox gains a `program` channel next to the
  typed events. Human-authored (console editor / picked template) or codex-synthesized from NL.
- **NL path, redesigned:** instead of `classify.py` guessing fields, a **planner** codex call emits a DSL
  program for the request, rendered back to the researcher to review/edit before it runs. Deterministic
  once fixed, inspectable, and far more expressive than the field-classifier. (The old classifier can stay
  as a thin fallback for trivial nudges; note it is *currently a no-op* because `openai` isn't installed
  in the venv — a separate one-line fix.)
- **Phase-staged adoption:**
  - *Phase 1* — workflows run as an injected phase: a program drains at a seam and executes to completion
    (budget-bounded, resumable), interleaved with normal rounds. The built-in loop is untouched.
  - *Phase 2* — express INIT / a round / FINALIZE themselves as built-in DSL programs, so "everything is a
    program" and the hardcoded orchestrator shrinks to an interpreter + a standard-library of programs.

---

## 9. Worked examples

**Per-entity summary ("a summary for each gene"):**
```
genes = recall(entities="gene", status="confirmed")
summaries = batch([codex("summarize_entity", {"gene": g, "fields": ["evidence","mechanism","confidence"]})
                   for g in genes], batch_size=4)
for s in summaries: remember(claim=s)
remember(field=["summary of "+g for g in genes])     # gate convergence on per-gene coverage
report = reduce("assemble_per_entity_section", summaries)
```

**Comparison matrix (A vs B across dimensions):**
```
cells = batch([codex("compare", {"a":a,"b":b,"dim":d}) for a in items for b in items for d in dims],
              batch_size=6)
remember(claim=cells)
```

**Re-expressing one EXPLORE round (Phase 2 sketch):**
```
dirs   = recall(directions="open", top=K)
found  = batch([codex("explore", d) for d in dirs], batch_size=concurrency)
claims = promote(found)                 # promote = a registered combinator (beam + Thompson)
batch([codex("verify", c) for c in claims], batch_size=concurrency)
```

---

## 10. Non-goals (v1)

- Not a general programming language — no user functions, recursion, unbounded loops, or I/O.
- Not a replacement for the belief ledger, budget pools, calibration, or FDR — those stay; the DSL
  *drives* them.
- Not human-free — codex-synthesized programs are reviewable before they spend.

---

## 11. Decisions

1. **Sandbox** — ✅ *decided:* allow anything; full Python `exec`, bounded by cost/resource not grammar (§6).
2. **v1 authorship** — ✅ *decided:* straight to the **codex program-synthesizer** (NL → codex writes a
   program → human reviews → run). Templates are just a fallback/library, not the v1 gate.
3. **Orchestrator stance** — *open:* Phase-1 augment-only first (recommended), or commit to Phase-2 "loop
   as a program" from the start?
4. **Combinator surface** — *open:* is §4 right, or trim v1 to `codex + batch + for` (+ `remember`/`recall`)?
5. **Concurrency vs budget precedence** when both bind — batch_size vs the two-pool ceiling.
6. **Synthesizer review UX** — does every synthesized program get shown for approval before it runs, or
   only above a cost threshold? (auto-run cheap programs, gate expensive ones?)

---

## 12. Grounding (existing code this builds on)

- `codex_exec.run_task` — the leaf primitive (schema-constrained task, per-task USD watchdog, retries).
- `orchestrator.py` — `ThreadPoolExecutor` concurrency, two-pool budget, checkpoint/resume, phase seams.
- `ledger.py` — typed belief state; `remember`/`recall` wrap its existing API.
- `steer.py` — the inbox + `SteerEvent`; gains a `program` channel.
- `config.py` — model/reasoning defaults, so programs stay model-agnostic.
- Prior art for journal/resume + bounded fan-out: the platform Workflow tool (pipeline/parallel/resume).
```
