# Progress & Findings — SynLethDB evaluation of the research-agent prototypes

_Last updated: 2026-06-21._

Goal: turn the graph-search prototypes into a robust literature research agent and
measure them on a concrete task — **predict the synthetic-lethal (SL) partners of a
query gene**, scored against [SynLethDB](https://www.synlethdb.com/). The eval
harness lives in `experiments/synlethdb/` (parent repo); the agents live here.

---

## 1. Architecture we built

Two minimal research-agent prototypes share **one tool layer** (the only thing that
differs is how guidance is delivered):

- **proto1 `graph_search`** — one fat inline prompt (`prompts/research.md`).
- **proto2 `skills_agent`** — slim prompt + **skills auto-discovered from
  `<repo>/.agents/skills`** (no global install; codex finds them because the run cwd
  is under the repo and repo-scope wins).

**Tools — a stdio MCP server** (`graph_search/mcp_server.py`, console script
`graph-search-mcp`), launched per run by `codex_runner` via `-c mcp_servers.research.*`:

| tool | purpose |
|---|---|
| `paperclip_search` | search the paperclip biomedical corpus (full-text, readable) |
| `serper_search` | Google Scholar / web — discovery channel (titles/snippets only) |
| `fetch` | download a doc's full text (`paperclip cat --full`) to `./papers/<id>.txt` for shell grep; returns path + meta only |
| `notes` | SQL over `notes.sqlite` (SELECT capped at 10 rows) |
| `budget` | real USD spent so far |

The server runs **on the host** (outside codex's sandbox), which is what makes
paperclip work cleanly. Every tool reply ends with a live `[notes.sqlite: …]` footer.

**Agent method** (both prototypes):
- **serper-discover → paperclip-read handoff** (serper finds what exists incl.
  out-of-corpus; resolve to a paperclip id and `fetch` full text; snippet-only
  fallback as a Class-3 lead when a doc isn't in the corpus).
- **Explicit θ/D ledger** in a `state.md` scratchpad (θ = candidate answers/categories
  with status `confirmed/tentative/open/contradicted`; D = search angles tried + yield).
- **IDS/BOED planning** (`task_regret² / design_gain`), **record-as-you-go**,
  **read→reflect→search** (each fetch nudges "record + decide whether to search more").
- **Generic class-tiered final list** (`prompts/finalize.md`): a ranked list of
  answer entities **in the form the question asks for**, each tagged
  **Class 1 (established) / 2 (likely) / 3 (plausible/inferred)**. The model may use
  its own knowledge to resolve groups/orthologs to the requested form; only the
  *claim* must stay grounded in a finding. No domain logic in the engine.

Old multi-stage engine (decompose/plan/expand/explore/paper-mine/synthesize/report,
hypotheses, paper hydration, planner, store) was removed.

---

## 2. Bugs found & fixed (each cost real score/budget)

1. **`ModuleNotFoundError: requests`** — paperclip (`#!/usr/bin/env python3`) resolved
   the uv-venv python (no `requests`). **Fix:** the MCP server scrubs `sys.prefix/bin`
   from PATH so system python (with `requests`) wins. Root cause was the env, not paperclip.
2. **MCP tools auto-cancelled in `codex exec`** — MCP tools default to requiring
   approval; non-interactive exec resolves that to "user cancelled." **Fix:**
   `mcp_servers.research.default_tools_approval_mode="approve"`.
3. **`fetch` returned a ~1000-char preview, not the paper** — `paperclip cat` truncates;
   `--full` is required. The agent was **reading ~7 % of every paper** (40-line previews
   vs ~580-line full text). **This was the single biggest quality bug.** Fixed with `--full`.
4. **Budget meter cross-read between concurrent runs** — `spent_usd` took the newest
   rollout. **Fix:** match the rollout whose `session_meta.cwd == run_dir`.
5. **Console-script path resolution** chased the venv `python` symlink to `/usr/bin`.
   **Fix:** `shutil.which` / `.venv/bin/...`, no `resolve()`.

---

## 3. Experiments & results

### 3a. Retrieval: serper vs paperclip (coverage of the 17 GT-supporting papers)

Title-oracle coverage test (upper bound — query each paper's exact title):

| channel | retrieved@5 | misses |
|---|---|---|
| **paperclip** (PMC corpus) | 14/17 | 2006, 2010, 2012 papers (incl. the SMC3 yeast paper) |
| **serper** (Scholar) | 17/17 | — |

**Finding:** serper has higher *coverage* (finds everything incl. old/out-of-corpus);
paperclip provides *readable full text* (serper returns snippets/links only). They're
**complementary** — serper = discovery, paperclip = reading. The 3 serper-only papers
are "discover but can't read" (not in paperclip → `fetch` can't read them).

### 3b. SMC3 deep dive (standalone, all fixes + handoff)

$10.41, 12 notes, 102 tool calls. Final list: PARP1/PARP2 (Class 2), GSK3A/B (2),
+ CHTF18/CHTF8/DSCC1/PAXIP1/PAGR1/MAU2/NIPBL/DDX11/TIPIN/WDHD1/WAPL (Class 3,
ortholog/indirect). **Score (discoverable GT, Class 1+2): AP 0.50, precision 0.50,
recall 0.40 (PARP1+PARP2 of 5).**

Why ATAD5/RFC5/SMC1A were still missed (all three from **one paper, PMID 20728441 =
Maradeo & Skibbens 2010, a *yeast* FEBS Lett paper**):
- That paper is **not in paperclip's corpus at all** (confirmed: exact-title + `--all`
  + fetch-by-id all fail). serper finds it, but `fetch` can't read it.
- The human papers the agent *did* read name the **alternative CTF18-RFC clamp**
  (CHTF18/CHTF8/DSCC1), not canonical RFC5 or ATAD5(ELG1) — biologically adjacent,
  wrong GT symbol.
- **SMC1A** is a cohesin core subunit; the agent (reasonably) treats it as a complex
  member, not a pairwise SL partner. It appeared in a note as "SL with WNT," not "with SMC3."

The serper→paperclip handoff *did* work: it discovered a **new 2023 human CRISPR paper**
that grounded the CHTF18/PAXIP1/PAGR1 candidates.

### 3c. Full 10-gene benchmark (proto2, $10 budget each, 4 concurrent)

Confident tier = Class 1+2.

| gene | discoverable: hit / AP | note |
|---|---|---|
| SMC3 | 2/5 · AP 1.00 | PARP1/PARP2 |
| UNG | 1/44 · AP 0.17 | |
| KLF10, TKT, PDGFA, NAMPT, MRPS18A, CDA, NARS2, TRRAP | 0 | — |

**Aggregate (mean over genes with non-empty GT):**

| GT / tier | mAP | recall | precision | hit@5 | MRR |
|---|---|---|---|---|---|
| discoverable, Class 1+2 | **0.167** | 0.060 | 0.190 | 0.286 | 0.214 |
| discoverable, all classes | 0.090 | 0.108 | 0.085 | 0.429 | 0.243 |
| literature, Class 1+2 | 0.117 | 0.031 | 0.133 | 0.200 | 0.150 |

**Cost: ~$118 research-phase (~$125–130 total).** Several genes overshot the $10 cap to
$20–24 (SMC3 $20.5, MRPS18A $23.9, NAMPT $22.2, NARS2 $21.9) — see finding #4 below.

---

## 4. Key findings / insights

1. **The score is ground-truth-modality-bound, not agent-bound.** Only 2/10 genes
   score. The agent produces sensible tiered candidates for every gene, but **most
   SynLethDB partners are screen/computational-derived** (GEMINI, "Mapping the Genetic
   Landscape," "Widespread genetic epistasis," siRNA screens) — table rows, not
   narrated text — which a literature-reading agent structurally cannot name. Where the
   GT comes from **narrative papers** (SMC3 → PARP), the agent nails it. So the benchmark
   as scored largely measures "is this SL pair written up in prose," and most aren't.
2. **The class hierarchy keeps precision honest.** At Class 1+2 precision is ~0.19
   (not spraying wrong answers); recall is GT-bound. Scored flat, the Class-3
   ortholog/screen candidates crater precision (~0.07–0.13) — so always read at a tier.
3. **Retrieval, not phrasing, is the binding constraint** for the misses. Better
   queries don't help when a paper isn't in paperclip's corpus; the ortholog mapping
   now works, but the *readability* of out-of-corpus papers is the wall.
4. **`--full` reading made cost decouple from the budget.** The budget meter caps
   search/fetch **ops**, not the **reasoning/reading tokens** (grepping 600–1400-line
   papers + long reasoning), so real cost ran 2×+ the nominal cap.
5. **GT quality issues exist.** PMID `3965078` ("supporting" a UNG pair) resolves to a
   1985 *Periosteal osteosarcoma* paper — a mis-citation. Several "literature" pairs
   rest on large computational screens.
6. **Budget usage trajectory** (the "stops too early" concern is fixed): SMC3 went
   $2.16 → $5.53 → $10.41 across the fixes, while staying grounded and tiered.

---

## 5. Open problems / what to try next (prioritized)

**A. Make the benchmark fair (cheap, high value).**
- **Strict-narrative GT re-score**: drop the big computational/screen source papers
  (keep only narrated/low-throughput pairs) and re-aggregate — the apples-to-apples
  number for a literature agent. (We have the per-paper source map.)
- Clean obvious GT mis-citations (e.g., the osteosarcoma paper).

**B. Close the readability gap (the main recall lever).**
- **`fetch`-beyond-paperclip**: resolve a serper hit / DOI / PMID to its open-access
  full text (or at least its abstract) and read that. Turns "serper found it" into
  "agent read it" — unlocks the out-of-corpus tail (e.g., the SMC3 yeast paper).
- **Citation-following tool**: extract a read paper's reference list, resolve each
  title/DOI to a fetchable id, fetch the new ones. The papers we read already cite
  straight into the right neighborhoods.

**C. Recover screen-derived partners (the other modality).**
- Add a **screen-data channel** (DepMap / BioGRID-ORCS / SynLethDB's own tables) so
  screen/computational partners are reachable at all — otherwise they're unscorable.
- Optional **complex/ortholog normalizer** (HGNC alias + CORUM/Reactome members +
  Alliance ortholog map) as a deterministic downstream pass, to recover class→member
  and yeast→human at scale (the prompt-side resolution helps but is per-run).

**D. Cost / efficiency.**
- Meter **reading tokens**, not just ops (or cap per-fetch grep volume / full-text
  size) so cost tracks the budget — the $20+ overshoots came from `--full` greps.
- Consider abstract-first triage before pulling full text.

**E. Scale / rigor.**
- Re-run the **realistic serper-only vs paperclip-only vs both** A/B (topical queries,
  not title-oracle) to quantify each channel's downstream contribution.
- Larger / cleaner gene sample; report variance (runs are stochastic, ±0.15 AP at n=1).

---

## 6. Where things live
- Agents: `src/graph_search/` (proto1), `src/skills_agent/` (proto2); skills in `.agents/skills/`.
- MCP server: `src/graph_search/mcp_server.py`; budget reader: `src/graph_search/spend.py`.
- Prompts: `src/graph_search/prompts/{research,finalize}.md`, `src/skills_agent/prompt.md`.
- Eval harness: `experiments/synlethdb/{sldata,extract_predictions,evaluate}.py` (parent repo).
- Benchmark driver + scorer (this run): `/tmp/bench/{run_all.sh,score_all.py,scores.json}`.
