# Methodology v2 — a belief-ledger research agent

A budget-bounded, self-correcting literature-research agent. Given one research question, it
spends a fixed USD budget across many small LLM calls — accumulating grounded, source-verified
claims, recalibrating its own confidence against verification outcomes, and rendering a ranked,
cited report.

The design principle is **calibrate-then-allocate**: the LLM's self-reported confidence is
overconfident and nearly uniform, so the harness recalibrates it online against real verification
results and then spends a bounded verification budget where it buys the most.

The whole agent lives in [`src/`](src/) and is self-contained — it shells out to the `codex` CLI and
calls an embeddings endpoint, but imports no other in-repo package.

## Quick start

```bash
# offline self-test — no codex, no spend
python3 -m src.selftest

# a real run (writes everything under --run-dir)
python3 -m src.cli \
  --question-file artifacts/genomics/pancreatic/question.txt \
  --run-dir v2_runs/genomic_pancreatic \
  --budget 50 -K 5 --rho 0.7
```

Requires the `codex` CLI on `PATH` and a `.env` at the repo root supplying an OpenAI-compatible
endpoint (`OPENAI_API_KEY` + `OPENAI_BASE_URL`, e.g. the Stanford LiteLLM→Azure proxy). The default
model is `gpt-5.4-mini`.

## Core idea

The **harness owns the control loop and all belief state; the LLM is a stateless executor** —
`f(task, context) → schema-validated JSON`, one task per call, no cross-task memory. Intelligence
goes where it helps (reading, judging); determinism goes where it matters (budget, state, stopping).

### The belief ledger

A bipartite graph separating the search frontier from the evidence:

- **Directions** — open questions (the frontier). Scored by forward value; consumed by EXPLORE.
- **Claims** — propositions with provenance (a resolvable `SourceRef`). Scored by calibrated
  confidence; consumed by VERIFY. A direction owns its claims; a bad claim spawns a corrective
  direction.

### The loop

```
INIT   parse required fields · prior candidates · prior-probe (seed the calibrator)
LOOP   SELECT DIRECTIONS (beam + Thompson)  →  EXPLORE (web search → grounded claims)
       →  PROMOTE (beam + Thompson over a resurfacing pool)  →  VERIFY (3-state)
       →  CHECKPOINT  →  (converged?  no → update from research yield; yes → finalize)
FINAL  deterministic synthesis + a citation-verify sweep → ranked, sourced report
```

Two separate budgets are allocated independently: an **explore pool** (over directions) and a
**verify pool** (over claims), split by `--rho`.

## The methodology

- **Online calibration** (`calibration.py`) — each EXPLORE/VERIFY claim carries a point `confidence`
  plus a `[conf_low, conf_high]` credible interval. Two isotonic (PAV) maps are fit online from
  verification outcomes: a **point map** (raw → P(true)) and a **width map** (stated interval width →
  actual outcome variance). The width map corrects the model's over-confident *uncertainty*.
- **Promotion = beam + Thompson** — the top-k claims by calibrated confidence are verified
  deterministically (exploit); the remaining verify slots are Thompson-sampled from calibrated Beta
  posteriors over a resurfacing pool (explore). Replaces a hard confidence floor, which would
  silently delete surprising-but-uncertain discoveries.
- **Three-state verification** — an adversarial literature check returns `confirmed` / `error`
  (supported but a fixable defect) / `refuted`; `error` and `refuted` each spawn a corrective
  direction. VERIFY uses codex's own web search to read primary sources.
- **Online-FDR verify budget** (`AlphaInvesting`) — an alpha-investing gate keyed on the *calibrated*
  score bounds false confirmations as claims resurface and get re-tested.
- **Annealing** — waves anneal broad-and-shallow → few-and-deep across rounds.
- **Evidence-aware convergence** — stop only when the question is complete, no evidence is unresolved
  (verify backlog drained + no open corrections), and the frontier is exhausted.

See [`METHODOLOGY_v2.md`](METHODOLOGY_v2.md) for the full write-up and
[`src/METHODOLOGY_v2_algorithm.tex`](src/METHODOLOGY_v2_algorithm.tex) for the formal spec.

## Layout

```
src/
  orchestrator.py    the control loop, budget pools, promotion, convergence
  ledger.py          the belief ledger (Direction / Claim / SourceRef) + provenance gate
  executors.py       PRIOR · GROUND · EXPLORE · VERIFY · judges · patterns · finalize
  codex_exec.py      the single LLM primitive: one `codex exec --output-schema` call → JSON + USD
  calibration.py     the two-map isotonic calibrator (point + width)
  embed.py           text-embedding-3-large for relevance / novelty / context (no lexical proxies)
  measure.py         frontier scoring
  metrics.py         checkpoint metrics (coverage / quality / progress)
  schemas.py         Azure-strict JSON schemas for every executor
  workspace.py       the per-question git workspace: ledger→CSV/JSON export, artifact indexing
  steer.py           interactive steering: SteerEvent + pluggable SteerSource (file/console/callback)
  steer_server.py    stdlib HTTP steering console backend (serves the ledger, accepts steer events)
  ui/steer.html      the self-contained browser steering console
  cli.py             the command-line entry point
  selftest.py        offline self-test (no codex / no spend)
  docs/              the documentation site (build with docs/build.py)
```

## Outputs (in `--run-dir`)

- `answer.md` — the deterministic synthesis: confirmed, sourced claims clustered by aspect
  (`✓` = source-verified).
- `ledger.json` — the full belief ledger (directions, claims, provenance, verification state).
- `run.json` — budget split, per-checkpoint metric snapshots, config.
- `tasks/NNNN_*/` — every codex call's prompt, schema, output JSON, and transcript.
- `orchestrator.log` — the control trace.
- `workspace/` — a **git repository for this question** (see Artifacts below): `data/` (the ledger as
  CSV + JSON), `artifacts/` (the deliverables), `scripts/` (the code that built them).
- `artifacts.json` — the deliverables index and the workspace's commit log.

## Configuration

`--budget` (total USD), `--rho` (explore/verify split), `-K` (best-first batch width), `--max-rounds`,
`--concurrency`, `--model` (default `gpt-5.4-mini`), `--env`. Full knob reference (calibration, FDR,
annealing, promotion) is in `src/orchestrator.py`'s `Config` and the docs.

## Interactive steering

A human can watch a live run and steer it — supply new **directions**, set **scope** filters, state
**assumptions**, reprioritize or drop directions, adjust the budget, or (rarely) rule on a claim — all
applied through the same typed ledger API the orchestrator uses. State is serialized every round, so a
run can also be paused and resumed. See [`src/DESIGN_interactive.md`](src/DESIGN_interactive.md).

```bash
# run with an async steer inbox drained each round
python3 -m src.cli --question-file Q.txt --run-dir OUT --budget 50 \
    --steer-inbox OUT/steer_inbox.json

# in another terminal: the browser steering console (stdlib only, no deps)
python3 -m src.steer_server --run-dir OUT --inbox OUT/steer_inbox.json --port 8765
#   → open http://localhost:8765

# or block for console steering at every checkpoint
python3 -m src.cli ... --interactive

# resume a paused/finalized run from its run-dir
python3 -m src.cli --run-dir OUT --resume
```

Steer events are plain JSON appended to the inbox (keys: `directions_add`, `directions_drop`,
`directions_boost`, `constraints`, `assumptions`, `fields_add`/`fields_remove`, `claims_pin`,
`claims_verdict`, `artifacts_request`, `budget_delta`, `control`) — or just send free text as `nl`
and the agent classifies it. Scope and assumptions are threaded into the research
prompts as guardrails and are **context, not claims** — they never pass the provenance gate. Human
verdicts are pinned (never re-verified, `$0`) and feed the calibrator as gold labels. Every applied
event is logged to `OUT/steer.log`; the current digest a human reads is `OUT/steer_request.md`.

## Artifacts — a git workspace per question

A run doesn't only write prose. Each `--run-dir` carries a **git repository for that question**,
`workspace/`, where the agent builds real deliverables — a CSV of every benchmark number, a chart
comparing candidates, a summary table — and commits them. See
[`src/DESIGN_workspace.md`](src/DESIGN_workspace.md).

```
workspace/
  data/        the ledger, exported by the harness as JSON + CSV (regenerated before every build)
  inputs/      the researcher's own data files
  artifacts/   the deliverables
  scripts/     the code that produced them — committed alongside, so each artifact is reproducible
```

The export is free and happens on every run: `findings.csv` (one row per tested hypothesis),
`evidence.csv` (one row per sourced item), and `metrics.csv` — **long format, one row per number any
source reported, with that source**. Because a build computes over those files rather than
transcribing figures out of a prompt, an artifact cannot contain a number the ledger doesn't hold;
its values carry the same DOIs the report cites.

Ask for one mid-run through the steering channel — free text works, it is classified into
`artifacts_request`:

```bash
echo '[{"nl":"give me a csv with all the benchmarks, and plot the AUCs by marker"}]' \
    > OUT/steer_inbox.json
```

Requests are built at the next loop seam (top of round / post-checkpoint / finalize), capped at
`--artifact-usd` (default `$1.50`) each and charged to their own budget phase. The harness indexes
whatever actually appeared on disk — not what the model claimed — so a build that runs out of budget
or gets `git commit` refused still has its work captured and committed. `--no-auto-artifacts` skips
the one bounded finalize pass; `--no-workspace` disables all of it.

## Your own data — `--data`

Point a run at your own files and the question can be about *them*, not only the literature:

```bash
python3 -m src.cli \
  --question "Which genes are present in both cohorts, and which are established DDR components?" \
  --data cohorts.csv --run-dir OUT --budget 8
```

The files are copied **read-only** into `workspace/inputs/` and pinned by content hash, so a claim
records the exact bytes it came from. The agent answers by writing a script into `scripts/` and
running it — never by reading numbers out of a prompt. See
[`src/DESIGN_data_plane.md`](src/DESIGN_data_plane.md).

The run first decides **which kinds of claim the question needs**, because that determines how each
one can be checked at all:

| the question needs | what happens |
|---|---|
| only your data | compute it; the research loop never starts |
| only the literature | unchanged from today |
| both | compute first, then research **the actual result** — not a guess about it |

Two claim kinds, verified differently. A claim about the world is tested against the literature. A
claim about your data is verified by **reading the script that produced it** — because re-running
deterministic code over an unchanged file proves only that it repeats, including repeating a wrong
answer. Reading it catches what re-running cannot.

Every query must also declare its **assumptions** — the interpretive choices it made that you could
reasonably have made differently (which column identifies an entity, what counts as present, how
blanks and duplicate or differently-cased identifiers were treated). These are not paperwork: in
testing, the same request over the same file returned 8 genes in one run and 7 in another, purely
because one matched gene symbols case-sensitively and the other didn't. Both are defensible; you
just have to be able to *see* which one you got. They appear in the report's **Data sources**
section, with the script and the row counts, next to the number they produced.

Data findings are never dressed up as citations — they have no author, year or DOI, and the report
attributes them to your data with the operation that produced them.

**It relocates the risk rather than removing it.** Instead of an invented figure you can get a wrong
join or a silently-empty filter that runs cleanly and returns a confident number. The safeguard is
that a script is stored, readable and re-runnable while a recalled fact is none of those — so review
is mandatory, not best-effort, and an unreviewed claim is reported as unverified.

## Documentation

- [`src/README.md`](src/README.md) — package-level overview.
- [`src/docs/`](src/docs/) — a browsable documentation site (architecture, module walkthroughs,
  design notes); build it with `python3 src/docs/build.py`.
- [`METHODOLOGY_v2.md`](METHODOLOGY_v2.md) — the methodology.
- [`src/DESIGN_promotion_v3.md`](src/DESIGN_promotion_v3.md) — the promotion / calibration redesign.
- [`src/DESIGN_interactive.md`](src/DESIGN_interactive.md) — human-in-the-loop steering.
- [`src/DESIGN_workspace.md`](src/DESIGN_workspace.md) — the per-question git workspace and artifacts.
- [`src/DESIGN_data_plane.md`](src/DESIGN_data_plane.md) — the researcher's own data as a queryable
  source: claim-kind routing, script review, and why data findings aren't citations.
