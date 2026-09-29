# Implementation brief — showing agent-built artifacts in the sliders portal

**For:** the sliders-portal agent (`/srv/services/sliders-portal`).
**From:** the methodology-v2 research agent (`graph-search-sliders`), which now produces them.
**Status:** the agent side is implemented and tested. The portal side is not started.

---

## 1. What changed, in one paragraph

A methodology-v2 run used to produce only prose (`answer.md`). It now also **builds files**: a CSV of
every benchmark number, a chart comparing candidates, a summary table. Each run-dir carries a git
repository — `<run-dir>/workspace/` — where the agent writes deliverables and commits them, and an
index at `<run-dir>/artifacts.json` describing what it built.

A researcher can ask for one mid-run in plain language ("give me a csv with all the benchmarks",
"plot the AUCs by marker"). **That request path already works through the portal today** — see §5 —
so the work here is almost entirely *read*: list the artifacts, let people open and download them,
and render images inline.

---

## 2. The read model (what is on disk)

Run-dirs are the ones the portal already serves: `extracted/steer_runs/<slug>/`. Two new things
appear beside the existing `ledger.json` / `run.json` / `answer.md`:

```
extracted/steer_runs/<slug>/
    answer.md            ← existing
    ledger.json          ← existing
    run.json             ← existing
    artifacts.json       ← NEW: the index (poll this)
    workspace/           ← NEW: a git repo, one per question
        README.md          what the workspace is (written for the agent)
        ARTIFACTS.md       human-readable index of the same records
        data/              the belief ledger exported as CSV + JSON (harness-owned)
        inputs/            the researcher's own uploaded data files
        artifacts/         THE DELIVERABLES — this is what users want to see
        scripts/           the code that generated them, committed alongside
```

### 2.1 `artifacts.json` — the index

Rewritten every round and after every build. Real sample:

```json
{
  "workspace": "/srv/services/sliders-portal/extracted/steer_runs/run-1933ee9f/workspace",
  "artifacts": [
    {
      "path": "artifacts/benchmarks.csv",
      "title": "All benchmarks",
      "kind": "data",
      "description": "every reported metric, one row per marker",
      "request": "give me a csv with all the benchmarks",
      "auto": false,
      "commit": "0aac1333380c837fbe7376f0d92a670b9d933b89",
      "created": 1786050696,
      "bytes": 8421
    }
  ],
  "pending": [
    { "spec": "plot the AUCs by marker", "kind": "chart" }
  ],
  "commits": [
    { "sha": "0aac133…", "short": "0aac133", "ts": 1786050696, "subject": "artifact: benchmarks" },
    { "sha": "8a7ae57…", "short": "8a7ae57", "ts": 1786050696, "subject": "workspace: initialise" }
  ]
}
```

| field | meaning |
|---|---|
| `path` | **workspace-relative**, always. Never absolute, never escapes the workspace. |
| `title` | display name. Falls back to a prettified filename, so it is never empty. |
| `kind` | one of `chart` · `table` · `data` · `doc` · `code` · `other`. Drives the icon. |
| `description` | may be `""` — the agent didn't always describe what it built. |
| `request` | the user's own words that asked for it. Good subtitle / grouping key. |
| `auto` | `true` = the agent chose to build this at finalize; `false` = a user asked. |
| `commit` | git sha, or `""` if git was unavailable on the host. |
| `created` | **epoch seconds** (not ISO — differs from `launch.json.requested_at`). |
| `bytes` | file size. |

`artifacts` is oldest-first — reverse it for display. `pending` is requests not yet built.
`commits` is the workspace's git log, newest first.

**`artifacts.json` may not exist**: older runs, runs launched with `--no-workspace`, or a run that
hasn't reached its first save. Treat a 404 as *"no artifacts yet"* and render the empty state, not an
error banner.

### 2.2 What is actually in `artifacts/`

Whatever the agent built. In practice: `.png` charts (~50KB, dpi=160), `.csv` tables, occasionally
`.md` summaries or `.svg`. Nothing enormous — but a CSV over a large corpus could reach a few MB, so
stream rather than buffering into memory.

Note that `data/` is *not* artifacts — it's the harness's ledger export that the agent computes over.
It's worth exposing as a secondary "raw data" affordance (§4.3) but keep it out of the main list; the
index already excludes it.

---

## 3. Endpoints to add

Both are read-only and mirror patterns already in `server.py`. Follow the existing conventions:
`_steer_dir(run)` for slug validation and root confinement, `_steer_file(...)` for the no-cache
`FileResponse`, and declare these **after** `/api/steer/new` so the literal isn't captured as a slug.
The `/api/` auth middleware covers them as-is.

### 3.1 `GET /api/steer/{run}/artifacts`

Serve `<run-dir>/artifacts.json` verbatim — one line, same shape as `steer_ledger`:

```python
@app.get("/api/steer/{run}/artifacts")
def steer_artifacts(run: str):
    return _steer_file(run, "artifacts.json", "application/json")
```

Consider returning `{"artifacts": [], "pending": [], "commits": []}` on a missing file instead of a
404, so the frontend has one less branch. Either is fine — just pick one and make the UI match.

### 3.2 `GET /api/steer/{run}/artifact?path=<workspace-relative>`

Serve one file out of `<run-dir>/workspace/`. **This is the security-sensitive one.** Three rules,
all mandatory:

1. **Confine the path.** Resolve `(workspace_root / path)` and reject unless the result is
   `workspace_root` itself or has it in `.parents` — the same check `_steer_dir` already does for
   slugs. This must survive `../../.env`, URL-encoded `..%2F..%2F`, absolute `/etc/passwd`, and
   symlinks (hence `.resolve()`, not string prefix matching). The run-dirs sit next to `.env` and the
   investigation SQLite DBs, so a traversal here is a real credential leak.
2. **Never render model-authored markup on the portal's origin.** Everything under `workspace/` was
   written by an LLM. If the guessed content type is `text/html`, `image/svg+xml`, or
   `application/xhtml+xml`, serve it as `text/plain` instead. An SVG served as `image/svg+xml` can
   carry `<script>` and would run with the user's portal session. Send
   `X-Content-Type-Options: nosniff` on every response.
3. **Only inside `workspace/`.** Don't let this route reach `ledger.json`, `steer_inbox.json`, or the
   task transcripts — those have their own endpoints with their own semantics.

The local dev console in the research repo implements exactly this in ~20 lines; see
`graph-search-sliders/src/steer_server.py::_workspace_file` for a reference implementation and its
test cases.

### 3.3 Optional: `GET /api/steer/{run}/artifacts.zip`

"Download everything" is a natural ask once there are more than two or three files. Zip
`workspace/artifacts/` (and optionally `workspace/data/`). Low priority — the per-file route covers
the main need.

---

## 4. The UI

### 4.1 Where it goes

A new **Artifacts** tab in the run view's tab bar (`backend/index.html`, alongside Report / Graph /
Papers / Trajectory / Activity), following the `trajTab` / `actTab` pattern: hidden by default,
revealed when the run has at least one artifact or one pending request. Show a count badge like the
Graph and Papers tabs do.

### 4.2 The list

Reverse-chronological cards, one per artifact:

- **Charts** (`kind: "chart"`, or a `.png`/`.jpg` path) — render the image inline at a sensible
  max-width, clickable to open full size. This is the payoff: a user asks "plot the AUCs by marker"
  and the plot appears in the run they're already reading.
- **Tables / data** (`.csv`, `.tsv`) — the file is small and structured, so parse and render the
  first ~50 rows as a real table with a "download CSV" button. Falling back to a download link is
  acceptable for v1, but inline preview is most of the value for `metrics.csv`-style output.
- **Docs** (`.md`) — render as markdown; the portal already has a renderer for `answer.md`.
- **Anything else** — filename, size, download link.

Each card shows `title`, `description` when present, and — importantly — **`request`**, the user's own
words that produced it. That's what makes the tab legible to a teammate who didn't ask for it.
`auto: true` items deserve a quiet "agent's choice" marker to distinguish them from what someone
requested.

### 4.3 Secondary affordances

- **Pending requests** render as skeleton cards: *"plot the AUCs by marker — queued, builds at the
  next round."* Without this the UI looks broken for the 30–120s between asking and getting.
- **Provenance.** Each artifact's `commit` links to nothing today (there's no git browser), but
  showing the short sha communicates that this is versioned, reproducible output. The `commits` array
  can back a small "history" disclosure listing every build.
- **The generating script.** Artifacts under `scripts/` are indexed like any other file. Consider
  collapsing them under the artifact they produced rather than listing them as peers — "show the code
  that made this" is a strong trust signal for a research tool.
- **Raw data.** A quiet link to `data/findings.csv`, `data/evidence.csv`, and `data/metrics.csv`
  (fetched through the same `/artifact` route) gives power users the full export without cluttering
  the list. `metrics.csv` is long format — one row per number any source reported, with that source —
  and is frequently what someone actually wants.

### 4.4 Polling

`artifacts.json` is rewritten on every round save and after every build. The run view already polls
`/run` and `/ledger` for live runs; add `/artifacts` to the same cycle at the same cadence. No
push, no websocket.

---

## 5. The write path — already works, nothing to build

`POST /api/steer/{run}` appends its raw JSON payload to the run's `steer_inbox.json`, which the agent
drains at every loop seam. It doesn't validate or filter keys, so **artifact requests already flow
through it unchanged**. Two accepted forms:

```jsonc
// free text — the agent classifies it into the right steer channel
{ "nl": "give me a csv with all the benchmarks, and plot the AUCs by marker" }

// or structured, if the UI has a dedicated box
{ "artifacts_request": [ { "spec": "a csv with all the benchmarks", "kind": "data" } ] }
```

`kind` is optional (`chart` · `table` · `data` · `doc` · `other`). The existing free-text steer box
therefore *already* produces artifacts — the classifier routes "give me a CSV" to a build and "go
look into X" to a research direction. Adding an explicit "Ask for a deliverable" input next to the
artifact list is a nice-to-have, not a requirement.

**One behaviour worth surfacing in the UI:** `_request_resume` in `server.py` already resumes a
finished run when a steer arrives and ≥ $0.50 of budget remains, and the agent builds queued
artifacts immediately on resume. Below $0.50 the request stays in `pending` and never builds. So if
`pending` is non-empty and the run is finished with a near-exhausted budget, the honest message is
*"add budget to build this"* — not a spinner.

Timing, for setting expectations in the UI: a request lands at the next loop seam (top of round,
post-checkpoint, or finalize), so **within a round** — typically 30 seconds to a couple of minutes on
a live run, and near-immediately on a resumed one.

---

## 6. Guarantees you can rely on

These are enforced on the agent side, so the portal doesn't need to defend against them:

- `path` is always workspace-relative and inside the workspace. (Validate anyway — §3.2 — but the
  index won't contain anything hostile.)
- The index reflects **files that actually exist on disk**. The agent detects artifacts by diffing the
  filesystem, not by trusting the model's declaration, so an entry in `artifacts.json` is never a
  phantom. Conversely a build that crashed still has its real output indexed.
- Numbers inside artifacts come from the run's own evidence export, carrying the same DOIs the report
  cites. An artifact cannot contain a figure the belief ledger doesn't hold.
- `title` and `kind` are always populated. `description` and `commit` may be empty strings.
- The workspace is per-question and never shared between runs.

---

## 7. Acceptance checklist

- [ ] `GET /api/steer/{run}/artifacts` returns the index; a run without one degrades to an empty state.
- [ ] `GET /api/steer/{run}/artifact?path=artifacts/foo.png` returns the image.
- [ ] `?path=../../.env`, `?path=..%2F..%2F.env`, `?path=/etc/passwd`, and `?path=` all return 404.
- [ ] An `.html` or `.svg` under `workspace/` is served as `text/plain`, with `nosniff`.
- [ ] The Artifacts tab is hidden for runs with none, and shows a count when there are some.
- [ ] A chart renders inline; a CSV previews or downloads; each card shows the request that produced it.
- [ ] Pending requests render as queued rather than being invisible.
- [ ] Nothing regresses for older runs that have no `workspace/` at all.

---

## 8. Reference

Full design rationale, the export format, and why artifacts are detected from the filesystem rather
than the model's declaration: `graph-search-sliders/src/DESIGN_workspace.md`.
Reference implementation of both endpoints (stdlib, ~40 lines):
`graph-search-sliders/src/steer_server.py`. Reference UI (plain HTML/JS artifact panel):
`graph-search-sliders/src/ui/steer.html`.
