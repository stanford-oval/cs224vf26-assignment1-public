"""The codex executor tasks (Methodology §3) — each a pure schema-constrained call.

| Task      | Role                                        | Mode     |
|-----------|---------------------------------------------|----------|
| PRIOR     | initial knowledge + candidate answers        | reason   |
| FIELDS    | parse the explicit asks from the Q           | reason   |
| GROUND    | nail one term + a SourceRef                  | research |
| PLAN      | rank the frontier AND allocate its budget    | reason   |
| EXPLORE   | investigate a direction → HYPOTHESES         | research |
| SCREEN    | stage 1: quick search — does this hold up?   | research |
| DEEP TEST | stage 2: hunt evidence AND counter-examples  | research |
| EVALUATE  | Reflexion reflection over the draft          | reason   |
| ARTIFACT  | build a deliverable in the git workspace     | research |

Each returns validated JSON (codex enforces the schema) plus the USD it cost. The
orchestrator decides what to do with the result; the model never sees the loop.
"""
from __future__ import annotations

from pathlib import Path

from . import schemas
from .codex_exec import run_task
from .ledger import Direction, Hypothesis, Ledger, _publisher_of, _real_authors


def _guard(guardrails: str) -> str:
    """A human-supplied scope/assumptions guardrail block (from ledger.guardrails_md), formatted for
    a prompt. Empty string when there is no steering context."""
    g = (guardrails or "").strip()
    return f"\n\nHUMAN STEERING (obey strictly):\n{g}\n" if g else ""


def _slice_for(ledger: Ledger, ctx: list[Hypothesis]) -> str:
    if not ctx:
        return "(nothing related in the ledger yet)"
    rows = []
    for h in ctx:
        sup, con = ledger.support_balance(h)
        rows.append(f"- [{h.status}] {h.text}  ({sup} for / {con} against)")
    return "\n".join(rows)


def _evidence_rules() -> str:
    return (
        "Every evidence item needs `text` (what the source says), `stance` relative to the "
        "hypothesis (supports / contradicts / neutral), exactly ONE real `source` with a "
        "resolvable DOI/PMID/PMC/URL (copy authors verbatim — never invent them), and any "
        "`numbers` it reports. Evidence with no resolvable source is DISCARDED on ingest. "
        "CONTRADICTING evidence is as valuable as supporting evidence — report it."
    )


# ── INIT executors ──────────────────────────────────────────────────────────

def fields(question: str, task_dir: Path, **kw) -> tuple[list[str], float]:
    prompt = (
        "Parse the EXPLICIT, separable asks from this research question. List each "
        "distinct thing the answer is required to deliver (a field, sub-question, or "
        "ranking criterion). Be literal — do not invent asks the question did not make.\n\n"
        f"QUESTION:\n{question}\n\nReturn JSON per the schema."
    )
    data, usd = run_task(task_dir, prompt, schemas.REQUIRED_FIELDS, mode="reason", **kw)
    return (list(data.get("required_fields") or []) if data else []), usd   # None on codex failure


def prior(question: str, task_dir: Path, **kw) -> tuple[dict, float]:
    prompt = (
        "You are a domain expert. From your own knowledge ONLY (no tools), give your "
        "starting position on this research question. Be concrete and falsifiable so each "
        "candidate answer can later be tested against the literature.\n\n"
        f"QUESTION:\n{question}\n\n"
        "Return JSON: `knowledge` (what you already know), `prior_hypothesis` (your best "
        "current answer), `candidate_answers` (specific answers to TEST — each an object with "
        "`answer`, a `confidence` in [0,1] = your calibrated probability it will hold up against "
        "the literature, and the `aspect` it concerns), `key_terms` (terminology to ground), "
        "`open_questions` (the most valuable directions to investigate first), and `assumptions` "
        "(the premises you are taking as GIVEN to produce this answer — interpretations of the "
        "question, scope, or facts you're assuming; each one that proved wrong could change the "
        "answer. State them plainly for the researcher)."
    )
    return run_task(task_dir, prompt, schemas.PRIOR, mode="reason", **kw)


def plan(question: str, items: list, round_usd: float, ceiling_usd: float, k: int,
         task_dir: Path, uncovered: list[str] | None = None, **kw) -> tuple[dict, float]:
    """THE BUDGET ALLOCATOR. One call that both ranks the frontier and decides how much money each
    direction is worth — the agent owns the allocation, the harness only enforces it. `items` is a
    list of (id, text, rationale). Returns ({id: {score, usd, rationale}}, usd_spent)."""
    listing = "\n".join(f"- id={iid}: {txt}" + (f"\n    (why: {why})" if why else "")
                        for iid, txt, why in items)
    gaps = ("\nSTILL UNANSWERED (directions that close these are worth more):\n"
            + "\n".join(f"  - {u}" for u in uncovered) if uncovered else "")
    prompt = (
        "You are allocating a research budget. Below are the open research directions for a "
        "question. Decide which to pursue NEXT and HOW MUCH MONEY each deserves.\n\n"
        f"QUESTION:\n{question}\n{gaps}\n\nOPEN DIRECTIONS:\n{listing}\n\n"
        f"You have ${round_usd:.2f} to hand out this round across AT MOST {k} directions. "
        f"No single direction may get more than ${ceiling_usd:.2f}. Spend on depth where the "
        "payoff justifies it and keep cheap looks cheap — an expensive direction should be "
        "expensive because it needs the searching, not because it sounds important.\n\n"
        "For each direction you choose, return `score` (0..1, value of pursuing it next), `usd` "
        f"(what to spend, 0 to skip it — the total must not exceed ${round_usd:.2f}), and a one-line "
        "`rationale` for the amount. Directions you skip may be omitted. Return JSON per the schema."
    )
    data, usd = run_task(task_dir, prompt, schemas.PLAN, mode="reason", **kw)
    out: dict[str, dict] = {}
    for r in ((data or {}).get("allocations") or []):
        rid = str(r.get("id", "")).strip()
        if rid:
            out[rid] = {"score": float(r.get("score", 0.0) or 0.0),
                        "usd": max(0.0, float(r.get("usd", 0.0) or 0.0)),
                        "rationale": str(r.get("rationale", "") or "")}
    return out, usd


def ground(term: str, question: str, task_dir: Path, budget_hint: float | None = None,
           guardrails: str = "", **kw) -> tuple[dict, float]:
    prompt = (
        f"Define the term \"{term}\" as it is used in the context of this question:\n"
        f"{question}\n\nSearch the web for an authoritative source, READ it, and return a "
        "precise definition plus a single resolvable SourceRef (real title/authors/year and "
        "a DOI, PMID, PMC, or URL). Do not invent author names — copy them from the source. "
        "Return JSON per the schema."
        + _guard(guardrails)
        + (f"\nBUDGET: ~${budget_hint:.2f} — one good source is enough; emit JSON promptly."
           if budget_hint else "")
    )
    return run_task(task_dir, prompt, schemas.GROUND, mode="research", **kw)


# ── MAIN-LOOP executors ─────────────────────────────────────────────────────

def explore(d: Direction, ctx: list[Hypothesis], ledger: Ledger, task_dir: Path,
            budget_hint: float | None = None, guardrails: str = "",
            **kw) -> tuple[dict, float]:
    """Investigate one direction and come back with HYPOTHESES — propositions that may or may not
    be true. Testing them is a separate, later stage; this task's job is to generate the candidates
    (with any evidence it happens to find) and to grow the frontier."""
    cap = (f"\n\nBUDGET: you have ${budget_hint:.2f} of model usage for THIS direction — it was "
           "allocated to you deliberately, so use it in proportion. Search, read, and EMIT THE JSON "
           "before you run out: a killed task returns nothing." if budget_hint else "")
    # Source-aware grounding: if the run selected paperclip corpora, retrieve real papers for this
    # direction and hand them to codex (which also web_searches). Empty/failure → web_search only.
    src_block = ""
    if getattr(ledger, "sources", None):
        try:
            from . import search
            src_block, _ = search.source_context(ledger.sources, d.question_text)
        except Exception:
            src_block = ""
    src_block = ("\n\n" + src_block) if src_block else ""
    prompt = (
        "You are a literature-research executor. Investigate ONE research direction and return the "
        "HYPOTHESES it raises. A hypothesis is a specific, FALSIFIABLE proposition that might or "
        "might not be true — not a summary and not a settled fact. Each will be tested against the "
        "literature afterwards, so state them sharply enough to be proved wrong."
        + _guard(guardrails) + cap + "\n\n"
        f"OVERALL QUESTION:\n{ledger.question}\n\n"
        f"DIRECTION TO EXPLORE:\n{d.question_text}\n"
        f"(why this matters: {d.rationale})\n\n"
        f"ALREADY ON THE BOARD (do not restate; extend, sharpen, or contradict):\n"
        f"{_slice_for(ledger, ctx)}"
        + src_block + "\n\n"
        "Return JSON with:\n"
        "- `hypotheses`: 3-8 propositions worth testing. Each has `text` (the proposition), "
        "`rationale` (why it is worth testing), `aspects` (1-3 free-form grouping tags — reuse the "
        "tags above when they fit), `confidence` (your prior P(true) in [0,1], BEFORE testing), and "
        "`evidence` (whatever you already found — may be empty; a hypothesis does not need evidence "
        "to be worth testing). " + _evidence_rules() + "\n"
        "- `new_directions`: promising follow-up sub-questions, each with a self-estimated "
        "`promise` (0..1, expected information gain about the overall question) and `est_cost` "
        "(rough USD to explore).\n"
        "- `dead_end`: true if this direction has nothing more worth pursuing."
    )
    return run_task(task_dir, prompt, schemas.EXPLORE, mode="research", **kw)


def screen(h: Hypothesis, question: str, task_dir: Path, budget_hint: float | None = None,
           guardrails: str = "", **kw) -> tuple[dict, float]:
    """STAGE 1 of the two-stage test. A quick web search asking one question: does this hypothesis
    make sense and have any footing in the literature? Cheap and shallow by design — its job is to
    stop nonsense from consuming a deep test, not to settle anything."""
    prompt = (
        "You are screening a research hypothesis. Do a QUICK web search — one or two queries — and "
        "judge only this: does the hypothesis MAKE SENSE and have some footing in the literature, "
        "such that an in-depth investigation is worth paying for?\n\n"
        f"OVERALL QUESTION:\n{question}\n\nHYPOTHESIS:\n{h.text}\n"
        f"(why it was proposed: {h.rationale})\n\n"
        "Set `plausible` false only when the quick look shows the hypothesis is incoherent, already "
        "clearly false, or has no footing at all in the literature. If you are unsure, set it TRUE — "
        "the in-depth test exists to decide, and a wrongly-screened-out hypothesis is a real loss. "
        "Give a one-line `note` on what you saw, your `confidence` P(true) after this quick look, and "
        "up to 2 `evidence` items if a source turned up. " + _evidence_rules()
        + _guard(guardrails)
        + (f"\n\nBUDGET: this is a CHEAP screen — stay under ${budget_hint:.2f}. Do not read deeply, "
           "do not chase citations, do not try to settle the question. Emit the JSON quickly."
           if budget_hint else "")
    )
    return run_task(task_dir, prompt, schemas.SCREEN, mode="research", **kw)


def answer_search(question: str, notes_so_far: str, task_dir: Path,
                  budget_hint: float | None = None, guardrails: str = "", **kw) -> tuple[dict, float]:
    """ABLATION baseline: no hypotheses, no belief ledger, no verdicts. Just search the literature
    and answer — the "plain RAG agent" the full pipeline is being measured against."""
    prompt = (
        "Answer a research question from the literature. Search, read what you find, and write what "
        "the literature actually says — specific findings, names and numbers, not a summary of the "
        "topic.\n\n"
        f"QUESTION:\n{question}\n\n"
        + (f"ALREADY COVERED (do not repeat; go further or go elsewhere):\n{notes_so_far[:6000]}\n\n"
           if notes_so_far.strip() else "")
        + "Return `answer_markdown` with what you found, `sources` for everything you cite, and "
          "`open_gaps` listing what you could not settle. Cite only sources you actually retrieved. "
        + _evidence_rules() + _guard(guardrails)
        + (f"\n\nBUDGET: stay under ${budget_hint:.2f}." if budget_hint else "")
    )
    return run_task(task_dir, prompt, schemas.ANSWER_SEARCH, mode="research", **kw)


def deep_test(h: Hypothesis, question: str, prior_evidence: str, task_dir: Path,
              budget_hint: float | None = None, guardrails: str = "", **kw) -> tuple[dict, float]:
    """STAGE 2. The expensive one: search extensively for evidence AND, specifically, for
    counter-examples. A hypothesis only reaches the pool if support survives a real attempt to
    contradict it — 'contested' is a legitimate verdict, not an indecision."""
    prompt = (
        "You are an ADVERSARIAL research investigator. Test this hypothesis against the literature "
        "EXTENSIVELY. Your job is not to confirm it — it is to find out whether it survives a "
        "serious attempt to break it.\n\n"
        f"OVERALL QUESTION:\n{question}\n\nHYPOTHESIS UNDER TEST:\n{h.text}\n"
        f"(why it was proposed: {h.rationale})\n\n"
        f"EVIDENCE ALREADY ATTACHED (verify it; do not just trust it):\n{prior_evidence}\n\n"
        "Steps:\n"
        "1. Search widely for evidence bearing on the hypothesis. Fetch and READ the sources — "
        "check that each is real and resolvable and that its authors, venue, and numbers are as cited.\n"
        "2. SEARCH SPECIFICALLY FOR COUNTER-EXAMPLES: contradicting studies, failed replications, "
        "negative results, populations where it does not hold, and stated limitations. Spend real "
        "effort here — evidence that only confirms means you did not look for the contradiction.\n"
        "3. Report EVERY source you used as an `evidence` item with its stance. " + _evidence_rules() + "\n"
        "4. Decide the `verdict`:\n"
        "   • \"supported\" — the literature supports it and a genuine search for counter-evidence "
        "found none that stands.\n"
        "   • \"conflicted\" — there is real support AND real contradiction. List each contradiction "
        "in `conflicts`. This is a finding; do not force it either way.\n"
        "   • \"refuted\" — the literature gives no support, or contradicts it outright.\n"
        "Give your `rationale`, your posterior `confidence` P(true) in [0,1], and any "
        "`new_directions` this investigation opened up."
        + _guard(guardrails)
        + (f"\n\nBUDGET: ~${budget_hint:.2f} for this test — this is the deep pass, so use it, but "
           "emit the JSON before you run out." if budget_hint else "")
    )
    return run_task(task_dir, prompt, schemas.DEEP_TEST, mode="research", **kw)


def _hypothesis_digest(ledger: Ledger, limit: int = 80) -> str:
    """Compact view of the pool + the bin, for the coverage judge and the evaluator."""
    rows = []
    for h in sorted(ledger.pool(), key=lambda h: -h.confidence)[:limit]:
        asp = ", ".join(h.aspects) or "(none)"
        sup, con = ledger.support_balance(h)
        rows.append(f"- [pooled] {h.text}  ({sup} for / {con} against; aspects: {asp})")
    for h in sorted(ledger.binned(), key=lambda h: -h.confidence)[: max(0, limit - len(rows))]:
        rows.append(f"- [binned: {h.verdict}] {h.text}  ({h.bin_reason[:80]})")
    return "\n".join(rows) or "(no tested hypotheses yet)"


def _finalize_digest(ledger: Ledger, limit: int = 220) -> str:
    """Numbered, source-grounded digest for FINALIZE — the pool first, then the deprioritised
    hypotheses (clearly labelled, with the reason), each with its sources and numbers."""
    rows: list[str] = []
    ordered = (sorted(ledger.pool(), key=lambda h: -h.confidence)
               + sorted(ledger.binned(), key=lambda h: -h.confidence))
    for i, h in enumerate(ordered[:limit], 1):
        tag = "POOLED" if h.status == "pooled" else f"DEPRIORITISED/{h.verdict}"
        sup, con = ledger.support_balance(h)
        nums: dict[str, object] = {}
        srcs = []
        for ev in ledger.evidence_for(h):
            nums.update(ev.numbers)
            s = ev.source
            if s.is_dataset():
                # A data finding has no author or year. Rendering it in the citation format yields
                # "(Unknown, n.d.)", which the report writer then copies inline as if it were a
                # paper with a missing author — so it is described as what it is: a computation.
                srcs.append(f"{ev.stance}: COMPUTED from the researcher's data "
                            f"[{s.dataset_id}] — {s.query}"
                            + (f" (script: {s.script})" if s.script else ""))
                continue
            loc = s.doi or (f"PMID:{s.pmid}" if s.pmid else None) or s.pmc or s.url or ""
            _au = _real_authors(s)
            auth = (_au[0] + (" et al." if len(_au) > 1 else "")) if _au else (_publisher_of(s) or "")
            srcs.append(f"{ev.stance}: {auth} ({s.year or 'n.d.'}) {s.title} {loc}".rstrip())
        num_s = "  ".join(f"{k}={v}" for k, v in nums.items())
        rows.append(f"[F{i}] ({tag}) {h.text}"
                    + (f"  | numbers: {num_s}" if num_s else "")
                    + (f"  | aspects: {', '.join(h.aspects)}" if h.aspects else "")
                    + f"  | balance: {sup} for / {con} against"
                    + (f"  | why deprioritised: {h.bin_reason}" if h.status == "binned" else "")
                    + ("".join(f"\n      SOURCE {s}" for s in srcs)))
    return "\n".join(rows) or "(no tested hypotheses)"


def patterns(ledger: Ledger, task_dir: Path, **kw) -> tuple[dict, float]:
    """Distill CROSS-CUTTING abstract patterns / hypotheses over the grounded findings —
    the domain-agnostic 'patterns' table from graph-search-sliders-2 (fixed 8 fields)."""
    prompt = (
        "You are a research synthesist. Across the grounded findings below, distill the "
        "CROSS-CUTTING abstract patterns — recurring structures, trade-offs, contradictions, "
        "or gaps that hold ACROSS multiple findings (not single-study facts). For each pattern "
        "give: `pattern` (the recurring observation), `abstraction` (the domain-agnostic "
        "generalization), `instance` (a concrete example from the findings), `direction` (a "
        "promising next research direction it implies), `support` (how strong the evidence is), "
        "`sources` (the supporting citations), `hypothesis` (a testable hypothesis it raises), "
        "and `novelty` (how non-obvious it is).\n\n"
        f"QUESTION:\n{ledger.question}\n\nGROUNDED FINDINGS:\n{_finalize_digest(ledger, limit=150)}\n\n"
        "Return JSON `patterns` = the strongest 4-8 cross-cutting patterns. Ground each in the "
        "findings above; do not invent."
    )
    return run_task(task_dir, prompt, schemas.PATTERNS, mode="reason", **kw)


def finalize_report(question: str, ledger: Ledger, patterns_rows: list[dict], task_dir: Path,
                    **kw) -> tuple[dict, float]:
    """Outline-then-fill final report: design a section outline from the question, then fill
    each section from the grounded findings + cross-cutting patterns. Returns {outline,
    report_markdown}."""
    asks = "\n".join(f"- {f}" for f in ledger.required_fields) or "(none parsed)"
    pats = ""
    for p in (patterns_rows or [])[:8]:
        pats += (f"- PATTERN: {p.get('pattern','')}\n  abstraction: {p.get('abstraction','')}\n"
                 f"  direction: {p.get('direction','')}\n  hypothesis: {p.get('hypothesis','')}\n")
    glossary = "\n".join(f"- {t}: {g.get('definition','')}" for t, g in (ledger.glossary or {}).items())
    prompt = (
        "You are writing the FINAL research report. Work in two steps and return BOTH.\n\n"
        "STEP 1 — OUTLINE: from the QUESTION and its EXPLICIT ASKS, design a section outline "
        "(`outline` = [{heading, intent}]). The outline MUST include whatever the question "
        "demands — in particular, if it asks to RANK items by credibility / translational "
        "readiness, include an explicit ranked section. Cover every explicit ask.\n\n"
        "STEP 2 — FILL: write `report_markdown`, a comprehensive markdown report that follows "
        "your outline and fills each section USING ONLY the tested hypotheses below. Rules:\n"
        "  • Cite sources inline exactly as given (author, year, DOI/PMID) — NEVER invent a "
        "source or a number; use only what the findings provide.\n"
        "  • ALSO tag every claim with the finding id(s) it rests on — the [F#] labels in the "
        "GROUNDED FINDINGS below — written bare, like F7 or (F7; F8), next to the sentence they "
        "support. The reader's interface turns these into links to the underlying evidence, so a "
        "claim without one cannot be traced. Use the ids exactly as given; never invent one.\n"
        "  • A finding marked COMPUTED came from the researcher's OWN data, not the literature. It "
        "has no author, year or DOI — never write \"(Unknown, n.d.)\" or invent a citation for one. "
        "Attribute it to the data instead (e.g. \"computed from your cohort data\"); the operation "
        "and its assumptions are listed in the report's Data sources section. Where a claim rests on "
        "BOTH your data and the literature, say which part came from which — that distinction is the "
        "point, and its confidence is only as strong as the weaker half.\n"
        "  • Build the answer from the POOLED hypotheses. DEPRIORITISED ones were not discarded: "
        "where they matter, report them in a clearly-labelled section with the reason they were "
        "set aside (refuted / contested) — a contested hypothesis is a real finding about the "
        "state of the literature.\n"
        "  • Where the question asks for per-item attributes (e.g. marker, sample, technology, "
        "cohort sizes, AUC/sensitivity/specificity, study type), present them compactly "
        "(tables are good).\n"
        "  • Use the cross-cutting PATTERNS for a synthesis / open-questions section.\n\n"
        f"QUESTION:\n{question}\n\nEXPLICIT ASKS (cover all):\n{asks}\n\n"
        + _guard(ledger.guardrails_md())
        + ("\nIf assumptions were given above, open the report with a short **Given assumptions** "
           "section listing them (state they were taken as premises, not verified).\n"
           if ledger.assumptions else "")
        + (f"GLOSSARY:\n{glossary}\n\n" if glossary else "")
        + (f"CROSS-CUTTING PATTERNS:\n{pats}\n" if pats else "")
        + f"\nGROUNDED FINDINGS:\n{_finalize_digest(ledger)}\n\n"
        "Return JSON {outline, report_markdown}."
    )
    return run_task(task_dir, prompt, schemas.FINALIZE, mode="reason", **kw)


AUTO_ARTIFACT_SPEC = (
    "Build the two or three things that would most help a domain researcher UNDERSTAND THE ANSWER "
    "to the question — figures and tables about the SUBJECT MATTER.\n\n"
    "Think about what this field would put in a paper: the candidates or methods compared on their "
    "real reported measurements; how a quantity varies across groups, doses, cohorts or time; a "
    "ranked table of the entities the question asks about with their actual numbers and sources; "
    "where the literature agrees and where it genuinely splits, expressed in the domain's own terms. "
    "The best artifact usually makes ONE comparison the question cares about immediately legible.\n\n"
    "If the findings carry too few comparable numbers to plot honestly, say so in `caveats` and ship "
    "a well-built table instead. Never manufacture a chart just to have one."
)


def answer_question(question: str, ledger: Ledger, report: str, state_note: str,
                    task_dir: Path, **kw) -> tuple[dict, float]:
    """Answer a researcher's QUESTION from what the run already holds (DESIGN_interactive.md).

    Deliberately `reason` mode: this reports on the run, it does not extend it. If the answer is not
    in the ledger the honest reply is "the run doesn't settle this" plus a steer that WOULD settle
    it — quietly going and researching it here would spend budget the user never authorised and
    bypass the two-stage test everything else goes through.
    """
    prompt = (
        "A researcher is watching a live research run and has asked you a question about it. Answer "
        "them from the run's own findings below — clearly, in their terms, and without padding.\n\n"
        f"THE RUN'S QUESTION:\n{ledger.question}\n\n"
        f"THEY ASKED:\n{question}\n\n"
        f"WHERE THE RUN STANDS:\n{state_note}\n\n"
        + (f"THE CURRENT REPORT:\n{report[:14000]}\n\n" if report.strip() else "")
        + f"THE TESTED FINDINGS (pooled first, then deprioritised with the reason why):\n"
          f"{_finalize_digest(ledger, limit=90)}\n\n"
        "RULES:\n"
        "  • Answer ONLY from the material above. You have no search tool here, and inventing a "
        "fact would be worse than admitting a gap.\n"
        "  • If the run does not actually settle their question, say so plainly and set `confident` "
        "false. A deprioritised or contested finding is a real answer — give the reason it was set "
        "aside, don't hide it.\n"
        "  • Cite what you rely on in `basis`: source authors/DOIs where the finding carries them, "
        "or the computation for a finding derived from the researcher's own data.\n"
        "  • Do not describe the machinery — no hypothesis ids, no pooled/binned vocabulary, no "
        "confidence scores. They asked about the subject, not the pipeline.\n\n"
        "THEN OFFER A NEXT STEP. Based on what you just told them, propose ONE concrete thing the "
        "agent could do that would genuinely help — close the gap you found, resolve the "
        "contradiction, chase the promising lead. Write `suggested_steer` as a ready-to-send "
        "instruction TO the agent (\"investigate X in Y population\", \"restrict to trials since "
        "2020\"), and `suggest_reason` as one line on why it helps. If the answer honestly implies "
        "no useful next step, set both to null — a manufactured suggestion wastes their money."
    )
    return run_task(task_dir, prompt, schemas.ANSWER_QUESTION, mode="reason", **kw)


# ── the data plane (DESIGN_data_plane.md) ───────────────────────────────────

def classify_request(question: str, inputs_manifest: str, task_dir: Path,
                     **kw) -> tuple[dict, float]:
    """Which KINDS of claim does this request need? (§3.2) Not "research vs task" — that has no
    correct answer for a composite ask like "get the overlap from my CSV, then find which are
    relevant to pathway X", which needs both and in that order."""
    prompt = (
        "Decide what kinds of claim this request requires. There are two, with different ways of "
        "being established:\n\n"
        "  • a claim about the RESEARCHER'S DATA — settled by computing over the files below "
        "(an overlap, a count, a ranking, a filter). No literature involved.\n"
        "  • a claim about the WORLD — settled by evidence from the literature (does X cause Y, "
        "is marker M credible, what does the field report). No amount of computing over a private "
        "file can settle it.\n\n"
        f"REQUEST:\n{question}\n\n"
        f"THE RESEARCHER'S DATA (what is actually available):\n{inputs_manifest}\n\n"
        "Return:\n"
        "- `kind`: \"data_only\" (everything asked for is computable from the files), "
        "\"research_only\" (nothing needs the files), or \"both\".\n"
        "- `data_ask`: exactly what must be computed from the data ('' if none).\n"
        "- `research_ask`: exactly what must be established from the literature ('' if none). "
        "For \"both\", write this as it applies TO THE RESULT of the data step.\n"
        "- `rationale`: one line.\n"
        "- `ambiguities`: anything the request leaves genuinely open that changes the answer — "
        "e.g. which column identifies an entity, what \"overlapping\" means, how to treat blanks. "
        "Be concrete and list only real ambiguities, not hypothetical ones."
    )
    return run_task(task_dir, prompt, schemas.CLASSIFY_REQUEST, mode="reason", **kw)


def data_query(ask: str, question: str, inputs_manifest: str, prior_work: str, task_dir: Path,
               budget_hint: float | None = None, guardrails: str = "",
               python_bin: str = "python3", **kw) -> tuple[dict, float]:
    """Answer a question FROM THE RESEARCHER'S DATA by writing and running a script in the
    workspace. Like `artifact` its real output is files; the JSON is its report.

    The declared `assumptions` are the point, not paperwork: a query silently fixes interpretive
    choices (which column is the identity, what counts as present, how blanks are treated) and each
    one changes the answer. Stated, they can be reviewed and corrected; unstated, the number just
    appears (§4.3)."""
    prompt = (
        "You are answering a question FROM THE RESEARCHER'S OWN DATA. Your working directory is a "
        "git repository; `inputs/` holds their files.\n\n"
        f"WHAT TO COMPUTE:\n{ask}\n\n"
        f"THE OVERALL QUESTION this serves:\n{question}\n\n"
        f"THE DATA:\n{inputs_manifest}\n\n"
        "HOW TO WORK:\n"
        f"1. LOOK at the data first ({python_bin} has pandas and numpy). Check the real columns, "
        "dtypes, blanks and duplicates before deciding what to compute — not what you assume is "
        "there.\n"
        "2. Write your code to `scripts/` and RUN it. Never hand-write a result you should have "
        "computed, and never transcribe numbers by eye.\n"
        "3. Write the full result to `artifacts/` (CSV for a table) so it can be checked.\n"
        "4. `git add -A && git commit`. If the sandbox refuses, leave the files — they are picked "
        "up anyway.\n\n"
        "RULES:\n"
        "  • `inputs/` is READ-ONLY. Never modify or overwrite the researcher's files.\n"
        "  • Every number you report must come from the data. If the data cannot answer part of "
        "the ask, say so in `caveats` — a silently narrowed answer is worse than a stated gap.\n"
        "  • State your ASSUMPTIONS explicitly — every interpretive choice your script made that "
        "someone could reasonably have made differently: which column identifies an entity, what "
        "counts as present/overlapping, how blanks and duplicates were treated, whether matching "
        "was case-sensitive. These get reviewed, so an empty list is only correct if the operation "
        "genuinely admitted no choices.\n"
        "  • `claims` are the FINDINGS a reader should take away, each specific and checkable "
        "against your result file — not a description of what you did.\n"
        + _guard(guardrails)
        + (f"\nBUDGET: ~${budget_hint:.2f}. Inspect, compute, write the result, emit the JSON."
           if budget_hint else "")
        + (f"\n\nALREADY COMPUTED (build on it; do not redo):\n{prior_work}" if prior_work else "")
        + "\n\nReturn JSON per the schema. `dataset_id` must be copied exactly from the manifest "
          "above, and `script`/`result_path` must be real workspace-relative paths you created."
    )
    return run_task(task_dir, prompt, schemas.DATA_QUERY, mode="research", **kw)


def judge_query(claim_text: str, query: str, assumptions: list[str], script_src: str,
                inputs_manifest: str, task_dir: Path, **kw) -> tuple[dict, float]:
    """Verify a data claim by READING the script that produced it (§4.3).

    Re-running it would prove only repeatability — guaranteed for deterministic code over an
    unchanged file, and equally true of a wrong answer. Reading it is what can catch the failure
    that actually happens: a script that runs cleanly and computes the wrong thing."""
    asm = "\n".join(f"  - {a}" for a in (assumptions or [])) or "  (none declared)"
    prompt = (
        "You are reviewing the CODE behind a claim someone derived from a data file. Decide "
        "whether the script actually computes what the claim says. Read it closely — it ran "
        "without error, so syntax is not the question; correctness is.\n\n"
        f"THE CLAIM:\n{claim_text}\n\n"
        f"WHAT IT SAYS IT DID:\n{query}\n\n"
        f"THE ASSUMPTIONS IT DECLARED:\n{asm}\n\n"
        f"THE DATA IT RAN OVER:\n{inputs_manifest}\n\n"
        f"THE SCRIPT:\n```python\n{script_src[:12000]}\n```\n\n"
        "Look specifically for: the wrong column used; a join or merge that silently drops rows; a "
        "filter that removes more than intended; blanks/NaN treated in a way the claim does not "
        "reflect; duplicates double-counting; case or whitespace mismatches in key columns; a "
        "result that does not actually support the claim as worded.\n\n"
        "Also list any `unstated_assumptions` — interpretive choices the script makes that are NOT "
        "in the declared list. An undeclared choice is the most common way one of these is wrong.\n\n"
        "`verdict`: \"correct\" (computes what the claim says), \"wrong_script\" (a real defect — "
        "it computes something else), or \"questionable_assumptions\" (the code is right for the "
        "assumptions it made, but a reasonable person would have chosen differently — this is a "
        "question for the researcher, not a defect). Give `confidence` in [0,1] and a one-line "
        "`note`. Judge only from the script and the data description; do not consult the literature."
    )
    return run_task(task_dir, prompt, schemas.JUDGE_QUERY, mode="reason", **kw)


def artifact(spec: str, kind: str, question: str, ledger: Ledger, data_manifest: str,
             existing: str, task_dir: Path, budget_hint: float | None = None,
             guardrails: str = "", python_bin: str = "python3", **kw) -> tuple[dict, float]:
    """Build a DELIVERABLE in the run's git workspace — a chart, a CSV, a table, a document.

    Unlike every other executor this one's output is FILES, not JSON: it runs with the workspace as
    its cwd (so workspace-write lets it create them) and the harness commits whatever appears. The
    returned JSON is a declaration of what it built, used for titles in the index.

    The whole belief state is already exported to `data/` as JSON + CSV, so the task computes over
    real files rather than transcribing numbers out of a prompt — which is also the mechanism that
    keeps artifact numbers traceable to the same sources the report cites.
    """
    asks = "; ".join(ledger.required_fields) or "(not parsed)"
    state = (f"{len(ledger.pool())} pooled / {len(ledger.binned())} deprioritised hypotheses, "
             f"{len(ledger.evidence)} sourced evidence items")
    prompt = (
        "You are building a research DELIVERABLE. Your working directory is a git repository that "
        "belongs to ONE research question, and it is yours to work in: create files, write and run "
        "code, and commit.\n\n"
        f"THE REQUEST (what the researcher asked for):\n{spec}\n"
        + (f"(they asked for it as a {kind})\n" if kind else "")
        + f"\nTHE RESEARCH QUESTION this run is answering:\n{question}\n"
        + f"What the answer must deliver: {asks}\n"
        + f"What the run has to work with: {state}.\n\n"
        "THE DATA — already exported for you into `data/`, straight from the run's belief ledger:\n"
        f"{data_manifest}\n\n"
        "`findings.csv` is one row per tested hypothesis, `evidence.csv` one row per sourced "
        "evidence item, and `metrics.csv` is long format — one row per number any source reported, "
        "with the source it came from. `findings.json` has the same content nested, with full source "
        "records. `report.md` is the written answer when the run has produced one.\n\n"
        "WHO THIS IS FOR — read this before choosing what to build. Your reader is a researcher in "
        "the field who wants to understand THE ANSWER TO THE QUESTION. They do not know this "
        "pipeline exists, did not run it, and have no interest in how it worked internally.\n"
        "  • BUILD artifacts about the SUBJECT MATTER: the markers, methods, genes, cohorts, "
        "models or interventions the question is about, and the real measurements reported for them "
        "— AUC, sensitivity, effect size, expression, sample size, year, cost, whatever this field "
        "actually reports. `metrics.csv` and the `numbers` fields are where that substance lives, "
        "and `inputs/` if the researcher supplied their own data.\n"
        "  • DO NOT build artifacts about the pipeline's own bookkeeping. No counts of hypotheses "
        "by status or verdict, no pooled-vs-deprioritised breakdown, no confidence scores or their "
        "distribution, no supporting-vs-contradicting source tallies, no coverage or budget "
        "figures, no hypothesis/direction ids as chart categories. A plot of how many hypotheses "
        "were supported tells the reader nothing about their research question.\n"
        "  • Use `status`/`verdict`/`confidence` the way they are meant: to FILTER (build from what "
        "was supported, and label anything contested as contested) and to carry provenance — never "
        "as the subject of a figure. Where a finding is genuinely contested, show the disagreement "
        "in the domain's terms (the two conflicting values and who reported them), not as a count.\n\n"
        "HOW TO WORK:\n"
        f"1. Look at the data first ({python_bin} has pandas, numpy and matplotlib). Understand what "
        "is actually in it before deciding what to build — the honest artifact is the one the data "
        "supports, not the one the request imagined.\n"
        "2. Write the code that builds the artifact into `scripts/` and RUN it, so the result is "
        "reproducible. Do not hand-write output files that should have been computed.\n"
        "3. Save deliverables under `artifacts/` with descriptive snake_case names.\n"
        "4. `git add -A && git commit` your work with a clear message. If git is unavailable or the "
        "sandbox refuses it, just leave the files in place — they will still be picked up.\n\n"
        "RULES:\n"
        "  • EVERY number must come from `data/`. Never invent, extrapolate, or fill a gap with a "
        "plausible value. If the data cannot answer part of the request, build what it can support "
        "and put the rest in `caveats`.\n"
        "  • Carry provenance through: a table gets source/DOI columns, a chart names its source in "
        "a caption or a companion `.md` next to it.\n"
        "  • Charts: matplotlib with the Agg backend, `MPLCONFIGDIR=$PWD/.mplcache`. Titled, axes "
        "labelled with units, readable at half size, no chartjunk, and a colour-blind-safe palette. "
        "Save PNG at dpi=160. One clear comparison beats a busy dashboard.\n"
        "  • Do NOT edit anything under `data/` — the harness overwrites it on every export.\n"
        + (f"\nALREADY IN THE WORKSPACE (extend or supersede rather than duplicate):\n{existing}\n"
           if existing else "")
        + _guard(guardrails)
        + (f"\nBUDGET: ~${budget_hint:.2f} for this build. Inspect, build, commit, and emit the JSON "
           "before you run out — a killed task still leaves its files, but loses the description."
           if budget_hint else "")
        + "\n\nReturn JSON: `artifacts` (one entry per file you produced, `path` relative to the "
          "workspace root), `summary`, `committed`, and `caveats` (anything the data could not "
          "support — be explicit; a silently narrowed deliverable is worse than a stated gap)."
    )
    return run_task(task_dir, prompt, schemas.ARTIFACT, mode="research", **kw)


def judge_coverage(ledger: Ledger, task_dir: Path, **kw) -> tuple[dict, float]:
    """LLM judge for covered(field) — replaces the lexical faithfulness/coverage proxy.
    For each explicit ask, decide whether a grounded claim genuinely answers it."""
    asks = "\n".join(f"- {f}" for f in ledger.required_fields) or "(none)"
    prompt = (
        "You are judging COVERAGE of a research question's explicit asks against the "
        "hypotheses tested so far. For each ask, decide whether at least one POOLED "
        "hypothesis genuinely ANSWERS it (not merely mentions it), and list which aspect "
        "tags contribute. Deprioritised hypotheses do NOT count as coverage.\n\n"
        f"QUESTION:\n{ledger.question}\n\nEXPLICIT ASKS:\n{asks}\n\n"
        + _guard(ledger.guardrails_md())
        + f"TESTED HYPOTHESES:\n{_hypothesis_digest(ledger)}\n\n"
        "Return JSON: `fields` = one entry per ask with `covered` (bool) and "
        "`contributing_aspects`. Be strict: covered only if a pooled hypothesis "
        "substantively addresses the ask."
    )
    return run_task(task_dir, prompt, schemas.JUDGE_COVERAGE, mode="reason", **kw)


def judge_forward(ledger: Ledger, directions: list[Direction], task_dir: Path,
                  **kw) -> tuple[dict, float]:
    """LLM judge for q(d) — score each OPEN direction as testable AND non-obvious.
    Replaces using the model's self-reported promise as the forward-looking proxy."""
    listing = "\n".join(f"- id={d.id}: {d.question_text}" for d in directions) or "(none)"
    prompt = (
        "You are scoring candidate next research directions. For each, give a 0..1 score "
        "for how TESTABLE and NON-OBVIOUS it is (high = a sharp, answerable, "
        "information-rich question that isn't already trivially known).\n\n"
        f"OVERALL QUESTION:\n{ledger.question}\n\nDIRECTIONS:\n{listing}\n\n"
        "Return JSON `directions` = one {id, score} per direction above."
    )
    return run_task(task_dir, prompt, schemas.JUDGE_FORWARD, mode="reason", **kw)


def evaluate(draft: str, prev_draft: str, ledger: Ledger, rubric: str,
             task_dir: Path, **kw) -> tuple[dict, float]:
    asks = "\n".join(f"- {f}" for f in ledger.required_fields) or "(none parsed)"
    prompt = (
        "You are a research-run evaluator (Reflexion-style). Compare the CURRENT draft to the "
        "PREVIOUS one and steer the next round. Score each axis intrinsically (0..1, for "
        "steering only) and propose concrete corrective directions for the weakest axis.\n\n"
        f"OVERALL QUESTION:\n{ledger.question}\n\nEXPLICIT ASKS (faithfulness checklist):\n{asks}\n\n"
        f"RUBRIC AXES: {rubric}\n\n"
        f"PREVIOUS DRAFT:\n{prev_draft or '(none — first checkpoint)'}\n\n"
        f"CURRENT DRAFT:\n{draft}\n\n"
        "Return JSON with `per_axis_intrinsics` (correctness/completeness/forward_looking/"
        "faithfulness, each {score, note}), `weakest_axis`, `corrective_directions` (testable, "
        "non-obvious next sub-questions with promise+est_cost, aimed at the weakest axis), and "
        "`regressions` (anything the current draft lost vs the previous one)."
    )
    return run_task(task_dir, prompt, schemas.EVALUATE, mode="reason", **kw)
