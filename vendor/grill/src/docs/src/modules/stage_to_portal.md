# stage_to_portal.py

A standalone CLI that converts a finished methodology_v2 run directory into a "report-only" investigation the OVAL portal can display. It reads a run's `answer.md`, `run.json`, `ledger.json`, and `orchestrator.log`, then writes an `extracted/<slug>_db/` folder containing `report.md`, `question.txt`, and a v2-native `activity.json`.

Related: [orchestrator.py](./orchestrator.md), [ledger.py](./ledger.md), [build_trajectory_html.py and build_explore_html.py](./html-inspectors.md), [System overview](../architecture/overview.md)

## What it produces and why

The portal (an external `server.py`, not in this repo) renders an investigation from a directory named `extracted/<slug>_db/`. This script emits the minimum that portal expects for a *report-only* card: a cleaned report, the question, an activity summary, and a placeholder SQLite file. It deliberately does **not** emit a `trajectory.json`; per the module docstring, the portal hides the trajectory tab when `trajectory_graph` is absent from its `server.py` entry (`stage_to_portal.py:7-8`).

```
run_dir/                          extracted/<slug>_db/
  answer.md      ── clean_report ──►  report.md
  question.txt   ─────────────────►  question.txt
  run.json       ─┐
  ledger.json    ─┼─ build_activity ─►  activity.json
  orchestrator.log┘                     (summary+timeline+cost_curve+ledger)
  tasks/*        ─┘                  _none.sqlite   (empty placeholder)
```

## Module-level state and constants

| Name | Line | Purpose |
|------|------|---------|
| `ROOT` | `stage_to_portal.py:19` | Hardcoded portal root, `Path("/data/oval/report_formation")`. Output lands in `ROOT/extracted/<slug>_db`. |
| `LOG_TEXT` | `stage_to_portal.py:24` | Module global holding the run's `orchestrator.log` contents. Empty by default; set inside `main()` (`stage_to_portal.py:175-177`) and read by `build_activity` via `_timeline_from_log`. |

`LOG_TEXT` is passed by global rather than argument: `build_activity` references it directly (`stage_to_portal.py:119`), so it must be populated before `build_activity` runs.

## `_timeline_from_log(text) -> list[dict]`  (`stage_to_portal.py:27-66`)

Parses `orchestrator.log` line by line into an ordered list of timeline events for the portal Activity tab, reconstructing a cumulative USD figure from the pool numbers each log line prints.

Data flow per line:

1. Strip the log prefix: `re.search(r"\]\s*(.*)$", line)` keeps everything after the first `]` as `body` (`stage_to_portal.py:42-45`). Lines with no `]` are skipped.
2. Update running pool totals from any `explore $X/` or `verify $X/` substring found in `body` (`stage_to_portal.py:46-51`), stored in `last_expl` / `last_ver`.
3. `cum_now = last_expl + last_ver` is the reconstructed cumulative spend at that line (`stage_to_portal.py:52`).
4. Classify the line by prefix and call the nested `add(...)` helper.

The nested `add(kind, name, label, summary, cum_now, state=False)` (`stage_to_portal.py:34-39`) appends a row with an incrementing `seq`, a per-event `usd` delta (`max(0, cum_now - cum)` rounded to 4 places, where `cum` is the previous line's cumulative), the `cum_usd`, and a `state_update` flag.

Line classification:

| Body prefix / match | Line | Event `kind` / `name` | Notes |
|---------------------|------|-----------------------|-------|
| `INIT spent` | `:53-54` | `state` / `init` | `cum_now` overridden to the first `$X` in the body via regex, not the pool sum. |
| `ROUND` | `:55-56` | `search` / `explore` | Label is the text before the first `(`. |
| lstripped starts `+` and contains `claims` | `:57-58` | `notes` / `ingest` | Claim-ingest events. |
| contains `VERIFY drained` | `:59-60` | `think` / `verify` | |
| `CHECKPOINT` | `:61-62` | `state` / `checkpoint` | `state=True`. |
| `FINALIZE` or `DONE` | `:63-64` | `state` / `finalize` | `state=True`. |

Lines that match `]` but none of these prefixes still update `cum` (`stage_to_portal.py:65`) so their spend is folded into the next emitted event's delta. The `INIT` branch will raise `AttributeError` if an `INIT spent` line contains no `$` amount, since it calls `.group(1)` on the search result unconditionally (`stage_to_portal.py:54`).

## `_src_key(s) -> str | None`  (`stage_to_portal.py:69-73`)

Builds a deduplication key for one evidence source dict. Checks identifier fields in priority order `doi, pmid, pmc, url`; the first present one yields `"<field>:<value lowercased/stripped>"` (`stage_to_portal.py:70-72`). If none exist, falls back to the lowercased title, or `None` when even the title is empty (`stage_to_portal.py:73`). Used to count distinct papers.

## `build_activity(run, ledger, generated_at, task_dirs) -> dict`  (`stage_to_portal.py:76-145`)

Assembles the full `activity.json` payload. Inputs are the parsed `run.json` dict, the `ledger.json` dict, an ISO timestamp string, and the list of task subdirectory names.

**Budget block** (`stage_to_portal.py:77-81`): pulls `spent`, `explore`, `verify`, `embeddings` from `run["budget"]`, each rounded to 4 decimals.

**Source counting** (`stage_to_portal.py:83-92`): iterates every claim's `evidence` list, keys each source with `_src_key`, adds to `all_src`, and to `conf_src` only when the *owning claim* has `verification == "confirmed"`. Note the confirmed test is on the claim, so a confirmed claim's evidence counts as a "read" paper even if that same source also appears under an unconfirmed claim.

**Task counts** (`stage_to_portal.py:94-99`): a nested `count(pred)` tallies task-dir names. `n_verify` matches substring `verify_`, `n_explore` matches `explore_`, and `n_other` is the remainder.

**`by_kind`** (`stage_to_portal.py:101-105`):

| Key | usd source | count | color |
|-----|-----------|-------|-------|
| `explore` | `explore` pool | `n_explore + n_other` | `var(--blue)` |
| `verify` | `verify` pool | `n_verify` | `var(--teal)` |
| `embeddings` | `embeddings` pool | `1` (hardcoded) | `var(--green)` |

`n_other` (tasks matching neither prefix) is folded into the explore count.

**`summary`** (`stage_to_portal.py:106-113`): fields below.

| Field | Value | Line |
|-------|-------|------|
| `total_usd` | `budget.spent` | `:107` |
| `codex_usd` | `explore + verify` | `:107` |
| `aux_usd` | `embeddings` | `:107` |
| `n_actions`, `n_tool_calls` | both `len(task_dirs)` | `:108` |
| `by_kind` | table above | `:109` |
| `papers_read` | `len(conf_src)` | `:110` |
| `papers_total` | `len(all_src)` | `:110` |
| `generated_at` | passed-in timestamp | `:111` |
| `rounds` | `run["round"]` | `:112` |

**`cost_curve`** (`stage_to_portal.py:115-117`): one point per entry in `run["snapshots"]`, `{"seq": i+1, "cum_usd": snapshot["cost"]}`.

**`timeline`** (`stage_to_portal.py:119-129`): calls `_timeline_from_log(LOG_TEXT)` if the global log text is non-empty. If that yields an empty list (no log, or no matching lines), it falls back to one `checkpoint` event per snapshot (`stage_to_portal.py:120-129`). The fallback summary string switches format depending on whether the snapshot carries a `coverage` field (coverage/quality/answeredness) or not (`S`/`Corr` score form).

**`ledger` view** (`stage_to_portal.py:131-143`): filters claims to `verification == "confirmed"`, sorts them by descending `confidence`, takes the top 40, and renders them as a markdown bullet list in `confirmed_findings` (`stage_to_portal.py:132-134`). The `scope` string is a fixed sentence with the run's `config.rubric` appended (`stage_to_portal.py:137-138`). `counts` reports total claims, confirmed, refuted, and number of `directions` (`stage_to_portal.py:140-142`).

**Return** (`stage_to_portal.py:144-145`): `{"summary", "timeline", "cost_curve", "ledger", "ledger_versions": []}`. `ledger_versions` is always an empty list — no version history is emitted.

## `clean_report(answer_md, title) -> str`  (`stage_to_portal.py:148-154`)

Replaces the report's first line with `# <title>` only if that first line already begins with `# ` (`stage_to_portal.py:152-153`). The rationale (docstring) is that `answer.md` opens with the full question as an oversized H1, while the portal shows the question separately in its own callout. Returns the body right-stripped with a single trailing newline (`stage_to_portal.py:154`). If the first line is not an H1, the report is returned unchanged aside from trailing-whitespace normalization.

## `main() -> int`  (`stage_to_portal.py:157-191`)

Positional CLI arguments (no argparse):

| `sys.argv` | Name | Meaning | Line |
|-----------|------|---------|------|
| `[1]` | `run_dir` | Path to the completed v2 run directory | `:158` |
| `[2]` | `slug` | Output folder is `ROOT/extracted/<slug>_db` | `:159,161` |
| `[3]` | `title` | Clean H1 title for the report | `:160` |

Invocation form (docstring `stage_to_portal.py:10`):

```
python3 -m src.stage_to_portal <run_dir> <slug> "<clean title>"
```

Control flow:

1. Create the output dir with `mkdir(parents=True, exist_ok=True)` (`stage_to_portal.py:161-162`).
2. Read `answer.md`, `run.json`, `ledger.json` (`stage_to_portal.py:164-166`). These reads are unguarded — a missing file raises.
3. Resolve the question: `question.txt` if present, else `run["question"]`, else `ledger["question"]` (`stage_to_portal.py:167-170`).
4. Write `report.md` via `clean_report` and `question.txt` stripped with a trailing newline (`stage_to_portal.py:172-173`).
5. Populate the `LOG_TEXT` global from `orchestrator.log` (empty string if the file is absent) (`stage_to_portal.py:175-177`).
6. Derive `generated_at` from the mtime of `answer.md` as a UTC ISO string (`stage_to_portal.py:179-180`). The timestamp reflects the file, not the current time.
7. Collect `task_dirs` from `run_dir/tasks/*` names, or `[]` if `tasks/` is absent (`stage_to_portal.py:181`).
8. Build and write `activity.json` with `json.dumps(..., indent=1)` (`stage_to_portal.py:182-183`).
9. `touch` an empty `_none.sqlite` so the portal's `_none.sqlite` path resolves; a report-only card never opens it (`stage_to_portal.py:185-186`).
10. Print a one-line summary (report KB, total USD, papers read/total, action count, output path) and return `0` (`stage_to_portal.py:188-191`).

The module entry point is `raise SystemExit(main())` (`stage_to_portal.py:194-195`).

## Notes and honest caveats

- **Not part of the orchestration loop.** This is a post-hoc export/staging tool run manually after a completed run; nothing in `orchestrator.py` imports or calls it.
- **Hardcoded portal root.** `ROOT` (`stage_to_portal.py:19`) is an absolute path specific to the deployment host; there is no override flag or env var.
- **No error handling / no argparse.** Missing `sys.argv` entries or missing input files raise uncaught exceptions. The `INIT` timeline branch (`stage_to_portal.py:54`) assumes a `$` amount is present.
- **`LOG_TEXT` via global.** `build_activity` depends on the module global being set first (`stage_to_portal.py:119`); calling `build_activity` directly without setting `LOG_TEXT` silently yields the checkpoint-only fallback timeline.
- **`embeddings` count is hardcoded to 1** (`stage_to_portal.py:104`) regardless of actual embedding-call volume.
