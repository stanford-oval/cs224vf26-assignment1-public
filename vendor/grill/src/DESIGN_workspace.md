# The workspace — artifacts the agent builds, not just text it writes

**Status:** implemented. Offline-tested in `python3 -m src.selftest`.
**Goal:** let a researcher ask for a *deliverable* — "give me a CSV with all the benchmarks",
"plot the AUCs by marker" — and get a real file, built from the run's own evidence, versioned.

**Where it lives:** `src/workspace.py` (the git repo + the ledger export), `schemas.ARTIFACT` +
`executors.artifact` (the build task), the `_build_artifact` / `_service_artifacts` /
`_finalize_workspace` hooks in `src/orchestrator.py`, `artifacts_request` in `src/steer.py` and
`src/classify.py`, and the `/artifacts` + `/file` routes in `src/steer_server.py`.
CLI: `--no-workspace`, `--no-auto-artifacts`, `--artifact-usd`.

---

## 1. The gap this closes

Every codex task runs with `--cd <task_dir>`, a freshly created empty leaf that is thrown away
(`codex_exec.py`). Nothing the agent writes survives the task, so the run has exactly one output
shape: markdown prose. A researcher who wants the numbers as a spreadsheet, or the comparison as a
chart, has to extract them by hand from the report — re-typing figures that the ledger already holds
in structured form.

The fix is not "let the model attach files to its answer". It is to give the run **one durable,
version-controlled place to work**, and to put the belief state there as data.

---

## 2. Design

### 2.1 One git repo per question

`<run-dir>/workspace/` is a real git repository, created at run start (idempotently, so `--resume`
re-enters it) and never shared between questions:

```
workspace/
    data/         ← the ledger, exported by the HARNESS as JSON + CSV (read-only, regenerated)
    inputs/       ← the researcher's own data files (read-only, never regenerated)
    artifacts/    ← the deliverables
    scripts/      ← the code that produced them
    ARTIFACTS.md  ← the human-readable index
```

Git is what makes "the agent can go make changes and commit" safe rather than alarming: every build
is a commit, `git log` is the audit trail, and a bad artifact is a `git revert` rather than a lost
file. The workspace is initialised with a local `user.name`/`user.email` and `commit.gpgsign=false`
so committing works regardless of the host's global git config and can never block on a passphrase.

Git is a *nice-to-have*, not a dependency. Without it the workspace is a plain folder and artifacts
are still produced and indexed; only the history is missing.

### 2.2 The data comes from the ledger, deterministically

Before every build the harness exports the belief state into `data/`:

| file | shape |
|---|---|
| `findings.json` | every tested hypothesis, nested, with full source records |
| `findings.csv` | one row per hypothesis — status, verdict, confidence, support balance |
| `evidence.csv` | one row per sourced evidence item |
| `metrics.csv` | **long format: one row per number any source reported, with that source** |
| `report.md`, `run.json`, `question.txt` | the written answer, budget/snapshots, the question |

`metrics.csv` is the answer to "give me a CSV of all the benchmarks" — it already *is* that table;
a build only has to shape it. And because the agent computes over real files instead of transcribing
figures out of a prompt, the numbers in an artifact are the same numbers the report cites, carrying
the same DOIs. That is the provenance gate applied to deliverables: **an artifact cannot contain a
number the ledger does not hold.**

The export is free (no model call), so *every* run ends with a committed workspace holding the
report plus machine-readable findings — whether or not anyone asked for an artifact.

### 2.3 The ARTIFACT executor

One task type, `mode="research"` (workspace-write is what grants file creation), run with
`cwd=<workspace>` — a new `codex_exec` parameter that decouples *where codex runs* from *where the
harness keeps the task's control files*. The prompt tells it to inspect the data first, write its
generator into `scripts/`, run it, save under `artifacts/`, and commit.

Builds are **serial**: they share one working directory and one git index.

### 2.4 Files are the source of truth, not the model's declaration

The task returns a JSON declaration of what it built, but the harness never trusts it for existence.
What counts as produced is what *changed on disk* — `snapshot()` before, `changed()` after, minus
the harness-owned directories and anything gitignored (importing matplotlib drops a ~90KB font cache
in the cwd, which is not a deliverable). The declaration only supplies nicer titles and descriptions
where its paths match reality.

So a build that dies at its budget cap, emits malformed JSON, or has `git commit` refused by the
sandbox still gets its work indexed and committed by the harness. This is the same principle the
ledger already applies to evidence: the harness verifies, the prompt merely asks.

### 2.5 Asking for one

A deliverable request is a **steer event key**, `artifacts_request: [{spec, kind}]` — the same typed
mutation API as every other kind of human input (`DESIGN_interactive.md` §3.1). It is a *residual*,
not a ledger mutation: an artifact is a file, not a belief, so it never becomes a Direction, never
enters the frontier, and never gets scored. `classify.py` routes free text to it, with the boundary
stated explicitly: *building something out of existing findings is an artifact; going to find out
more is a direction.*

Requests are serviced at the loop seams that already exist (top of round, post-checkpoint, finalize),
so a request made mid-run is answered at the next seam instead of waiting for the run to end. An
unbuilt request persists in `run.json` state and survives a resume; one that cannot be afforded stays
queued and is logged, never silently dropped.

### 2.6 Cost

| | |
|---|---|
| workspace + data export + commit | **$0** — pure Python |
| a requested build | capped at `artifact_task_usd` (default $1.50) |
| the finalize pass | one build, only if `auto_artifacts` and the budget covers it |

Artifact spend is its own `Budget` phase, so it shows up separately in `run.json` and never
silently eats research budget.

---

## 3. Why this is safe

It reuses every existing invariant. The harness still owns state (the export is one-way, ledger →
files; nothing in the workspace flows back into beliefs). Provenance still holds, because artifacts
are computed from exported evidence rather than generated from memory. The budget still bounds
everything, through the same per-task USD watchdog. And the blast radius of anything the agent does
wrong is one git repository belonging to one question.
