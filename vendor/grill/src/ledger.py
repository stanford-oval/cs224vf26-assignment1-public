"""The belief ledger — a typed graph that is the v2 blackboard (Methodology §2).

The orchestrator owns this state; the LLM never holds it. Every mutation here is
deterministic Python (no model call), which is what lets the harness *enforce
provenance*, *manage the frontier*, and *never forget anything it has seen*.

Three first-class objects:

    Direction   the frontier — a research direction to investigate, with the USD the
                agent allocated to it
    Hypothesis  a proposition that may or may not be true, generated inside a direction
    Evidence    ONE sourced statement bearing on ONE hypothesis, with a stance
                (supports / contradicts / neutral) and a SourceRef

A hypothesis moves PROPOSED → (screen) → SCREENED → (deep test) → POOLED or BINNED.
**Nothing is ever discarded.** A hypothesis that fails the screen, is refuted, or stays
contested goes to the BIN with a reason — it remains in the ledger, is rendered in the
report, and can be resurfaced by later corroborating evidence.

There is deliberately no Entity type; grouping is done with free-form ``aspects[]`` tags
so the ledger works for entity-ranking tasks and open-problem/mechanism tasks alike.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# direction statuses
OPEN, EXPLORING, CLOSED, EXPLORED = "OPEN", "EXPLORING", "CLOSED", "EXPLORED"

# hypothesis lifecycle
PROPOSED = "proposed"    # generated, not yet screened
SCREENED = "screened"    # passed the quick screen; queued for the in-depth test
POOLED = "pooled"        # deep-tested and supported → the hypothesis pool (the answer material)
BINNED = "binned"        # deprioritised: screen-failed, refuted, or contested. RETAINED and resurfacable.

# deep-test verdicts
UNTESTED = "untested"
SUPPORTED = "supported"      # evidence supports it and no contradiction survived
CONFLICTED = "conflicted"    # real support AND real contradiction — genuinely contested
REFUTED = "refuted"          # the literature gives no support, or contradicts it

# evidence stance, relative to its hypothesis
SUPPORTS, CONTRADICTS, NEUTRAL = "supports", "contradicts", "neutral"


@dataclass
class SourceRef:
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmc: Optional[str] = None
    url: Optional[str] = None
    quote: Optional[str] = None
    verified: bool = False           # the source was fetched and checked, not just cited
    # ── the user's own data as a source (DESIGN_data_plane.md §4.1) ──────────
    # kind "dataset" evidence is produced by running a script over a file the researcher supplied.
    # Its provenance is not a citation but the script itself: readable, and pinned to exact bytes
    # via a content-addressed dataset_id.
    kind: str = "literature"         # literature | dataset
    dataset_id: str = ""             # "<name>@<12-hex sha256>" — pins the exact file contents
    query: str = ""                  # what was computed (a one-line description of the operation)
    script: str = ""                 # workspace-relative path to the code that produced it
    assumptions: list[str] = field(default_factory=list)   # the interpretive choices it fixed
    rows: Optional[int] = None       # rows the operation returned — a cheap sanity signal

    def is_dataset(self) -> bool:
        return self.kind == "dataset"

    def resolvable(self) -> bool:
        """Resolvable = "someone else could check this". For literature that means a locator; for
        data it means the exact file plus the operation run over it (§4.1)."""
        if self.is_dataset():
            return bool(self.dataset_id and (self.query or self.script))
        return bool(self.doi or self.pmid or self.pmc or self.url)

    def key(self) -> str:
        """Identity for DEDUP — "is this the same evidence item?". Two different operations over
        one dataset are two different findings, so the operation is part of the key."""
        if self.is_dataset():
            import hashlib
            op = f"{self.query}{self.script}"
            return f"{self.dataset_id}#{hashlib.sha1(op.encode('utf-8')).hexdigest()[:12]}"
        for v in (self.doi, self.pmid, self.pmc, self.url):
            if v:
                return str(v).strip().lower()
        return (self.title or "").strip().lower()

    def independence_key(self) -> str:
        """Identity for INDEPENDENCE — "how many separate sources back this?". Ten queries against
        one CSV are ten findings but ONE source, so they must not read as ten-fold corroboration
        (§2.3). For literature this is the same as key(); only datasets collapse."""
        return self.dataset_id if self.is_dataset() else self.key()

    def title_key(self) -> str:
        """Title-based identity for dedup: the SAME paper often appears under several locators (arXiv
        DOI vs published DOI vs OpenReview vs a PDF url), so keying on the locator leaves duplicates.
        Normalise the title to alphanumerics only (folds curly quotes, punctuation, case, whitespace)."""
        import re
        import unicodedata
        t = unicodedata.normalize("NFKD", self.title or "")
        t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
        return t or self.key()   # fall back to locator when there's no title

    @classmethod
    def from_json(cls, d: dict) -> "SourceRef":
        d = d or {}
        return cls(
            title=d.get("title", "") or "",
            authors=list(d.get("authors") or []),
            year=d.get("year"), journal=d.get("journal"),
            doi=d.get("doi"), pmid=d.get("pmid"), pmc=d.get("pmc"),
            url=d.get("url"), quote=d.get("quote"),
            verified=bool(d.get("verified", False)),
            kind=(d.get("kind") or "literature"),
            dataset_id=(d.get("dataset_id") or ""),
            query=(d.get("query") or ""),
            script=(d.get("script") or ""),
            assumptions=list(d.get("assumptions") or []),
            rows=d.get("rows"),
        )


@dataclass
class Evidence:
    """One sourced statement bearing on one hypothesis. An Evidence item carries exactly ONE
    source — 'this paper says X' — so a hypothesis's support balance is just a count over
    independent sources."""
    id: str
    text: str
    source: SourceRef = field(default_factory=SourceRef)
    stance: str = SUPPORTS
    hypothesis_id: Optional[str] = None
    numbers: dict[str, object] = field(default_factory=dict)
    phase: str = "explore"           # explore | screen | deep — which task turned it up
    origin: str = "agent"            # agent | human

    def resolvable(self) -> bool:
        return self.source.resolvable()


@dataclass
class Hypothesis:
    """A proposition that may or may not be true. The unit the loop tests."""
    id: str
    text: str
    direction_id: Optional[str] = None
    rationale: str = ""
    aspects: list[str] = field(default_factory=list)
    status: str = PROPOSED
    verdict: str = UNTESTED
    confidence: float = 0.5          # belief P(true); moved by screen, deep test, corroboration
    evidence_ids: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)   # the contradictions the deep test surfaced
    screen_note: str = ""
    bin_reason: str = ""             # why it was deprioritised (never empty when status == BINNED)
    test_attempts: int = 0           # bounded re-testing (the peeking guard)
    parent_id: Optional[str] = None  # the hypothesis this one refines
    origin: str = "agent"            # agent | prior | human — human rulings are gold, never overwritten
    pinned: bool = False             # human-accepted → never re-tested, never re-queued

    def grounded(self) -> bool:
        """Provenance gate (§2): a hypothesis is grounded once it carries at least one
        resolvable source. Only grounded hypotheses reach the report body."""
        return bool(self.evidence_ids)


@dataclass
class Direction:
    id: str
    question_text: str
    parent_id: Optional[str] = None
    rationale: str = ""
    status: str = OPEN
    promise: float = 0.0
    est_cost: float = 0.0
    allocated_usd: float = 0.0       # what the agent's planner allocated to this direction
    spent_usd: float = 0.0           # what exploring it actually cost
    alloc_rationale: str = ""        # why the planner allocated that much
    produced_hypotheses: list[str] = field(default_factory=list)
    tests_hypothesis_id: Optional[str] = None   # the hypothesis this direction re-investigates
    origin: str = "agent"            # agent | human — human directions are never GC'd


@dataclass
class Prior:
    """The PRIOR executor's parametric-knowledge starting position."""
    text: str = ""
    candidate_answers: list[str] = field(default_factory=list)


# Author-less sources are usually databases/registries/docs. Name the publisher rather than
# printing "Unknown", which reads like a citation the pipeline failed to resolve.
_PUBLISHERS = [
    ("ncbi.nlm.nih.gov/clinvar", "ClinVar (NCBI)"),
    ("ncbi.nlm.nih.gov/gene", "NCBI Gene"),
    ("ncbi.nlm.nih.gov", "NCBI"),
    ("omim.org", "OMIM"),
    ("clinicaltrials.gov", "ClinicalTrials.gov"),
    ("ebi.ac.uk", "EMBL-EBI"),
    ("uniprot.org", "UniProt"),
    ("ensembl.org", "Ensembl"),
    ("genecards.org", "GeneCards"),
    ("orpha.net", "Orphanet"),
    ("who.int", "World Health Organization"),
    ("fda.gov", "U.S. Food and Drug Administration"),
    ("nih.gov", "NIH"),
    ("github.com", "GitHub"),
    ("huggingface.co", "Hugging Face"),
]


# Extractors sometimes emit a literal placeholder as the author name. Treated as no author at
# all, so the publisher fallback applies instead of printing "unknown et al. (2023)".
_NON_AUTHORS = {"unknown", "unknown author", "anonymous", "anon", "n/a", "na", "none", "-", "",
                "not available", "no author", "et al", "et al."}


def _real_authors(s) -> list:
    return [a for a in (getattr(s, "authors", None) or [])
            if str(a).strip().lower().strip(".") not in _NON_AUTHORS]


def _publisher_of(s) -> str:
    """A human-readable publisher for an author-less source, from its URL host (or the
    ' - Publisher - Site' tail many database page titles carry). '' if nothing sensible."""
    url = (getattr(s, "url", "") or "").lower()
    for frag, name in _PUBLISHERS:
        if frag in url:
            return name
    title = getattr(s, "title", "") or ""
    if " - " in title:                       # e.g. "…congenital variant - ClinVar - NCBI"
        tail = [p.strip() for p in title.split(" - ") if p.strip()]
        if len(tail) >= 2 and len(tail[-1]) <= 24:
            return " ".join(tail[-2:]) if len(tail[-2]) <= 24 else tail[-1]
    if url:
        try:
            import urllib.parse
            host = urllib.parse.urlparse(url).netloc
            return host[4:] if host.startswith("www.") else host
        except Exception:
            pass
    return ""


def _numbers_to_dict(pairs) -> dict:
    """Fold the schema's [{metric, value}] array back into a dict."""
    out: dict[str, object] = {}
    for p in pairs or []:
        m = str(p.get("metric", "")).strip()
        if m:
            out[m] = p.get("value")
    return out


def _ca_text(c) -> str:
    """A PRIOR candidate answer's text — accepts a plain string (legacy) or a {answer,...} object."""
    return (c.get("answer", "") if isinstance(c, dict) else str(c)).strip()


def _ca_conf(c) -> float:
    return float(c.get("confidence", 0.5)) if isinstance(c, dict) else 0.5


def _ca_aspect(c) -> str:
    return (c.get("aspect", "") if isinstance(c, dict) else "").strip()


class Ledger:
    """The blackboard. All state lives here; the orchestrator is its only writer."""

    def __init__(self, question: str):
        self.question = question
        self.required_fields: list[str] = []
        self.glossary: dict[str, dict] = {}
        # Human-supplied context, persisted and threaded into executor prompts.
        # constraints = SCOPE filters (what to search); assumptions = GIVENS (treat as true, do not test).
        self.constraints: list[str] = []
        self.assumptions: list[str] = []
        self.sources: list[str] = []   # paperclip corpora to search (arxiv/pmc/…); empty = web_search only
        # The researcher's own data files staged into workspace/inputs/ (DESIGN_data_plane.md).
        self.datasets: list[dict] = []  # {dataset_id, name, path, sha256, columns, rows}
        self.prior = Prior()
        self.prior_candidates: list[dict] = []   # {answer, confidence, aspect} — tested during INIT
        self.directions: dict[str, Direction] = {}
        self.hypotheses: dict[str, Hypothesis] = {}
        self.evidence: dict[str, Evidence] = {}
        self.patterns: list[dict] = []     # cross-cutting abstractions
        self._dir_seq = 0
        self._hyp_seq = 0
        self._ev_seq = 0

    # ── id minting ──────────────────────────────────────────────────────────
    def _new_dir_id(self) -> str:
        self._dir_seq += 1
        return f"d{self._dir_seq}"

    def _new_hyp_id(self) -> str:
        self._hyp_seq += 1
        return f"h{self._hyp_seq}"

    def _new_ev_id(self) -> str:
        self._ev_seq += 1
        return f"e{self._ev_seq}"

    # ── seeding (INIT) ──────────────────────────────────────────────────────
    def seed(self, *, open_questions: list[str], prior_hypothesis: str,
             candidate_answers: list) -> list[Hypothesis]:
        """Seed the frontier from PRIOR and turn each parametric candidate answer into a
        Hypothesis. Those hypotheses are screened + deep-tested during INIT; whichever survive
        (and whichever are refuted interestingly) go on to seed research directions."""
        cands = list(candidate_answers or [])
        self.prior = Prior(text=prior_hypothesis, candidate_answers=[_ca_text(c) for c in cands])
        self.prior_candidates = [{"answer": _ca_text(c), "confidence": _ca_conf(c),
                                  "aspect": _ca_aspect(c)} for c in cands]
        for q in open_questions:
            self.add_direction(q, rationale="seed: open question from PRIOR", promise=0.6)
        out = []
        for c in cands:
            text = _ca_text(c)
            if not text:
                continue
            h = self.add_hypothesis(text, rationale="PRIOR: candidate answer from parametric knowledge",
                                    aspects=[_ca_aspect(c)] if _ca_aspect(c) else [],
                                    confidence=_ca_conf(c), origin="prior")
            out.append(h)
        return out

    def add_direction(self, question_text: str, *, parent_id: Optional[str] = None,
                      rationale: str = "", promise: float = 0.5, est_cost: float = 1.0,
                      tests_hypothesis_id: Optional[str] = None,
                      origin: str = "agent") -> Direction:
        did = self._new_dir_id()
        d = Direction(id=did, question_text=question_text, parent_id=parent_id,
                      rationale=rationale, promise=float(promise), est_cost=float(est_cost),
                      tests_hypothesis_id=tests_hypothesis_id, origin=origin)
        self.directions[did] = d
        return d

    def add_directions(self, new_dirs: list[dict], *, parent_id: Optional[str] = None,
                       priority_boost: float = 0.0) -> list[Direction]:
        out = []
        for nd in new_dirs or []:
            qt = (nd.get("question_text") or "").strip()
            if not qt:
                continue
            out.append(self.add_direction(
                qt, parent_id=parent_id, rationale=nd.get("rationale", ""),
                promise=min(1.0, float(nd.get("promise", 0.5)) + priority_boost),
                est_cost=float(nd.get("est_cost", 1.0))))
        return out

    # ── hypotheses ──────────────────────────────────────────────────────────
    def add_hypothesis(self, text: str, *, direction_id: Optional[str] = None,
                       rationale: str = "", aspects: Optional[list[str]] = None,
                       confidence: float = 0.5, origin: str = "agent",
                       parent_id: Optional[str] = None) -> Hypothesis:
        hid = self._new_hyp_id()
        h = Hypothesis(id=hid, text=text.strip(), direction_id=direction_id, rationale=rationale,
                       aspects=[a.strip() for a in (aspects or []) if a and a.strip()],
                       confidence=max(0.0, min(1.0, float(confidence))),
                       origin=origin, parent_id=parent_id)
        self.hypotheses[hid] = h
        if direction_id and direction_id in self.directions:
            self.directions[direction_id].produced_hypotheses.append(hid)
        return h

    def ingest_hypotheses(self, raw: list[dict], direction_id: Optional[str] = None) -> list[Hypothesis]:
        """Add the hypotheses an EXPLORE task proposed, with whatever evidence it already found.
        A hypothesis needs no evidence to be admitted — that is what testing is for."""
        added: list[Hypothesis] = []
        d = self.directions.get(direction_id) if direction_id else None
        for rh in raw or []:
            text = (rh.get("text") or "").strip()
            if not text:
                continue
            h = self.add_hypothesis(
                text, direction_id=direction_id, rationale=rh.get("rationale", ""),
                aspects=rh.get("aspects"), confidence=float(rh.get("confidence", 0.5)),
                parent_id=(d.tests_hypothesis_id if d is not None else None))
            if h.parent_id and h.parent_id in self.hypotheses:
                # inherit the re-test budget so the fix loop stays bounded across regenerated refinements
                h.test_attempts = self.hypotheses[h.parent_id].test_attempts
            self.attach_evidence(h, rh.get("evidence"), phase="explore")
            added.append(h)
        return added

    def attach_evidence(self, h: Hypothesis, raw: list[dict], phase: str = "deep") -> list[Evidence]:
        """Attach sourced evidence to a hypothesis. Items with no resolvable source are dropped —
        provenance is enforced here, not in a prompt."""
        out: list[Evidence] = []
        own = {self.evidence[e].source.key() for e in h.evidence_ids if e in self.evidence}
        for re_ in raw or []:
            src = SourceRef.from_json(re_.get("source"))
            if not src.resolvable():
                continue
            if src.key() in own:                     # same source twice on one hypothesis → keep the first
                continue
            eid = self._new_ev_id()
            ev = Evidence(id=eid, text=(re_.get("text") or "").strip(), source=src,
                          stance=_stance(re_.get("stance")), hypothesis_id=h.id,
                          numbers=_numbers_to_dict(re_.get("numbers")), phase=phase)
            self.evidence[eid] = ev
            h.evidence_ids.append(eid)
            own.add(src.key())
            out.append(ev)
        return out

    def evidence_for(self, h: Hypothesis) -> list[Evidence]:
        return [self.evidence[e] for e in h.evidence_ids if e in self.evidence]

    def support_balance(self, h: Hypothesis) -> tuple[int, int]:
        """(independent supporting sources, independent contradicting sources).

        Counts by ``independence_key`` — many queries over one dataset are one source, not many
        (DESIGN_data_plane.md §2.3)."""
        sup, con = set(), set()
        for ev in self.evidence_for(h):
            (sup if ev.stance == SUPPORTS else con if ev.stance == CONTRADICTS
             else set()).add(ev.source.independence_key())
        return len(sup), len(con)

    # ── the two-stage test ──────────────────────────────────────────────────
    def apply_screen(self, h: Hypothesis, r: dict) -> bool:
        """Stage 1. A cheap web search asking only: does this hold up well enough to be worth an
        in-depth test? Passing moves it to SCREENED; failing BINS it (retained, resurfacable)."""
        h.screen_note = (r.get("note") or "").strip()
        self.attach_evidence(h, r.get("evidence"), phase="screen")
        if r.get("confidence") is not None:
            h.confidence = max(0.0, min(1.0, float(r["confidence"])))
        if r.get("plausible"):
            h.status = SCREENED
            return True
        self.bin(h, reason=f"screen: {h.screen_note or 'no support found in a quick search'}")
        return False

    def accept_screened(self, hyps: list) -> int:
        """ABLATION (no-verifier): take what the cheap screen passed and pool it untested.

        The real pipeline only pools a hypothesis after STAGE 2 has hunted for counter-evidence and
        found none. With the verifier removed there is no such warrant, so these are marked
        UNTESTED rather than SUPPORTED — the report and the console then show honestly that nothing
        here was checked against contradicting evidence."""
        n = 0
        for h in hyps:
            if h.status != SCREENED:
                continue
            h.status = POOLED
            h.verdict = UNTESTED
            h.bin_reason = ""
            n += 1
        return n

    def apply_deep(self, h: Hypothesis, r: dict, max_attempts: int = 2) -> Optional[Direction]:
        """Stage 2. An extensive hunt for evidence AND counter-examples. Supported and
        uncontradicted → the POOL. Contested or refuted → the BIN, plus a re-investigation
        direction (bounded by max_attempts) so the loop can try to resolve it."""
        self.attach_evidence(h, r.get("evidence"), phase="deep")
        h.conflicts = [c for c in (r.get("conflicts") or []) if str(c).strip()]
        if r.get("confidence") is not None:
            h.confidence = max(0.0, min(1.0, float(r["confidence"])))
        verdict = _verdict(r)
        h.verdict = verdict
        sup, con = self.support_balance(h)

        if verdict == SUPPORTED and con == 0 and h.grounded():
            h.status = POOLED
            h.bin_reason = ""
            return None

        h.test_attempts += 1
        if verdict == SUPPORTED and not h.grounded():
            self.bin(h, reason="supported but no resolvable source was produced")
            return None
        if verdict == CONFLICTED or (verdict == SUPPORTED and con):
            h.verdict = CONFLICTED
            why = "; ".join(h.conflicts) or "contradicting evidence found"
            self.bin(h, reason=f"contested ({sup} for / {con} against): {why}")
            if h.test_attempts <= max_attempts:
                return self.add_direction(
                    f"Resolve the conflict over: {h.text}", parent_id=h.direction_id,
                    rationale=f"deep test attempt {h.test_attempts} left this contested: {why}",
                    promise=0.75, tests_hypothesis_id=h.id)
            return None
        why = (r.get("rationale") or "the literature gave no support").strip()
        self.bin(h, reason=f"refuted: {why}")
        if h.test_attempts <= max_attempts:
            return self.add_direction(
                f"Re-investigate (refuted): {h.text}", parent_id=h.direction_id,
                rationale=f"deep test refuted it: {why}", promise=0.65, tests_hypothesis_id=h.id)
        return None

    # ── the bin: deprioritised, never discarded ─────────────────────────────
    def bin(self, h: Hypothesis, reason: str) -> None:
        """Deprioritise a hypothesis. It stays in the ledger, renders in the report, and can be
        resurfaced by later corroborating evidence — nothing is ever dropped on the floor."""
        h.status = BINNED
        h.bin_reason = reason.strip()

    def unbin(self, h: Hypothesis, reason: str) -> None:
        """Bring a binned hypothesis back for another in-depth test — the resurfacing path."""
        h.status = SCREENED
        h.bin_reason = ""
        h.screen_note = f"resurfaced: {reason}".strip()

    # ── corroboration re-scoring (the resurfacing driver) ────────────────────
    def corroborate(self, h: Hypothesis, fresh: list[Evidence],
                    per_source: float = 0.04, cap: float = 0.95) -> float:
        """Raise a hypothesis's confidence when fresh evidence brings INDEPENDENT sources that
        support it. Only sources it doesn't already cite count; the bump has diminishing returns
        and never lowers confidence. Returns the delta applied.

        The corroborating evidence is COPIED onto the hypothesis — so it shows up in the report's
        citation list, and so the same source can never bump the same hypothesis twice (this runs
        every round over the whole bin).

        Independence is judged by ``independence_key``: a dataset the hypothesis already draws on
        cannot corroborate it again under a different query (DESIGN_data_plane.md §2.3)."""
        own = {e.source.independence_key() for e in self.evidence_for(h)}
        new = [e for e in fresh
               if e.stance == SUPPORTS and e.resolvable()
               and e.source.independence_key() not in own]
        if not new:
            return 0.0
        seen = set()
        for e in new:
            if e.source.independence_key() in seen:
                continue
            seen.add(e.source.independence_key())
            self.attach_evidence(h, [{"text": e.text, "stance": SUPPORTS,
                                      "source": asdict(e.source), "numbers": []}],
                                 phase="corroborate")
        before = float(h.confidence)
        h.confidence = max(before, min(cap, before + per_source * len(seen)))
        return h.confidence - before

    # ── human steering context (scope + assumptions) ─────────────────────────
    def add_constraints(self, items: list[str]) -> list[str]:
        """SCOPE filters ('only post-2020', 'clinical not preclinical'). Deduped, order-preserving."""
        added = []
        for s in items or []:
            s = (s or "").strip()
            if s and s not in self.constraints:
                self.constraints.append(s)
                added.append(s)
        return added

    def add_assumptions(self, items: list[str]) -> list[str]:
        """GIVENS the agent should treat as true without spending budget to test them. Deduped."""
        added = []
        for s in items or []:
            s = (s or "").strip()
            if s and s not in self.assumptions:
                self.assumptions.append(s)
                added.append(s)
        return added

    def guardrails_md(self) -> str:
        """Scope + assumptions rendered as a prompt guardrail block ('' if none). Injected into
        research/judge executor prompts so every model call honours the human's scope and premises."""
        out = []
        if self.constraints:
            out.append("SCOPE (hard filters — ignore anything outside these):")
            out += [f"  - {c}" for c in self.constraints]
        if self.assumptions:
            out.append("GIVEN ASSUMPTIONS (treat as TRUE; do NOT spend budget verifying them):")
            out += [f"  - {a}" for a in self.assumptions]
        return "\n".join(out)

    # ── abstract patterns (cross-cutting beliefs that also grow the frontier) ──
    def add_patterns(self, rows: list[dict]) -> list[dict]:
        """Store distilled cross-cutting patterns as a higher-level belief structure."""
        fresh = [r for r in (rows or []) if r.get("pattern")]
        self.patterns.extend(fresh)
        return fresh

    def spawn_from_patterns(self, rows: list[dict], promise: float = 0.75) -> list[Direction]:
        """Turn each pattern's `direction` into a new frontier Direction (the pattern's
        hypothesis becomes the rationale). This is how abstraction digs the loop DEEPER."""
        out = []
        for r in (rows or []):
            q = (r.get("direction") or "").strip()
            if not q:
                continue
            why = (r.get("hypothesis") or r.get("abstraction") or "").strip()
            out.append(self.add_direction(q, rationale=f"pattern: {why}", promise=promise))
        return out

    def patterns_md(self) -> str:
        if not self.patterns:
            return ""
        lines = ["## Cross-cutting patterns & hypotheses"]
        for p in self.patterns:
            lines.append(f"- **{p.get('pattern','')}** — {p.get('abstraction','')}")
            if p.get("hypothesis"):
                lines.append(f"  - hypothesis: {p['hypothesis']}")
            if p.get("direction"):
                lines.append(f"  - next: {p['direction']}")
        return "\n".join(lines) + "\n"

    # ── group-level belief scoring (direction → its hypotheses) ──────────────
    def direction_scores(self) -> dict:
        """Each direction scored by ITS hypotheses. strength = pooled/(pooled+binned); thin =
        explored but nothing pooled; contested = pooled≈binned. A thin/contested direction is one
        whose follow-ups the frontier should prioritise."""
        out: dict[str, dict] = {}
        for did, d in self.directions.items():
            hs = [self.hypotheses[h] for h in d.produced_hypotheses if h in self.hypotheses]
            pooled = sum(h.status == POOLED for h in hs)
            binned = sum(h.status == BINNED for h in hs)
            pending = len(hs) - pooled - binned
            checked = pooled + binned
            strength = pooled / checked if checked else 0.0
            out[did] = {"n": len(hs), "pooled": pooled, "binned": binned, "pending": pending,
                        "strength": strength, "thin": len(hs) > 0 and pooled == 0,
                        "contested": checked >= 2 and 0.34 <= strength <= 0.66}
        return out

    def niche_scores(self) -> dict:
        """Cross-cutting aspect view, used as a diversity tie-breaker when ordering the test queue."""
        agg: dict[str, dict] = {}
        for h in self.hypotheses.values():
            niche = h.aspects[0].strip().lower() if h.aspects else "(none)"
            a = agg.setdefault(niche, {"n": 0, "pooled": 0, "binned": 0, "pending": 0})
            a["n"] += 1
            a["pooled" if h.status == POOLED else "binned" if h.status == BINNED else "pending"] += 1
        for a in agg.values():
            checked = a["pooled"] + a["binned"]
            a["strength"] = a["pooled"] / checked if checked else 0.0
            a["thin"] = a["pooled"] == 0
            a["contested"] = checked >= 2 and 0.34 <= a["strength"] <= 0.66
        return agg

    # ── frontier + queue views ──────────────────────────────────────────────
    def open_directions(self) -> list[Direction]:
        return [d for d in self.directions.values() if d.status == OPEN]

    def is_data_claim(self, h: Hypothesis) -> bool:
        """A claim about the researcher's data rather than about the world. It is settled by
        reading the script that produced it, never by the literature — see pending_screen."""
        return h.origin == "data" or any(
            e.source.is_dataset() for e in self.evidence_for(h))

    def pending_screen(self) -> list[Hypothesis]:
        """The literature test queue. Data claims are EXCLUDED by construction: screening asks
        "does this have footing in the literature?", which no paper can answer about a private
        file, so a data claim sent here would fail for a reason unrelated to its truth and get
        binned as unsupported (DESIGN_data_plane.md §2.2)."""
        return [h for h in self.hypotheses.values()
                if h.status == PROPOSED and not h.pinned and not self.is_data_claim(h)]

    def pending_deep(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values()
                if h.status == SCREENED and not h.pinned and not self.is_data_claim(h)]

    def pool(self) -> list[Hypothesis]:
        """The hypothesis pool — supported, sourced, uncontradicted. The answer material."""
        return [h for h in self.hypotheses.values() if h.status == POOLED]

    def binned(self) -> list[Hypothesis]:
        """Deprioritised hypotheses. Retained in full and rendered in the report."""
        return [h for h in self.hypotheses.values() if h.status == BINNED]

    def all_hypotheses(self) -> list[Hypothesis]:
        return list(self.hypotheses.values())

    def grounded_hypotheses(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.grounded()]

    def aspects(self) -> set[str]:
        out: set[str] = set()
        for h in self.hypotheses.values():
            out |= {a.lower() for a in h.aspects}
        return out

    def aspect_texts(self) -> set[str]:
        out: set[str] = set()
        for h in self.hypotheses.values():
            out |= set(h.aspects)
        return out

    # ── rendering ───────────────────────────────────────────────────────────
    def note_source(self, src) -> None:
        """Record a citation that has no hypothesis behind it.

        The search-baseline ablations produce prose and sources but no beliefs, so nothing attaches
        them to the ledger. Keeping them here lets reference_objs — and therefore clibib enrichment,
        dedup and references_md — work unchanged for those arms."""
        if not hasattr(self, "loose_sources"):
            self.loose_sources = []
        s = src if isinstance(src, SourceRef) else SourceRef.from_json(src or {})
        if s.resolvable() and not s.is_dataset():
            self.loose_sources.append(s)

    def reference_objs(self, only_pooled: bool = False) -> list:
        """The deduped bibliography as SourceRef objects. Dedup by normalised TITLE (folds the same
        paper's multiple locators into one entry); when a title recurs keep the richest citation
        (verified > has-DOI > has-any-locator). Mutating these objects (e.g. enrich via clibib) flows
        straight into references_md, which reuses this."""
        pool = self.pool() if only_pooled else self.grounded_hypotheses()

        def _rank(s) -> int:
            return (4 if s.verified else 0) + (2 if s.doi else 0) + (1 if s.resolvable() else 0)

        def _keys(s) -> list:
            ks = []
            tk = s.title_key()
            if tk:
                ks.append("t:" + tk)
            if s.doi:
                ks.append("d:" + str(s.doi).strip().lower())   # canonical DOI (clibib fills these in)
            return ks
        # Merge by shared TITLE *or* DOI: the same paper under different locators OR under slightly
        # different titles collapses to one entry. keymap points every key at a group id.
        keymap: dict = {}
        groups: dict = {}
        gid = 0
        srcs = [ev.source for h in pool for ev in self.evidence_for(h)
                if ev.resolvable() and not ev.source.is_dataset()]
        srcs += list(getattr(self, "loose_sources", []))     # ablation baselines: sources, no beliefs
        for s in srcs:
            ks = _keys(s)
            if not ks:
                continue
            g = next((keymap[k] for k in ks if k in keymap), None)
            if g is None:
                g, gid = gid, gid + 1
                groups[g] = s
            elif _rank(s) > _rank(groups[g]):
                groups[g] = s
            for k in ks:
                keymap[k] = g
        return list(groups.values())

    def data_sources_md(self, only_pooled: bool = False) -> str:
        """The DATA counterpart to the bibliography (DESIGN_data_plane.md §6). A data claim's
        provenance is the operation that produced it, so this lists — per dataset — every query
        run, the script that ran it, and the assumptions it declared. Doubles as the run's
        reproducibility record: it is what someone would read to check the numbers."""
        pool = self.pool() if only_pooled else self.grounded_hypotheses()
        by_ds: dict[str, list] = {}
        for h in pool:
            for ev in self.evidence_for(h):
                if ev.source.is_dataset():
                    by_ds.setdefault(ev.source.dataset_id, []).append(ev.source)
        if not by_ds:
            return ""
        lines = ["## Data sources", "",
                 "_Data findings are not citations: their provenance is the operation that produced "
                 "them. Each is listed with the script that computed it and the interpretive "
                 "choices that script made._", ""]
        for ds, srcs in sorted(by_ds.items()):
            lines.append(f"**`{ds}`**")
            seen: set[str] = set()
            for s in srcs:
                if s.key() in seen:
                    continue
                seen.add(s.key())
                rows = f" → {s.rows} rows" if s.rows is not None else ""
                lines.append(f"- {s.query or '(operation not described)'}{rows}"
                             + (f"  — `{s.script}`" if s.script else ""))
                for a in s.assumptions:
                    lines.append(f"    - assumed: {a}")
            lines.append("")
        return "\n".join(lines) + "\n"

    def references_md(self, only_pooled: bool = False) -> str:
        """A complete, deduped source bibliography — appended to the LLM finalize report so the
        reference list is guaranteed accurate."""
        refs = self.reference_objs(only_pooled=only_pooled)
        if not refs:
            return ""
        lines = ["## Sources"]
        for i, s in enumerate(sorted(refs, key=lambda s: (_real_authors(s) or [""])[0]), 1):
            loc = s.doi or (f"PMID:{s.pmid}" if s.pmid else None) or s.pmc or s.url or ""
            vmark = " ✓" if s.verified else ""
            auth = _real_authors(s)
            if auth:
                head = f"{auth[0] + ' et al.'} ({s.year or 'n.d.'})."
            else:
                # Database records and web resources (ClinVar, registries, docs) genuinely have no
                # author — naming the publisher is honest, where "Unknown (n.d.)" reads like a
                # citation we failed to resolve.
                pub = _publisher_of(s)
                year = f" ({s.year})" if s.year else ""
                head = f"{pub}{year}." if pub else (f"({s.year})." if s.year else "")
            lines.append(f"{i}. {head} {s.title}. {s.journal or ''} {loc}{vmark}".replace("  ", " ").strip())
        return "\n".join(lines) + "\n"

    def draft(self) -> str:
        """A lightweight rendering used only for in-loop EVALUATE (not the final answer)."""
        return self.synthesize(heading="DRAFT (in-progress)", include_binned=False)

    def synthesize(self, *, heading: str = "", include_binned: bool = True) -> str:
        """Deterministic fallback report: the pool clustered by aspect with numbered refs, then the
        bin — every deprioritised hypothesis with the reason it was set aside. Nothing is hidden."""
        refs: dict[str, int] = {}
        ref_objs: list[SourceRef] = []

        def cite(h: Hypothesis) -> str:
            ids = []
            for ev in self.evidence_for(h):
                k = ev.source.key()
                if k not in refs:
                    ref_objs.append(ev.source)
                    refs[k] = len(ref_objs)
                ids.append(str(refs[k]))
            return ("[" + ", ".join(sorted(set(ids), key=int)) + "]") if ids else ""

        def numbers_of(h: Hypothesis) -> str:
            nums: dict[str, object] = {}
            for ev in self.evidence_for(h):
                nums.update(ev.numbers)
            return "  ".join(f"{k}={v}" for k, v in nums.items())

        def render_clusters(hs: list[Hypothesis], out: list[str]) -> None:
            # Cluster by aspect, but render each hypothesis ONCE (under its largest cluster) so
            # multi-aspect hypotheses aren't repeated. Secondary aspects show as inline tags.
            clusters: dict[str, list[Hypothesis]] = {}
            for h in hs:
                for a in (h.aspects or ["(general)"]):
                    clusters.setdefault(a, []).append(h)
            order = sorted(clusters, key=lambda a: -len(clusters[a]))
            primary: dict[str, str] = {}
            for a in order:
                for h in clusters[a]:
                    primary.setdefault(h.id, a)
            for aspect in order:
                members = [h for h in clusters[aspect] if primary.get(h.id) == aspect]
                if not members:
                    continue
                out.append(f"## {aspect}")
                for h in sorted(members, key=lambda h: -h.confidence):
                    nums = numbers_of(h)
                    sup, con = self.support_balance(h)
                    tag = "" if h.status == POOLED else f" _({h.verdict})_"
                    others = [a for a in h.aspects if a != aspect]
                    also = f"  _(also: {', '.join(others)})_" if others else ""
                    out.append(f"- {h.text} {cite(h)}{(' — ' + nums) if nums else ''}"
                               f"  _({sup} for / {con} against)_{tag}{also}")
                out.append("")

        lines: list[str] = [f"# {heading or self.question}", ""]
        if self.assumptions:
            lines += ["## Given assumptions",
                      "_Human-supplied premises taken as true (not independently tested):_"]
            lines += [f"- {a}" for a in self.assumptions] + [""]
        if self.constraints:
            lines += ["## Scope", *[f"- {c}" for c in self.constraints], ""]
        if self.prior.text:
            lines += ["## Prior hypothesis", self.prior.text, ""]
        pool = self.pool()
        if pool:
            render_clusters(pool, lines)
        else:
            lines += ["_No hypothesis reached the pool within budget._", ""]

        if include_binned:
            binned = self.binned()
            if binned:
                lines += ["---", "", "## Deprioritised hypotheses",
                          "_Set aside, not discarded — each with the reason and its evidence "
                          "balance. Later evidence can resurface any of these._", ""]
                for h in sorted(binned, key=lambda h: -h.confidence):
                    sup, con = self.support_balance(h)
                    lines.append(f"- {h.text} {cite(h)}  _({sup} for / {con} against)_ "
                                 f"— **{h.bin_reason or h.verdict}**")
                lines.append("")
            pending = self.pending_screen() + self.pending_deep()
            if pending:
                lines += ["## Untested hypotheses",
                          "_Generated but not tested before the budget ran out._", ""]
                lines += [f"- {h.text}" for h in pending] + [""]

        if ref_objs:
            lines.append("## References")
            for i, s in enumerate(ref_objs, 1):
                loc = s.doi or (f"PMID:{s.pmid}" if s.pmid else None) or s.pmc or s.url or ""
                auth = (s.authors[0] + " et al." if s.authors else "Unknown")
                vmark = " ✓" if s.verified else ""
                lines.append(f"{i}. {auth} ({s.year or 'n.d.'}). {s.title}. {s.journal or ''} {loc}{vmark}".rstrip())
        return "\n".join(lines).strip() + "\n"

    # ── persistence ─────────────────────────────────────────────────────────
    def to_json(self) -> dict:
        return {
            "question": self.question,
            "required_fields": self.required_fields,
            "glossary": self.glossary,
            "sources": self.sources,
            "datasets": self.datasets,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "prior": asdict(self.prior),
            "prior_candidates": self.prior_candidates,
            "directions": {k: asdict(v) for k, v in self.directions.items()},
            "hypotheses": {k: asdict(v) for k, v in self.hypotheses.items()},
            "evidence": {k: _evidence_json(v) for k, v in self.evidence.items()},
            "patterns": self.patterns,
        }

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_json(), indent=2), encoding="utf-8")

    @classmethod
    def from_json(cls, d: dict) -> "Ledger":
        """Rehydrate a ledger from to_json() output (for finalize/inspection/resume)."""
        L = cls(d.get("question", ""))
        L.required_fields = list(d.get("required_fields") or [])
        L.sources = list(d.get("sources") or [])
        L.datasets = list(d.get("datasets") or [])
        L.glossary = dict(d.get("glossary") or {})
        L.constraints = list(d.get("constraints") or [])
        L.assumptions = list(d.get("assumptions") or [])
        L.patterns = list(d.get("patterns") or [])
        pr = d.get("prior") or {}
        L.prior = Prior(text=pr.get("text", ""), candidate_answers=list(pr.get("candidate_answers") or []))
        L.prior_candidates = list(d.get("prior_candidates") or [])
        for did, dd in (d.get("directions") or {}).items():
            L.directions[did] = Direction(
                id=dd.get("id", did), question_text=dd.get("question_text", ""),
                parent_id=dd.get("parent_id"), rationale=dd.get("rationale", ""),
                status=dd.get("status", OPEN), promise=dd.get("promise", 0.0),
                est_cost=dd.get("est_cost", 0.0),
                allocated_usd=float(dd.get("allocated_usd", 0.0) or 0.0),
                spent_usd=float(dd.get("spent_usd", 0.0) or 0.0),
                alloc_rationale=dd.get("alloc_rationale", ""),
                produced_hypotheses=list(dd.get("produced_hypotheses") or []),
                tests_hypothesis_id=dd.get("tests_hypothesis_id"),
                origin=dd.get("origin", "agent"))
        for eid, ed in (d.get("evidence") or {}).items():
            src = SourceRef.from_json(ed.get("source"))
            src.verified = bool((ed.get("source") or {}).get("verified", False))
            L.evidence[eid] = Evidence(
                id=eid, text=ed.get("text", ""), source=src,
                stance=_stance(ed.get("stance")), hypothesis_id=ed.get("hypothesis_id"),
                numbers=dict(ed.get("numbers") or {}), phase=ed.get("phase", "explore"),
                origin=ed.get("origin", "agent"))
        for hid, hd in (d.get("hypotheses") or {}).items():
            L.hypotheses[hid] = Hypothesis(
                id=hid, text=hd.get("text", ""), direction_id=hd.get("direction_id"),
                rationale=hd.get("rationale", ""), aspects=list(hd.get("aspects") or []),
                status=hd.get("status", PROPOSED), verdict=hd.get("verdict", UNTESTED),
                confidence=float(hd.get("confidence", 0.5) or 0.0),
                evidence_ids=[e for e in (hd.get("evidence_ids") or []) if e in L.evidence],
                conflicts=list(hd.get("conflicts") or []),
                screen_note=hd.get("screen_note", ""), bin_reason=hd.get("bin_reason", ""),
                test_attempts=int(hd.get("test_attempts", 0) or 0),
                parent_id=hd.get("parent_id"), origin=hd.get("origin", "agent"),
                pinned=bool(hd.get("pinned", False)))
        L._dir_seq = max([0] + [int(k[1:]) for k in L.directions if k[1:].isdigit()])
        L._hyp_seq = max([0] + [int(k[1:]) for k in L.hypotheses if k[1:].isdigit()])
        L._ev_seq = max([0] + [int(k[1:]) for k in L.evidence if k[1:].isdigit()])
        return L


def _stance(raw) -> str:
    s = str(raw or "").strip().lower()
    return s if s in (SUPPORTS, CONTRADICTS, NEUTRAL) else SUPPORTS


def _verdict(r: dict) -> str:
    raw = str(r.get("verdict") or "").strip().lower()
    return raw if raw in (SUPPORTED, CONFLICTED, REFUTED) else REFUTED


def _evidence_json(e: Evidence) -> dict:
    d = asdict(e)
    d["source"] = asdict(e.source)
    return d
