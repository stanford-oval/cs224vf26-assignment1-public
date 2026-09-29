"""One-call operations, so the assignment is about judgement, not plumbing.

Everything a student needs to *do* in this notebook is here as a function that
takes settings and returns a result you can read. Nobody is asked to reimplement
a matcher or hand-roll a SQL query — the interesting decisions are which
settings to use, what to tell the agent, and what the numbers mean.

The three verbs:

``steer``      tell the agent what to look for, in words
``configure``  describe the columns you want extracted, in words
``evaluate``   run a comparison and read the table

Each returns a plain object you can print. None of them hides a number: if a
setting changes an outcome, the change is in the table.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from .cohort import Cohort, Patient
from .hpo import DiseaseProfile, HpoBundle, TermMatcher
from .scoring import (Match, evaluate_ranking, likelihood_score, rank_cohort,
                      resnik_score)


# ==========================================================================
# STEER — telling the research agent what to look for
# ==========================================================================


@dataclass
class Steer:
    """Natural-language guidance for GRILL, in the shapes it accepts.

    GRILL takes human input through a typed steering channel rather than by
    editing the prompt: *directions* are questions to investigate, *constraints*
    bound what counts as in scope, and *assumptions* are interpretive choices
    you are making explicit. All three are threaded into the research prompts as
    guardrails and are **context, not claims** -- they never pass the provenance
    gate and can never become evidence.

    That distinction is the point. You can tell the agent what to look for
    without telling it what it will find.
    """

    directions: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def as_events(self) -> list[dict]:
        """The JSON GRILL's steer inbox expects."""
        out: list[dict] = []
        if self.directions:
            out.append({"directions_add": [{"question_text": d, "promise": 0.8}
                                           for d in self.directions]})
        if self.constraints:
            out.append({"constraints": list(self.constraints)})
        if self.assumptions:
            out.append({"assumptions": list(self.assumptions)})
        return out

    def write(self, path: str | Path) -> Path:
        """Write a steer inbox GRILL will drain at the next round boundary."""
        import json  # noqa: PLC0415

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_events(), indent=2) + "\n")
        return path

    def as_prompt_block(self) -> str:
        """The same guidance as text, for reading or for a one-shot run."""
        parts = []
        if self.directions:
            parts.append("INVESTIGATE:\n" + "\n".join(f"  - {d}" for d in self.directions))
        if self.constraints:
            parts.append("SCOPE:\n" + "\n".join(f"  - {c}" for c in self.constraints))
        if self.assumptions:
            parts.append("ASSUME:\n" + "\n".join(f"  - {a}" for a in self.assumptions))
        return "\n\n".join(parts)

    def critique(self) -> list[str]:
        """Cheap checks on steering text, before you spend anything on it.

        Not a grader. These catch the three ways steering usually goes wrong:
        asking for something you already believe, asking something unanswerable
        from any literature, and asking so broadly that any paper matches.
        """
        notes: list[str] = []
        leading = ("confirm", "prove", "show that", "verify that", "demonstrate that")
        for d in self.directions:
            low = d.lower()
            if any(low.startswith(w) or f" {w} " in low for w in leading):
                notes.append(f"leading: {d[:60]!r} asks the agent to confirm, "
                             "not to find out")
            if len(d.split()) < 5:
                notes.append(f"vague: {d[:60]!r} is too short to constrain a search")
            if "?" not in d and not low.startswith(("what", "which", "how", "why",
                                                    "identify", "determine", "compare")):
                notes.append(f"not a question: {d[:60]!r}")
        if not self.directions:
            notes.append("no directions: the agent will only follow its own priors")
        return notes


# ==========================================================================
# CONFIGURE — describing the table you want extracted
# ==========================================================================

#: The columns the diagnosis needs, and why each is worded the way it is.
DEFAULT_FIELD_NOTES: dict[str, str] = {
    "disease_or_gene": (
        "The disease name or causative gene these patients have, exactly as "
        "the paper names it. Read it from the row or column header that names "
        "the gene or disorder, not from what the page is mostly about."
    ),
    "phenotype": (
        "The clinical finding, as a short noun phrase in the paper's own words "
        "(e.g. 'microcephaly', 'absent speech'). Not a whole sentence."
    ),
    "n_affected": "How many assessed individuals showed it. Null if not stated.",
    "n_assessed": (
        "How many individuals were assessed for it -- the denominator. "
        "Null if not stated."
    ),
    "percent": (
        "The percentage, 0-100, only where the paper states one. "
        "Do not compute it from the counts."
    ),
    "cohort_label": (
        "Which cohort or subgroup the counts describe, if the paper "
        "distinguishes several."
    ),
}

DEFAULT_EXCLUDES: list[str] = [
    "phenotypes attributed to a different disease being compared",
    "phenotypes mentioned only as absent in the whole cohort",
    "findings quoted from another paper rather than observed here",
]


def configure_extraction(field_notes: Mapping[str, str] | None = None,
                         excludes: Sequence[str] | None = None,
                         drop_fields: Sequence[str] = ()):
    """Build the extraction schema from descriptions, not from code.

    A field's *description* is the only thing that tells the model what to put
    in it, so rewriting one is the main lever you have over extraction quality.
    Pass only the fields you want to change; the rest keep their defaults.

        configure_extraction(field_notes={
            "phenotype": "A short clinical finding, lower case, singular."
        })
    """
    from .extract import add_sliders_to_path  # noqa: PLC0415

    add_sliders_to_path()
    from sliders.models import Field, Schema, TableSpec, TableScope  # noqa: PLC0415

    notes = dict(DEFAULT_FIELD_NOTES)
    notes.update(field_notes or {})
    types = {"n_affected": "int", "n_assessed": "int", "percent": "float"}
    canon = {"disease_or_gene", "phenotype"}
    required = {"disease_or_gene", "phenotype"}

    fields = [
        Field(name=name, data_type=types.get(name, "str"), description=desc,
              required=name in required, canonicalize=name in canon)
        for name, desc in notes.items() if name not in drop_fields
    ]
    return Schema(
        reasoning=("Diagnosis needs P(phenotype | disease). The literature "
                   "states that as counts over an assessed subgroup."),
        tables=[TableSpec(
            name="PhenotypeFrequency",
            description=("One row per clinical phenotype reported for a "
                         "specific disease or gene in this paper's cohort."),
            primary_key=[f for f in ("disease_or_gene", "phenotype")
                         if f not in drop_fields],
            scope=TableScope(
                definition=("Findings observed in the patients this paper "
                            "reports. Count a phenotype once per disease "
                            "per paper."),
                excludes=list(DEFAULT_EXCLUDES if excludes is None else excludes),
            ),
            fields=fields,
        )],
    )


# ==========================================================================
# EVALUATE — running a comparison and reading the table
# ==========================================================================


@dataclass
class Setting:
    """One labelled configuration to compare against others."""

    label: str
    profile: DiseaseProfile
    scorer: Callable = likelihood_score
    kwargs: dict = field(default_factory=dict)


def evaluate_settings(settings: Sequence[Setting], cohorts: Sequence[Cohort],
                      hpo: HpoBundle, reference: DiseaseProfile | None = None,
                      show: bool = True) -> list[dict]:
    """Score several configurations over the same cohorts, and tabulate.

    This is the workhorse for every ablation in the assignment. One row per
    setting, one column per metric, so a claim that a setting helps is a row
    you can point at.

    ``top-1`` is how often the right patient ranked first. ``MRR`` is the mean
    of 1/rank, which still moves when the answer goes from fourth to second.
    ``margin`` is the mean gap to the runner-up: positive means a comfortable
    win, and it is the metric that notices a result getting *safer* rather than
    merely staying correct.
    """
    from .scoring import compare_profiles  # noqa: PLC0415

    rows = []
    for s in settings:
        reports = [evaluate_ranking(
            rank_cohort(c, s.profile, hpo, scorer=s.scorer, **s.kwargs),
            c.key.target_patient_id) for c in cohorts]
        row = {
            "setting": s.label,
            "terms": len(s.profile),
            "top-1": sum(r.top1_correct for r in reports) / len(reports),
            "MRR": sum(r.reciprocal_rank for r in reports) / len(reports),
            "margin": sum(r.margin for r in reports) / len(reports),
            "median rank": sorted(r.target_rank for r in reports)[len(reports) // 2],
        }
        if reference is not None:
            pr = compare_profiles(s.profile, reference, hpo)
            row["exact F1"] = pr.exact_f1
            row["lenient F1"] = pr.lenient_f1
        rows.append(row)

    if show:
        cols = list(rows[0])
        cells = [{c: _fmt(c, r[c]) for c in cols} for r in rows]
        widths = {c: max(len(c), *(len(x[c]) for x in cells)) for c in cols}
        print("  ".join(c.ljust(widths[c]) for c in cols))
        for x in cells:
            print("  ".join(x[c].ljust(widths[c]) for c in cols))
    return rows


#: Columns that are rates, and should print as percentages. Everything else
#: keeps its units -- a margin of 0.59 is not "59%", and printing it that way
#: is exactly the kind of quiet unit error this assignment is about.
_RATE_COLUMNS = {"top-1", "MRR", "exact F1", "lenient F1", "quality"}

#: Only a margin is signed. A signed rate reads as a change rather than a level.
_SIGNED_COLUMNS = {"margin"}


def _fmt(col: str, v: Any) -> str:
    if isinstance(v, float):
        if col in _RATE_COLUMNS:
            return f"{v:.0%}"
        return f"{v:+.2f}" if col in _SIGNED_COLUMNS else f"{v:.2f}"
    return str(v)


def explain_ranking(cohort: Cohort, profile: DiseaseProfile, hpo: HpoBundle,
                    top_k: int = 3, evidence_k: int = 6, **kwargs) -> list[Match]:
    """Rank the cohort and show *why*, itemised.

    A rank with no itemised reason is a number, not a diagnosis. This prints
    what drove each of the leading candidates and what argued against them.
    """
    matches = rank_cohort(cohort, profile, hpo, **kwargs)
    for i, m in enumerate(matches[:top_k], 1):
        print(f"{i}. {m.patient_id}   score {m.score:.2f}")
        for c in m.top_evidence(evidence_k):
            if c.contribution > 0:
                print(f"     {c.contribution:+6.2f}  {c.patient_label[:34]:<36} "
                      f"<- {c.matched_label}")
        against = [c for c in m.top_against(3) if c.contribution < 0]
        for c in against:
            print(f"     {c.contribution:+6.2f}  {c.patient_label[:34]:<36} {c.kind}")
        print()
    return matches


def grounding_report(rows: Sequence[Any], matcher: TermMatcher, hpo: HpoBundle,
                     show: int = 12) -> dict:
    """How many extracted phrases became HPO terms, and which did not.

    Grounding is the step between "the paper said this" and "the profile knows
    this", and it is where reconstructions quietly lose their best evidence.
    """
    grounded, failed = [], []
    for r in rows:
        cell = r.cells.get("phenotype")
        phrase = str(cell.value_raw) if cell and cell.value_raw else ""
        if not phrase:
            continue
        m = matcher.match(phrase)
        (grounded if m.hpo_id else failed).append((phrase, m))

    print(f"{len(grounded)} of {len(grounded)+len(failed)} phrases grounded "
          f"({len(grounded)/max(len(grounded)+len(failed),1):.0%})")
    if failed:
        print("\nphrases that reached no HPO term:")
        for phrase, m in failed[:show]:
            print(f"  {phrase[:46]:<48} best score {m.score:.2f}")
    return {"n_grounded": len(grounded), "n_failed": len(failed),
            "failed": [p for p, _ in failed]}


def recall_breakdown(profile: DiseaseProfile, reference: DiseaseProfile,
                     hpo: HpoBundle, rows: Sequence[Any], corpus_dir: str | Path,
                     ungrounded: Sequence[str] = (), top: int = 10) -> dict:
    """Why each high-frequency finding is missing, sorted into four causes.

    The four have different fixes, and only one of them means the literature
    cannot answer the question:

      (a) absent from the corpus      -- fetch different papers
      (b) in the corpus, not extracted -- improve the reader
      (c) extracted, grounding failed  -- improve the matcher
      (d) extracted, wrong disease     -- improve the scope rules
    """
    from .scoring import compare_profiles  # noqa: PLC0415

    report = compare_profiles(profile, reference, hpo)
    text = "\n".join(p.read_text() for p in Path(corpus_dir).glob("*.md")).lower()
    extracted = {str(r.cells["phenotype"].value_raw).lower()
                 for r in rows if r.cells.get("phenotype")}
    ung = {u.lower() for u in ungrounded}

    causes: Counter[str] = Counter()
    detail = []
    for term, label, freq in report.missed_high_frequency[:top]:
        head = label.lower().split()[-1]
        if any(head in u or u in label.lower() for u in ung):
            cause = "(c) grounding failed"
        elif any(head in e for e in extracted):
            cause = "(d) extracted, wrong disease"
        elif head in text:
            cause = "(b) in corpus, not extracted"
        else:
            cause = "(a) absent from corpus"
        causes[cause] += 1
        detail.append((cause, freq, label))

    print(f"{'cause':<30} {'freq':>5}  finding")
    for cause, freq, label in detail:
        print(f"{cause:<30} {freq:5.0%}  {label[:44]}")
    print("\n", dict(causes))
    return {"causes": dict(causes), "detail": detail, "report": report}


# ==========================================================================
# READING A GRILL RUN — tables, not code
# ==========================================================================


def frontier_table(run, show: bool = True) -> list[dict]:
    """Directions grouped by where they came from, with what each bought.

    Four origins. *seed* directions come from the PRIOR executor before any
    searching; *agent* ones are spawned by EXPLORE as it reads; *corrective*
    ones exist to resolve a claim that failed its deep test; *human* ones came
    through the steering channel.

    The column to read is pooled-per-dollar. Direction *count* measures what
    was produced, not what was investigated, and the two differ by an order of
    magnitude in a typical run.
    """
    raw = run.ledger_json or {}
    D = run.directions_table()
    pooled_by_dir = Counter(h["direction"] for h in run.hypotheses_table()
                            if h["status"] == "pooled")

    def origin_of(d):
        if d["tests"]:
            return "corrective"
        if d["origin"] == "human":
            return "human"
        rationale = (raw.get("directions", {}).get(d["id"], {}) or {}).get("rationale") or ""
        return "seed" if (d["parent"] is None and "seed" in rationale) else "agent"

    agg: dict[str, dict] = defaultdict(
        lambda: {"n": 0, "spent": 0.0, "hypotheses": 0, "pooled": 0})
    for d in D:
        a = agg[origin_of(d)]
        a["n"] += 1
        a["spent"] += d["spent"]
        a["hypotheses"] += d["n_hypotheses"]
        a["pooled"] += pooled_by_dir.get(d["id"], 0)

    rows = []
    for origin, a in sorted(agg.items(), key=lambda kv: -kv[1]["spent"]):
        rows.append({"origin": origin, "directions": a["n"],
                     "spent": a["spent"], "hypotheses": a["hypotheses"],
                     "pooled": a["pooled"],
                     "pooled/$": (a["pooled"] / a["spent"]) if a["spent"] else float("inf")})
    if show:
        print(f"{'origin':<12} {'dirs':>5} {'spent':>8} {'hyps':>6} "
              f"{'pooled':>7} {'pooled/$':>10}")
        for r in rows:
            print(f"{r['origin']:<12} {r['directions']:5d} {r['spent']:8.2f} "
                  f"{r['hypotheses']:6d} {r['pooled']:7d} {r['pooled/$']:10.1f}")
        empty = [d for d in D if d["spent"] > 0 and d["n_hypotheses"] == 0]
        print(f"\n{len(empty)} directions were funded and produced nothing")
        for d in empty[:3]:
            print(f"  {d['id']}  ${d['spent']:.2f}  {d['question'][:74]}")
    return rows


def claims_table(run, hpo: HpoBundle, show: bool = True) -> list[dict]:
    """Every pooled claim, with how many *independent* sources back it.

    Evidence count and independent-source count differ, and the gap matters:
    a claim with five evidence items may rest on one paper.
    """
    ledger = run.ledger()
    rows = []
    for h in ledger.pool():
        ev = ledger.evidence_for(h)
        keys = {e.source.independence_key() for e in ev
                if e.stance == "supports" and e.source.resolvable()}
        rows.append({"id": h.id, "verdict": h.verdict, "confidence": h.confidence,
                     "evidence": len(ev), "independent": len(keys), "text": h.text})
    if show:
        print(f"{'id':>4} {'verdict':<11} {'conf':>5} {'ev':>4} {'indep':>6}  claim")
        for r in rows:
            print(f"{r['id']:>4} {r['verdict']:<11} {r['confidence']:5.2f} "
                  f"{r['evidence']:4d} {r['independent']:6d}  {r['text'][:54]}")
        lone = sum(1 for r in rows if r["independent"] <= 1)
        print(f"\n{lone} of {len(rows)} pooled claims rest on one independent "
              f"source or none")

        gaps = sorted(((abs(h.confidence - (1.0 if h.verdict == "supported" else 0.0)), h)
                       for h in ledger.all_hypotheses() if h.verdict != "untested"),
                      key=lambda r: -r[0])
        print("\nwhere confidence and verdict disagree most:")
        for g, h in gaps[:3]:
            print(f"  gap={g:.2f}  {h.id}  verdict={h.verdict:<11} "
                  f"conf={h.confidence:.2f}")
            print(f"     {h.text[:88]}")
    return rows


def budget_table(run, show: bool = True) -> dict:
    """Where the money went, and what the planner intended to spend.

    Two things to notice. The split between finding claims (EXPLORE) and
    checking them (SCREEN + DEEP) is a design choice you can argue about. And
    `allocated` versus `spent` tells you whether the planner could predict its
    own costs.
    """
    phases = run.cost_by_phase()
    total = sum(phases.values()) or 1.0
    meta = run.run_json or {}
    allocs = meta.get("allocations") or []
    if show:
        print("spend by phase")
        for phase, usd in sorted(phases.items(), key=lambda kv: -kv[1]):
            if usd:
                print(f"  {phase:<10} ${usd:6.2f}  {usd/total:5.1%}  "
                      f"{'#' * int(usd * 6)}")
        find = phases.get("explore", 0.0)
        check = phases.get("screen", 0.0) + phases.get("deep", 0.0)
        print(f"\n  finding  ${find:.2f}   checking  ${check:.2f}"
              f"   ratio 1:{check/max(find, 0.01):.0f}")
        if allocs:
            print("\nplanner calibration")
            for a in allocs:
                used = a["spent"] / a["allocated"] if a["allocated"] else 0
                print(f"  {a['direction']:>4}  allocated ${a['allocated']:.2f}  "
                      f"spent ${a['spent']:.2f}  ({used:.0%} of intent)")
    return {"phases": phases, "allocations": allocs,
            "budget": (meta.get("budget") or {})}


def capture_table(schema, rows, show: bool = True) -> list[dict]:
    """Per-field capture and parse rates for an extraction schema.

    `capture_rate` is what fraction of rows got a value at all; `parse_rate` is
    what fraction of those values match the declared type; `distinct_ratio` is
    how unique the values are. Each catches a different defect, and none
    catches all of them -- a field can capture 100% and hold the wrong thing.
    """
    from .extract import add_sliders_to_path  # noqa: PLC0415

    add_sliders_to_path()
    from sliders.stages.schema import probe_fields  # noqa: PLC0415

    probes = probe_fields(schema, list(rows))
    out = [{"field": p.field, "capture": p.capture_rate, "parse": p.parse_rate,
            "distinct_ratio": p.distinct_ratio} for p in probes]
    if show:
        print(f"{'field':<18} {'capture':>8} {'parse':>7} {'distinct':>9}")
        for r in out:
            print(f"{r['field']:<18} {r['capture']:8.0%} {r['parse']:7.0%} "
                  f"{r['distinct_ratio']:9.2f}")
    return out


def table_summary(built, show: bool = True) -> dict:
    """The build report: what the extraction actually did, before its answer."""
    rep = built.report
    stats = built.stats
    info = {
        "rows": sum(len(t.rows) for t in built.tables),
        "documents": stats.n_docs,
        "chunks": stats.n_chunks,
        "gated_out": stats.n_chunks_gated_out,
        "zero_row_documents": len(rep.docs_with_zero_rows) if rep else None,
        "quote_verification": stats.quote_verification_rate,
        "rows_before_dedup": stats.n_rows_extracted,
        "rows_after_dedup": stats.n_rows_after_dedup,
    }
    if show:
        for k, v in info.items():
            shown = f"{v:.1%}" if isinstance(v, float) else v
            print(f"  {k:<22} {shown}")
        if rep and rep.canon:
            print("\n  canonicalization, column by column")
            for c in rep.canon:
                print(f"    {c.field:<18} kind={c.kind:<9} method={c.method:<14} "
                      f"{c.distinct_raw:>4} -> {c.distinct_key:<4} "
                      f"guards={c.guards_fired}")
    return info


# ==========================================================================
# VERIFICATION — what an adversarial test buys
# ==========================================================================


def verifier_diagnostics(runs: Mapping[str, Any], claims: Sequence[tuple],
                         show: bool = True) -> list[dict]:
    """Compare verifier variants on metrics that do and do not catch a bad one.

    ``quality`` is ``pooled / (pooled + binned)``. A verifier that never bins
    scores 1.00 while pooling false claims, so it reads *better* when broken.

    Two metrics that do catch it, and neither needs to know which claims are
    true: the **contradiction rate** (contradicting evidence per tested
    hypothesis) and the **corrective direction count**, since only refutation
    spawns those.
    """
    from src import metrics as _m  # noqa: PLC0415

    truth_map = dict(claims)
    rows = []
    for label, run in runs.items():
        ledger = run.ledger()
        pool = ledger.pool()
        tested = [h for h in ledger.all_hypotheses() if h.verdict != "untested"]
        against = sum(1 for h in ledger.all_hypotheses()
                      for e in ledger.evidence_for(h) if e.stance == "contradicts")
        rows.append({
            "run": label,
            "pooled": len(pool),
            "FALSE pooled": sum(1 for h in pool if not truth_map.get(h.text, True)),
            "quality": _m.quality(ledger),
            "contradiction rate": against / max(len(tested), 1),
            "corrective dirs": sum(1 for d in ledger.directions.values()
                                   if d.tests_hypothesis_id),
        })
    if show:
        cols = list(rows[0])
        cells = [{c: _fmt(c, r[c]) for c in cols} for r in rows]
        widths = {c: max(len(c), *(len(x[c]) for x in cells)) for c in cols}
        print("  ".join(c.ljust(widths[c]) for c in cols))
        for x in cells:
            print("  ".join(x[c].ljust(widths[c]) for c in cols))
    return rows


def verifier_price(run, runs: Mapping[str, Any], claims: Sequence[tuple],
                   show: bool = True) -> dict:
    """What the deep test cost, and what it caught, in the same table."""
    phases = run.cost_by_phase()
    H = run.hypotheses_table()
    binned = [h for h in H if h["status"] == "binned"]
    deep = phases.get("deep", 0.0)
    info = {
        "deep_usd": deep,
        "share_of_run": deep / max(sum(phases.values()), 1e-9),
        "tested": sum(1 for h in H if h["verdict"] != "untested"),
        "overturned": len(binned),
        "usd_per_catch": deep / max(len(binned), 1),
    }
    if show:
        print(f"DEEP cost             ${info['deep_usd']:.2f}  "
              f"({info['share_of_run']:.0%} of the run)")
        print(f"claims tested         {info['tested']}")
        print(f"claims overturned     {info['overturned']}  "
              f"{dict(Counter(h['verdict'] for h in binned))}")
        print(f"cost per claim caught ${info['usd_per_catch']:.2f}\n")
        verifier_diagnostics(runs, claims)
    return info


def budget_floor(config, show: bool = True) -> dict:
    """The smallest budget that lets INIT finish, derived from the knobs.

    INIT grounds every key term **in parallel** before any budget check, then
    probes each prior candidate. The cap is therefore soft: a run can bill more
    than its budget by roughly the width of one parallel batch.
    """
    ground = config.ground_task_usd * config.ground_terms
    probe = config.screen_task_usd + config.deep_task_usd
    info = {"ground_parallel": ground, "probe_per_candidate": probe,
            "floor": ground + probe}
    if show:
        print("the knobs")
        for k in ("ground_task_usd", "ground_terms", "screen_task_usd",
                  "deep_task_usd", "explore_round_frac", "alloc_ceiling_frac",
                  "explore_min_usd"):
            print(f"  {k:<22} {getattr(config, k)}")
        print(f"\nGROUND, launched in parallel  {config.ground_terms} x "
              f"${config.ground_task_usd:.2f} = ${ground:.2f}")
        print(f"probe, per prior candidate    ${probe:.2f}")
        print(f"-> floor before any research  ~${info['floor']:.2f}")
        cap = config.explore_round_frac * config.alloc_ceiling_frac
        print(f"\none direction can never get more than {cap:.0%} of what remains")
    return info


# ==========================================================================
# EXTRACTION — provenance, dedup, and auditing the table
# ==========================================================================


def provenance_demo(doc, chunk, rows, hpo: HpoBundle, show: bool = True) -> dict:
    """Show what `quote_verified` does and does not certify, on real lines."""
    from .extract import add_sliders_to_path, verification_rate  # noqa: PLC0415

    add_sliders_to_path()
    from sliders.chunking import line_index  # noqa: PLC0415
    from sliders.stages.extraction import (number_lines, resolve_lines,  # noqa: PLC0415
                                           value_supported)

    idx = line_index(doc.text)
    numbered = number_lines(chunk).split("\n")
    target = next((l for l in numbered if "%" in l and "(" in l), numbered[0])
    n = int(target.split("→")[0]) if "→" in target else 1
    span, cited = resolve_lines(n, n, chunk, idx)

    print("the cited line:\n ", cited.strip()[:100], "\n")
    pcts = [w for w in cited.replace("(", " ").replace(")", " ").split()
            if w.endswith("%")]
    if pcts:
        print(f"  '{pcts[0]}' supported by those lines? "
              f"{value_supported(pcts[0], cited)}")
        if len(pcts) > 1:
            print(f"  '{pcts[1]}' supported too? {value_supported(pcts[1], cited)}"
                  "   <- a different cohort's number, on the same line")
        raw = pcts[0].rstrip("%")
        try:
            print(f"  '{float(raw)/100}' supported? "
                  f"{value_supported(str(float(raw)/100), cited)}"
                  f"   <- but {pcts[0]} IS that value, normalised")
        except ValueError:
            pass
    bad, _ = resolve_lines(10_000, 10_001, chunk, idx)
    print(f"\n  an out-of-range citation resolves to {bad}  (rejected, not clamped)")

    print("\nresolving three locators by hand:")
    for r in list(rows)[:3]:
        c = r.cells.get("phenotype")
        if c and c.span:
            src = Path("data/corpus") / r.doc_name
            if src.exists():
                line = src.read_text().splitlines()[c.span.start_line - 1]
                print(f"  {r.doc_name}:{c.span.start_line}  {line.strip()[:72]}")

    from sliders.models import Table  # noqa: PLC0415
    spec = None
    for r in rows:
        spec = None
        break
    print("\nverification rate per field:")
    per = defaultdict(list)
    for r in rows:
        for name, cell in r.cells.items():
            if cell.value_raw is not None:
                per[name].append(bool(cell.quote_verified))
    for name, vals in sorted(per.items()):
        rate = sum(vals) / len(vals)
        flag = "   <- inferred, not read" if rate == 0 else ""
        print(f"  {name:<18} {rate:5.0%}{flag}")
    return {"verification": {k: sum(v) / len(v) for k, v in per.items()}}


def dedup_demo(rows, spec, hpo: HpoBundle, show: bool = True) -> dict:
    """Two papers disagreeing, the three dedup modes, and what really pools."""
    from .extract import add_sliders_to_path  # noqa: PLC0415

    add_sliders_to_path()
    from sliders.models import Cell, Row  # noqa: PLC0415
    from sliders.stages.dedup import dedup_rows, needs_reconciliation  # noqa: PLC0415
    from sliders.models import Table  # noqa: PLC0415

    def mk(rid, phen, n, d, verified, quote):
        return Row(row_id=rid, table="PhenotypeFrequency", doc_id="x",
                   doc_name=f"{rid}.md", chunk_id="c",
                   cells={"disease_or_gene": Cell(value_raw="GENE",
                                                  canonical_key="gene"),
                          "phenotype": Cell(value_raw=phen, canonical_key=phen,
                                            quote=quote, quote_verified=verified),
                          "n_affected": Cell(value_raw=n),
                          "n_assessed": Cell(value_raw=d),
                          "percent": Cell(value_raw=round(100 * n / d, 1)),
                          "cohort_label": Cell(value_raw=None)})

    pair = [mk("paperA", "microcephaly", 20, 39, True, "20/39"),
            mk("paperB", "microcephaly", 9, 9, False, "all nine")]
    dd = dedup_rows(pair, spec, mode="key")
    print(f"(a) two papers, same finding, different counts -> "
          f"{len(dd.rows)} row(s) survive")
    for r in dd.rows:
        print(f"    kept {r.row_id}: {r.cells['n_affected'].value_raw}/"
              f"{r.cells['n_assessed'].value_raw}  "
              f"verified={r.cells['phenotype'].quote_verified}")
    print("    the survivor is chosen by (cells filled, quotes verified) -- "
          "not by cohort size")

    print("\n(b) the three modes on your real rows")
    for mode in ("off", "exact", "key"):
        print(f"    {mode:<6} {len(rows)} -> "
              f"{len(dedup_rows(list(rows), spec, mode=mode).rows)} rows")
    v = needs_reconciliation(Table(spec=spec,
                                   rows=dedup_rows(list(rows), spec, mode="key").rows))
    print(f"    reconciliation needed: {v.needed}  ({v.reason[:60]})")

    print("\n(c) what actually pools into one HPO term")
    m = TermMatcher(hpo.ontology)
    groups = defaultdict(list)
    for r in rows:
        cell = r.cells.get("phenotype")
        if not cell or not cell.value_raw:
            continue
        hit = m.match(str(cell.value_raw))
        if hit.hpo_id:
            groups[hit.hpo_id].append((str(cell.value_raw), r.doc_name,
                                       r.cells["n_affected"].value_raw,
                                       r.cells["n_assessed"].value_raw))
    shown = 0
    for hid, members in groups.items():
        if len(members) > 1:
            print(f"    {hid} {hpo.label(hid)}")
            for phrase, doc, a, b in members:
                print(f"      {phrase[:28]:<30} {a}/{b}   {doc}")
            shown += 1
            if shown >= 3:
                break
    if not shown:
        print("    no term received more than one row")
    return {"groups": {k: v for k, v in groups.items() if len(v) > 1}}


def audit_table(built, table, conn, tname, table_mod, corpus_dir: str | Path,
                reference_rows: Sequence[Any] = ()) -> dict:
    """Separate irrelevant documents from missed ones, then hunt for bad rows."""
    import re as _re  # noqa: PLC0415

    gene_like = _re.compile(r"[A-Z][A-Z0-9-]{2,}")
    freq = _re.compile(r"\d{1,3}(?:\.\d)?%|\b\d{1,3}/\d{1,3}\b")
    phen = _re.compile(r"hypotonia|microcephaly|seizure|speech|developmental delay|"
                       r"feeding|stature|dysmorph|intellectual", _re.I)
    subject = Counter(str(r.cells["disease_or_gene"].value_raw)
                      for r in table.rows if r.cells.get("disease_or_gene"))
    key = subject.most_common(1)[0][0] if subject else ""

    with_rows = {r.doc_name for r in table.rows}
    missed, irrelevant = [], 0
    for path in sorted(Path(corpus_dir).glob("*.md")):
        text = path.read_text()
        if key and key.lower() not in text.lower():
            irrelevant += 1
            continue
        lines = [l for l in text.splitlines() if freq.search(l) and phen.search(l)]
        if lines and path.name not in with_rows:
            missed.append((path.name, len(lines)))
    print(f"(a) {irrelevant} documents never mention {key!r} -> correctly empty")
    print(f"    {len(missed)} DO carry phenotype frequencies that were not extracted")
    for name, n in missed[:5]:
        print(f"      {name}  ({n} such lines)")

    out, _ = table_mod.run_sql(conn, f"""SELECT phenotype,
             COUNT(DISTINCT disease_or_gene) AS n_diseases, COUNT(*) AS n_rows
      FROM {tname} GROUP BY phenotype
      HAVING COUNT(DISTINCT disease_or_gene) > 1
      ORDER BY n_diseases DESC LIMIT 8""")
    print("\n(b) phenotypes attributed to more than one disorder:")
    print(out if out.strip() else
          "    none -- this extractor gives every row the page's dominant "
          "subject, so it cannot produce this inconsistency")

    if reference_rows:
        print("\n(c) stand-in vs model-backed extraction")
        print(f"    rows        {len(table.rows):4d}  vs  {len(reference_rows):4d}")
        print(f"    documents   {len(with_rows):4d}  vs  "
              f"{len({r.doc_name for r in reference_rows}):4d}")
        print(f"    disorders   {len(subject):4d}  vs  "
              f"{len(Counter(str(r.cells['disease_or_gene'].value_raw) for r in reference_rows)):4d}")
    return {"irrelevant": irrelevant, "missed": missed}


# ==========================================================================
# GROUNDING AND SCORING — settings, not reimplementation
# ==========================================================================


def matcher_settings(hpo: HpoBundle, *, related_synonyms: bool = False,
                     strip_qualifiers: bool = False, min_score: float = 0.5,
                     idf_weighted: bool = True) -> TermMatcher:
    """A term matcher you configure rather than rewrite.

    Three settings, each fixing a different observed failure:

    ``related_synonyms``  HPO records "Epilepsy" as a *related* synonym of
        Seizure, and the default loader keeps only exact and narrow ones -- so
        `epilepsy` matches nothing at all. Turning this on trades precision for
        recall, deliberately.
    ``strip_qualifiers``  removes severity and course words ("severe",
        "neonatal") before matching, so a qualified phrase reaches its head
        concept.
    ``min_score``         the acceptance floor. Lower admits more matches,
        right and wrong.
    """
    import math as _math  # noqa: PLC0415
    import re as _re  # noqa: PLC0415

    from .hpo import TermMatch, _norm_phrase, _STOP  # noqa: PLC0415

    QUALIFIER = _re.compile(
        r"\b(severe|mild|moderate|profound|global|primary|secondary|progressive|"
        r"neonatal|congenital|estimated|level|of|suspected|possible|borderline)\b")

    class Configured(TermMatcher):
        def __init__(self, ontology):
            super().__init__(ontology)
            n = len(self.term_tokens) or 1
            df = Counter(t for toks in self.term_tokens.values() for t in toks)
            self.idf = {t: _math.log(n / (1 + c)) for t, c in df.items()}
            if related_synonyms:
                for hid, syns in ontology.related_synonyms.items():
                    for syn in syns:
                        self.exact.setdefault(_norm_phrase(syn), hid)

        def _weight(self, toks):
            if not idf_weighted:
                return float(len(toks)) or 1e-9
            return sum(self.idf.get(t, 1.0) for t in toks) or 1e-9

        def _variants(self, text):
            base = _norm_phrase(text)
            yield base
            if strip_qualifiers:
                stripped = _re.sub(r"\s+", " ", QUALIFIER.sub(" ", base)).strip()
                if stripped and stripped != base:
                    yield stripped

        def match(self, text, min_score=min_score):
            seen = set()
            for v in self._variants(text):
                if v and v not in seen:
                    seen.add(v)
                    if v in self.exact:
                        hid = self.exact[v]
                        return TermMatch(text, hid, self.ontology.label(hid),
                                         1.0, "exact")
            best_id, best = None, 0.0
            for v in seen:
                q = frozenset(v.split()) - _STOP
                if not q:
                    continue
                cands: set[str] = set()
                for tok in q:
                    cands |= self.token_index.get(tok, set())
                for hid in cands:
                    tt = self.term_tokens[hid]
                    if tt:
                        sc = self._weight(q & tt) / self._weight(q | tt)
                        if sc > best:
                            best_id, best = hid, sc
            if best_id is None or best < min_score:
                return TermMatch(text, None, None, best, "none")
            return TermMatch(text, best_id, self.ontology.label(best_id),
                             best, "weighted")

    return Configured(hpo.ontology)


def precision_blindspot(cohort: Cohort, profile: DiseaseProfile, hpo: HpoBundle,
                        target_patient: str, show: bool = True) -> dict:
    """Prove the scorer ignores profile precision, then show what still hurts.

    Two demonstrations. First: add findings the target *provably lacks* and the
    score does not move by a single float, because ``likelihood_score`` only
    ever iterates over the patient's own terms.

    Second: add *random* spurious terms and the ranking degrades anyway. The
    target's score cannot fall, so the damage runs entirely through the
    competitors -- a spurious term that matches another patient's findings
    hands them free evidence. Blind through the channel you expect, sensitive
    through one you do not.
    """
    import random as _random  # noqa: PLC0415

    target = cohort.get(target_patient)
    have: set[str] = set()
    for t in target.terms:
        have |= hpo.ontology.ancestors(t) | hpo.ontology.descendants(t)
    absent = [t for t in hpo.ontology.name
              if hpo.ontology.is_phenotype(t) and t not in have][:200]

    base = likelihood_score(target, profile, hpo)
    junk = DiseaseProfile("x", "x", {**profile.frequencies,
                                     **{t: 0.95 for t in absent}})
    after = likelihood_score(target, junk, hpo)

    pool = [t for t in hpo.ontology.name
            if hpo.ontology.is_phenotype(t) and hpo.ic.ic(t) > 1.5]

    def pollute(n, seed=0):
        r = _random.Random(seed)
        d = dict(profile.frequencies)
        d.update({r.choice(pool): 0.7 for _ in range(n)})
        return DiseaseProfile("X", "polluted", d, excluded=set())

    def capped(patient, prof, hpo_, *, weight=1.0, cap=2.0, **kw):
        m = likelihood_score(patient, prof, hpo_, **kw)
        h: set[str] = set()
        for t in patient.terms:
            h |= hpo_.ontology.ancestors(t) | hpo_.ontology.descendants(t)
        pen = sum(min(-math.log(max(1 - p, 1e-3)), cap)
                  for term, p in prof.frequencies.items() if term not in h)
        m.score -= weight * pen
        return m

    rows = []
    for n in (0, 10, 30, 80):
        pp = pollute(n)
        a = evaluate_ranking(rank_cohort(cohort, pp, hpo), target_patient)
        b = evaluate_ranking(rank_cohort(cohort, pp, hpo, scorer=capped),
                             target_patient)
        rows.append({"spurious": n, "plain rank": a.target_rank,
                     "plain margin": a.margin, "fixed rank": b.target_rank,
                     "fixed margin": b.margin})

    if show:
        print(f"profile {len(profile)} -> {len(junk)} terms "
              f"(+{len(junk)-len(profile)} the patient provably lacks)")
        print(f"{target_patient} score {base.score:.4f} -> {after.score:.4f}   "
              f"delta {after.score - base.score:+.4f}")
        print("The scorer never looked at them.\n")
        print(f"{'spurious':>9} {'plain rank':>11} {'plain margin':>13} "
              f"{'fixed rank':>11} {'fixed margin':>13}")
        for r in rows:
            print(f"{r['spurious']:9d} {r['plain rank']:11d} "
                  f"{r['plain margin']:13.2f} {r['fixed rank']:11d} "
                  f"{r['fixed margin']:13.2f}")
    return {"delta": after.score - base.score, "sweep": rows}


def negatives_analysis(cohorts: Sequence[Cohort], hpo: HpoBundle, target: str,
                       smoothings: Sequence[float] = (0.0, 1.0),
                       show: bool = True) -> dict:
    """Why real recorded negatives make the diagnosis worse, and how to fix it.

    Two effects, and they need separating. **Overconfident frequencies**: HPO
    curates some findings as ``2/2``, which read literally are certainties, so
    a patient lacking one is billed ``log(1 - 0.999)``. Laplace smoothing fixes
    that. **Ascertainment bias**: the penalty is a *sum* over recorded
    negatives, so it tracks how thoroughly a patient was examined -- and the
    published cases of a newly described disease are examined most thoroughly
    of all. Smoothing does not touch that; normalising by depth does.
    """
    def sweep(profile, **kw):
        rs = [evaluate_ranking(rank_cohort(c, profile, hpo, **kw),
                               c.key.target_patient_id) for c in cohorts]
        return (sum(r.top1_correct for r in rs) / len(rs),
                sum(r.reciprocal_rank for r in rs) / len(rs),
                sum(r.margin for r in rs) / len(rs))

    if show:
        print(f"{'smoothing':>10} {'negatives':>10} {'top-1':>7} {'MRR':>6} "
              f"{'margin':>9}")
    grid = []
    for s in smoothings:
        prof = hpo.store.profile(target, smoothing=s)
        for aw in (0.0, 1.0):
            a, m, g = sweep(prof, absent_weight=aw)
            grid.append({"smoothing": s, "negatives": bool(aw),
                         "top-1": a, "MRR": m, "margin": g})
            if show:
                print(f"{s:10.1f} {'on' if aw else 'off':>10} {a:7.0%} "
                      f"{m:6.3f} {g:9.2f}")

    prof = hpo.store.profile(target, smoothing=1.0)
    xs, ys, tgt_n, oth_n = [], [], [], []
    for c in list(cohorts)[:6]:
        for p in c.patients:
            m = likelihood_score(p, prof, hpo, absent_weight=1.0)
            pen = sum(x.contribution for x in m.contributions if x.kind == "absent")
            xs.append(len(p.excluded)); ys.append(pen)
            (tgt_n if p.patient_id == c.key.target_patient_id else oth_n).append(
                len(p.excluded))
    corr = 0.0
    if len(xs) > 2:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
        corr = cov / den if den else 0.0

    def depth_normalised(patient, profile, hpo_, *, weight=3.0, **kw):
        m = likelihood_score(patient, profile, hpo_, absent_weight=1.0, **kw)
        absent = [c for c in m.contributions if c.kind == "absent"]
        if absent:
            tot = sum(c.contribution for c in absent)
            m.score += -tot + weight * (tot / len(absent))
        return m

    comparison = []
    for label, kw in (("negatives off (default)", {"absent_weight": 0.0}),
                      ("negatives on, summed", {"absent_weight": 1.0})):
        a, m, g = sweep(prof, **kw)
        comparison.append({"scorer": label, "top-1": a, "MRR": m, "margin": g})
    a, m, g = sweep(prof, scorer=depth_normalised)
    comparison.append({"scorer": "negatives on, depth-normalised",
                       "top-1": a, "MRR": m, "margin": g})

    if show:
        print(f"\ncorrelation(n_excluded, absent-penalty) = {corr:+.3f}")
        if tgt_n and oth_n:
            print(f"mean recorded negatives -- targets "
                  f"{sum(tgt_n)/len(tgt_n):.0f}, others {sum(oth_n)/len(oth_n):.0f}")
        print(f"\n{'scorer':<34} {'top-1':>7} {'MRR':>6} {'margin':>9}")
        for r in comparison:
            print(f"{r['scorer']:<34} {r['top-1']:7.0%} {r['MRR']:6.3f} "
                  f"{r['margin']:9.2f}")
    return {"grid": grid, "correlation": corr, "comparison": comparison}


# ==========================================================================
# REPLAY — what a weaker verifier would have done with the same evidence
# ==========================================================================
#
# A finished run records, for every hypothesis, every evidence item the deep
# test found and which way it points. That is enough to re-decide each
# hypothesis under a different policy without spending anything:
#
#   actual              GRILL's rule: supported, zero contradicting, one
#                       resolvable source
#   confirmation_only   the deep test may only return support, so every
#                       contradicting item vanishes and anything with one
#                       supporting item pools
#   screen_only         GRILL's --ablate no-verifier: pool whatever passed
#                       the cheap screen, untested
#
# The replay is exact for the pooling decision and honest about what it
# cannot know: a confirmation-only verifier would also have *searched*
# differently, so its real behaviour is at least this permissive.


def replay_verifier(run) -> "pd.DataFrame":
    """One row per hypothesis: its fate under each of the three policies."""
    import collections  # noqa: PLC0415

    import pandas as pd  # noqa: PLC0415

    H = run.hypotheses_table()
    E = run.evidence_table()
    L = run.ledger_json or {}
    by_h: dict[str, list] = collections.defaultdict(list)
    for e in E:
        by_h[e["hypothesis"]].append(e)
    rows = []
    for h in H:
        ev = by_h[h["id"]]
        sup = [e for e in ev if e["stance"] == "supports"]
        con = [e for e in ev if e["stance"] == "contradicts"]
        raw = (L.get("hypotheses") or {}).get(h["id"], {})
        screened = bool(raw.get("screen_note")) or any(e["phase"] == "screen" for e in ev)
        rows.append({
            "id": h["id"],
            "claim": h["text"],
            "confidence": h["confidence"],
            "supports": len(sup),
            "contradicts": len(con),
            "actual": h["status"],
            "actual_verdict": h["verdict"],
            "confirmation_only": "pooled" if sup else "binned",
            "screen_only": "pooled (untested)" if screened else "binned",
            "what_the_deep_test_found_against": " | ".join(
                e["text"] for e in con if e["phase"] == "deep"),
        })
    return pd.DataFrame(rows).set_index("id")


def verifier_policies(run) -> "pd.DataFrame":
    """Pooled, binned and the quality metric under each policy, for one run."""
    import pandas as pd  # noqa: PLC0415

    t = replay_verifier(run)
    out = []
    for col, label in (("actual", "GRILL: adversarial deep test"),
                       ("confirmation_only", "deep test may only confirm"),
                       ("screen_only", "no deep test (--ablate no-verifier)")):
        pooled = int(t[col].str.startswith("pooled").sum())
        out.append({"policy": label, "pooled": pooled, "binned": len(t) - pooled,
                    "quality = pooled/(pooled+binned)": round(pooled / max(len(t), 1), 2),
                    "pooled claims carrying contradicting evidence":
                        int((t[col].str.startswith("pooled") & (t.contradicts > 0)).sum())})
    return pd.DataFrame(out).set_index("policy")


def verifier_replay_all(root="runs/reference") -> "pd.DataFrame":
    """The same three policies for every reference run, one row per directory."""
    import glob  # noqa: PLC0415
    import os  # noqa: PLC0415

    import pandas as pd  # noqa: PLC0415

    from . import grill as G  # noqa: PLC0415

    rows = []
    for path in sorted(glob.glob(os.path.join(str(root), "OMIM_*"))):
        t = replay_verifier(G.GrillRun(path))
        n = len(t)
        rows.append({
            "directory": os.path.basename(path), "hypotheses": n,
            "pooled_actual": int((t.actual == "pooled").sum()),
            "pooled_confirmation_only": int((t.confirmation_only == "pooled").sum()),
            "pooled_screen_only": int(t.screen_only.str.startswith("pooled").sum()),
            "contradicting_items_ignored": int(t.loc[t.actual == "binned", "contradicts"].sum()),
        })
    df = pd.DataFrame(rows).set_index("directory")
    df["quality_actual"] = (df.pooled_actual / df.hypotheses).round(2)
    df["quality_confirmation_only"] = (df.pooled_confirmation_only / df.hypotheses).round(2)
    return df
