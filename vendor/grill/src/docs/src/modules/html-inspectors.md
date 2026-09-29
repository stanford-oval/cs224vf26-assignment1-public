# build_trajectory_html.py and build_explore_html.py

Two standalone command-line scripts that turn a completed run directory into a single self-contained, offline HTML file. Neither script is imported by the orchestrator or the CLI; each has its own `main()` and is run by hand (or by `stage_to_portal.py`) after a run finishes.

Related: [orchestrator.py](./orchestrator.md) writes the artifacts these scripts read, [stage_to_portal.py](./stage_to_portal.md) invokes them for the portal, [The orchestration loop](../architecture/orchestration-loop.md) explains the trajectory they render, and [The belief ledger](../architecture/belief-ledger.md) documents the `ledger.json` schema.

## What they are

| | `build_trajectory_html.py` | `build_explore_html.py` |
|---|---|---|
| Renders | the whole-run view: INIT, belief ledger, round-by-round trajectory, checkpoints/metrics | per-EXPLORE-agent view: each agent's actions, claims, and spawned directions |
| Reads from run dir | `ledger.json`, `run.json`, `orchestrator.log` | `tasks/*explore_r*/{prompt.txt,transcript.log,out.json}` |
| Invocation | `python3 -m src.build_trajectory_html <run_dir> <out.html>` (`build_trajectory_html.py:11`) | `python3 -m src.build_explore_html <run_dir> <out.html>` (`build_explore_html.py:8`) |
| Output | one dark-theme HTML file, vanilla JS, no external deps | same |

Both follow the same construction pattern: parse the run directory in Python into a JSON payload, escape it, string-substitute it into a `/*__DATA__*/` placeholder inside a large `r"""..."""` HTML template, and write the file. The client-side rendering is vanilla JavaScript embedded in the template; the Python side does only parsing and injection.

The `/*__DATA__*/` splice is why the payload is a bare JavaScript literal, not an HTML `<script type="application/json">` block. The safe-embed step (see below) is what keeps run text from breaking out of that literal.

---

## build_trajectory_html.py

### `parse_timeline(text)` — `build_trajectory_html.py:21`

Turns the plain-text `orchestrator.log` into an ordered list of typed event dicts. It is line-oriented and regex-driven; it does not parse structured logging, it scrapes the human-readable log lines the orchestrator prints.

Every log line must match `\[(\d\d:\d\d:\d\d)\]\s*(.*)$` (`build_trajectory_html.py:24`) to yield a timestamp `ts` and a `body`; lines without a `[HH:MM:SS]` stamp are skipped.

Cumulative spend is tracked as it scans: `explore $X/` updates `expl` and `verify $X/` updates `ver` (`build_trajectory_html.py:28-33`), and every event gets `cum = round(expl + ver, 2)` (`build_trajectory_html.py:34`). So `cum` is a running total reconstructed from whatever the most recent explore/verify spend line said — it is not read from `run.json`.

The event `type` is assigned by matching the body against a prefix/substring ladder:

| type | Trigger (body) | Extra fields parsed | Line |
|---|---|---|---|
| `init` | starts `INIT: parse` | — | 36 |
| `init_seed` | starts `required_fields=` | `required_fields`, `seed_directions`, `terms` (int) | 38-43 |
| `ground` | starts `INIT: GROUND` | — | 44 |
| `init_done` | starts `INIT spent` | overrides `cum` with the `$X` in the line | 46-48 |
| `round` | starts `ROUND` | `round` (int), `n_explore` from `EXPLORE (\d+) dir` | 49-53 |
| `ingest` | starts `+` and contains `claims` | `claims_added`, `novelty`, `verify_queue` | 54-60 |
| `verify` | contains `VERIFY drained` | `drained`, `confab` | 61-65 |
| `checkpoint` | starts `CHECKPOINT` | `n`, plus any of the metric keys below, plus `backlog` | 66-76 |
| `steer` | contains `STALLED`, or `+N deeper directions` | `corrective`, `stall` (bool) | 77-81 |
| `steer` | starts `weakest_axis=` | `weakest`, `corrective` | 82-86 |
| `regressions` | starts `regressions:` | `text` (remainder of line) | 87-89 |
| `delta` | starts `Δ_t` or contains `gain/$` | `delta`, `flat` (`"a/b"`) | 90-96 |
| `finalize` | starts `FINALIZE` | — | 97-98 |
| `done` | starts `DONE` | — | 99-100 |
| `log` | anything else (fallback) | — | 101-102 |

The `checkpoint` branch reads two different metric vocabularies from the same line (`build_trajectory_html.py:69-70`): the legacy composite `S, Corr, Comp, Fwd, Faith, recall` and the simplified `coverage, quality, answeredness`. It records whichever keys are present, so the parser supports both old and new runs without a version flag. The two `steer` rows above both set `type == "steer"` but populate different fields (`stall`/`corrective` vs `weakest`/`corrective`); the renderer distinguishes them by which fields exist.

```
orchestrator.log  (text)
   │  splitlines(), require [HH:MM:SS]
   ▼
per-line: track expl/ver spend → cum
   │  prefix/substring ladder → e["type"]
   ▼
[ {ts, raw, cum, type, ...typed fields}, ... ]   → timeline
```

### `main()` — `build_trajectory_html.py:107`

1. `run_dir = argv[1]`, `out = argv[2]` (`:108-109`).
2. Load `ledger.json` and `run.json` as JSON, read `orchestrator.log` as text with `errors="replace"` (`:110-112`).
3. `timeline = parse_timeline(log)` (`:113`).
4. Build `payload = json.dumps({"ledger": ..., "run": ..., "timeline": ...}, ensure_ascii=False)` (`:115-116`).
5. **Safe-embed**: replace `<`, `>`, `&` with their `\uXXXX` escapes (`build_trajectory_html.py:118`). This prevents a literal `</script>` (or any HTML) inside claim text, source titles, or log lines from terminating the `<script>` block and breaking the page.
6. `html = HTML_TEMPLATE.replace("/*__DATA__*/", payload)` and write it (`:119-120`).
7. Print a one-line summary: file size in KB, and counts of directions, claims, and timeline events (`:121-123`).

Note there is **no error handling** if `ledger.json`, `run.json`, or `orchestrator.log` is missing — the `read_text`/`json.loads` calls will raise. The script assumes a complete run directory.

### The HTML template — `build_trajectory_html.py:127-447`

A `r"""..."""` string holding a full `<!DOCTYPE html>` page: inline CSS (dark theme, CSS variables at `:131-132`), the `/*__DATA__*/` placeholder inside `<script>` (`:198`), and the vanilla-JS renderers. Client globals: `L = DATA.ledger`, `R = DATA.run`, `TL = DATA.timeline` (`:199`).

Six tabs are wired in `TABS` (`build_trajectory_html.py:212-213`): `overview`, `init`, `ledger`, `trajectory`, `checkpoints`, `how`. `show(id)` toggles the `.on` class and sets `location.hash`; on load it opens the hash or defaults to `overview` (`:445`).

Client-side helpers:

- `srcLoc(s)` (`:204`) — resolves a SourceRef to a URL, in priority order `doi` → `pmid` (PubMed) → `pmc` (PMC) → `url`.
- `graduates(c)` (`:205`) — true iff a claim has at least one evidence entry with a resolvable `doi`/`pmid`/`pmc`/`url`. This is the "graduated / sourced" gate reflected in the overview KPIs.
- `byVer(v)` (`:219`) counts claims by `verification`; `uniqSrc`/`verSrc` (`:221-222`) are de-duplicated source sets (all vs. `verified === true`).

Views, each an IIFE that writes into its `#v-*` section:

| Tab | What it renders | Lines |
|---|---|---|
| Overview | KPI grid (spend, rounds, claims, directions, confirmed/refuted/sourced/sources), final belief-state metrics, budget-pool bars, a config-knobs table, and a five-executor summary card | 225-272 |
| INIT | required fields, prior hypothesis + candidate answers, grounded glossary cards, and how the root frontier was seeded | 275-295 |
| Belief ledger | filterable **claims** table and **directions** table (frontier) | 298-342 |
| Trajectory | the `TL` events rendered as a vertical timeline with cumulative spend on the right edge | 345-368 |
| Checkpoints & metrics | per-checkpoint formulas with the actual numbers substituted, plus a convergence test | 371-412 |
| How it works | a static blackboard-architecture pseudocode block and data-structure notes | 415-442 |

**Config knobs** shown in the overview table (only those present in `R.config` are rendered), `build_trajectory_html.py:261`:

| Knob | Knob | Knob |
|---|---|---|
| `budget` | `rho` | `K` |
| `promote_tau` | `eta` | `explore_task_usd` |
| `verify_task_usd` | `task_cap_mult` | `explore_work_frac` |
| `progress_eps` | `model` | |

**Budget pools** (`:252-258`) draw three bars: explore capped at `total × rho`, verify capped at `total × (1 − rho)`, and embeddings capped at `total`.

**Claim states.** The ledger view maps status and verification to colored pills:

| Direction `status` | pill class | | Claim `verification` | pill class |
|---|---|---|---|---|
| `OPEN` | `b-mut` | | `confirmed` | `b-green` |
| `EXPLORING` | `b-amber` | | `refuted` | `b-red` |
| `EXPLORED` | `b-blue` | | `unverified` | `b-amber` |
| `CLOSED` | `b-mut` | | | |
| `PROMOTED` | `b-green` | | | |

(status map at `build_trajectory_html.py:299`, verification map at `:300`.) Both tables cap output at 400 rows (`:322`, `:335`).

**Checkpoints** (`:371-412`). The renderer detects the metric era from the first snapshot: `NEW` is true when both `coverage` and `quality` are present (`build_trajectory_html.py:373`). Legacy runs fall back to a composite `S / Corr / Comp / Fwd / Faith / recall` view (`:383-387`). For new runs it prints, per snapshot, the substituted formulas:

```
Coverage     = asks_answered / total_asks
Quality      = confirmed / (confirmed + refuted)     (= VERIFY pass-rate)
Answeredness = Coverage × Quality
Progress     = (Δ covered + Δ confirmed) / Δcost
STALL        = Progress ≈ 0  AND  Coverage < 1  → dig deeper, do NOT stop
```

The convergence test it prints is: STOP ⟺ Coverage = 100% AND backlog = 0 AND Progress ≈ 0 (`:408-410`).

#### Honest notes on the template

- **`W` and `BETA` are dead.** `const W = {...}, BETA = 0.5` (`build_trajectory_html.py:202`, commented "metrics.py defaults") are declared but never referenced anywhere else in the template. They are leftovers from the legacy composite metric.
- **`snaps` is dead.** In the overview IIFE, `snaps = R.run ? R.run.snapshots : R.snapshots` (`build_trajectory_html.py:226`) is assigned but never used; the code uses `R.snapshots` directly.
- **Executor count is inconsistent in the copy.** The overview card is headed "The five executors" and lists PRIOR, GROUND, EXPLORE, VERIFY, EVALUATE (`build_trajectory_html.py:263-269`), but the INIT view attributes required-field parsing to a separate "FIELDS executor" (`:278`). This is display text only; see [The executor roles](../architecture/executor-roles.md) for the authoritative set.
- The prose in these cards (Methodology §2/§6/§7 references, blackboard pseudocode) is static template copy, not derived from the run data.

---

## build_explore_html.py

Renders one card per EXPLORE task: the direction it was handed, its planned steps, the ordered sequence of web searches / source reads / compute steps parsed from the codex transcript, and the schema output (claims + new directions).

### Cost model — `build_explore_html.py:17`

`RATE = 10.0 / 1_000_000`, i.e. **$10 per 1M tokens**, a single flat blended rate. Per-agent USD is `round(tokens * RATE, 3)` (`build_explore_html.py:69`), where `tokens` is scraped from the transcript. This is an approximation local to this script — it is not read from `run.json` and does not reflect real, model-specific input/output pricing.

### `parse_prompt(p)` — `build_explore_html.py:20`

Pulls the explored direction and its rationale from the task `prompt.txt`. Preferred pattern captures `DIRECTION TO EXPLORE:\n<dir>\n(why this matters: <rationale>)` (`:22`); if the parenthetical rationale is absent it falls back to `DIRECTION TO EXPLORE:\n<dir>\n\n` and leaves `rationale` empty (`:27-29`).

### `parse_transcript(text)` — `build_explore_html.py:33`

Walks the transcript line by line to produce `{plan, actions, tokens, usd}`.

- **Plan bullets**: while still `in_prompt` and before any action, lines matching `^(→|•|*)\s+` are collected as plan items (`build_explore_html.py:44`).
- **exec steps**: the marker line `exec` (`:46`) flips `in_prompt` off; the *next* line is the command, passed to `classify_exec`. A non-empty classification is appended as an action.
- **web search lines**: `web search: <q>` (`:54`); if `<q>` starts with `http` it is recorded as a `read`, otherwise a `search` (`:57-61`).
- **tokens**: the line `tokens used` (`:62`) makes the next line the token count (commas stripped; `ValueError` ignored).

### `classify_exec(cmd)` — `build_explore_html.py:72`

Maps a shell command to an action `(kind, label)`:

| Match on lowercased command | kind | label |
|---|---|---|
| contains `curl` or `wget` | `read` | the URL if present, else first 90 chars |
| contains `printf` or `echo` | `""` (skipped — agent narrating) | `""` |
| contains `python` / `<<'py'` / `<<py` | `compute` | `python: extract/check numbers` |
| otherwise, if a URL is present | `read` | the URL |
| otherwise | `shell` | first 90 chars of the command |

An empty `kind` means the action is dropped (`build_explore_html.py:47-50`).

### `main()` — `build_explore_html.py:86`

1. Glob `run_dir/tasks/*explore_r*` and sort by `(round, idx)` parsed from `r(\d+)_(\d+)` in the directory name (`build_explore_html.py:89-90`).
2. For each task dir, parse `prompt.txt`, `transcript.log`, and `out.json`. Each file is guarded by `.exists()`, and `out.json` is additionally wrapped in a `try/except json.JSONDecodeError` that falls back to `{}` (`:95-103`). So a task missing or with an unparseable output degrades gracefully rather than crashing (unlike the trajectory script).
3. Build the per-agent record (`build_explore_html.py:117-124`):

| Field | Source |
|---|---|
| `round`, `idx` | parsed from dir name (`:93-94`) |
| `name` | task dir basename |
| `direction`, `rationale` | from `parse_prompt` |
| `plan`, `actions` (capped at 120), `n_actions`, `usd` | from `parse_transcript` |
| `claims` | `out.json` `claims[]`, each reshaped to `{text, stance, aspects, numbers, conf, src}` (`:104-114`) |
| `new_dirs` | `out.json` `new_directions[]` → `{q, p (promise), c (est_cost)}` (`:115-116`) |
| `dead_end` | `bool(out_json.get("dead_end"))` |
| `killed` | `not bool(out_json)` — true when `out.json` was missing or empty/unparseable (`:123`) |

   Each claim's `numbers` is rebuilt from the schema's list-of-`{metric, value}` into a flat `{metric: value}` map, skipping entries without a `metric` key (`build_explore_html.py:110`). The source `src` takes the first evidence entry and keeps first author, year, title, and a `loc` resolved as `doi || pmid || pmc || url` (`:112-113`).

4. Same safe-embed (`<`, `>`, `&` → `\uXXXX`, `build_explore_html.py:127`), splice into `TEMPLATE`, write, and print a summary counting agents, searches, reads, and claims (`:130-134`).

```
tasks/*explore_r{round}_{idx}/
   ├─ prompt.txt      → parse_prompt   → direction, rationale
   ├─ transcript.log  → parse_transcript → plan, actions[], tokens→usd
   └─ out.json        → claims[], new_directions[], dead_end
                          │  (missing/unparseable ⇒ killed=true)
                          ▼
              per-agent record → JSON payload → TEMPLATE
```

### The HTML template — `build_explore_html.py:138-226`

A two-pane layout (`.wrap` grid, 300px sidebar + main, `:147`). Client global is `A` = the agent array (`:181`).

- **Sidebar** (`build_explore_html.py:186-194`): agents grouped by round; each item shows the truncated direction and a meta line with `killed` tag, claim count, action count, and USD.
- **`loc(l)`** (`:184`): client-side SourceRef resolver — passes through `http…`; treats `^10.` as a DOI (`doi.org`), an all-digits string as a PMID (PubMed), a `PMC…` string as PMC, else returns the raw value.
- **`render(a)`** (`:196-223`): the detail pane. Renders the direction/rationale header, a KPI row (claims, searches, reads, new directions, dead-end), the plan block, the **research trajectory** timeline (action dots colored by kind — search=blue, read=teal, compute=amber, shell=violet, `:164`), the **claims** (each a card whose left border is green by default, red for `refutes` stance, muted for `neutral`, `:167-168`), and the **new directions** spawned. `read` actions whose text is a URL become clickable links (`:197`).
- On load, `sel(0)` opens the first agent (`:224`).

---

## Generating the files

```
# whole-run trajectory inspector
python3 -m src.build_trajectory_html  runs/<id>  runs/<id>/trajectory.html

# per-EXPLORE-agent inspector
python3 -m src.build_explore_html      runs/<id>  runs/<id>/explore.html
```

Both write a fully self-contained file (all CSS/JS/data inlined) that opens offline in any browser. `build_trajectory_html.py` needs `ledger.json`, `run.json`, and `orchestrator.log` in the run directory and will raise if any is missing; `build_explore_html.py` needs the `tasks/` subtree and tolerates missing or empty per-task files (rendering those agents as `killed`). See [stage_to_portal.py](./stage_to_portal.md) for how these are produced as part of publishing a run.
