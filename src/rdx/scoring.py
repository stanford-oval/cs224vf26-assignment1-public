"""Scoring a patient against a disease profile, and evaluating a ranking.

Two scorers, deliberately different in what they need:

``resnik_score``      ontology-only. Needs a *set* of disease terms. This is the
                      classic Phenomizer-style symmetric Resnik similarity.
``likelihood_score``  needs term *frequencies*, and pays attention to findings
                      the disease excludes. Strictly more informative -- and
                      strictly harder to get from the literature, which is the
                      point of the SLIDERS half of the assignment.

Both return a ``Match`` carrying per-term contributions, because a ranking
without an itemised reason is not evidence, and the assignment grades the
evidence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping, Sequence

from .cohort import Cohort, Patient
from .hpo import DiseaseProfile, HpoBundle, InformationContent, Ontology


# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------


@dataclass
class TermContribution:
    patient_term: str
    patient_label: str
    matched_term: str | None
    matched_label: str | None
    contribution: float
    kind: str = "support"  # support | penalty | unmatched

    def as_row(self) -> dict:
        return {
            "patient_term": self.patient_term,
            "patient_label": self.patient_label,
            "matched_term": self.matched_term,
            "matched_label": self.matched_label,
            "contribution": round(self.contribution, 3),
            "kind": self.kind,
        }


@dataclass
class Match:
    patient_id: str
    score: float
    contributions: list[TermContribution] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    def top_evidence(self, k: int = 5) -> list[TermContribution]:
        return sorted(self.contributions, key=lambda c: -c.contribution)[:k]

    def top_against(self, k: int = 5) -> list[TermContribution]:
        return sorted(self.contributions, key=lambda c: c.contribution)[:k]


# --------------------------------------------------------------------------
# Scorers
# --------------------------------------------------------------------------


def _best_match(
    term: str,
    against: Iterable[str],
    ontology: Ontology,
    ic: InformationContent,
) -> tuple[str | None, float]:
    """The disease term most informatively sharing an ancestor with ``term``."""
    best_t, best_v = None, 0.0
    for other in against:
        _, v = ic.mica(term, other)
        if v > best_v:
            best_t, best_v = other, v
    return best_t, best_v


def resnik_score(
    patient: Patient,
    profile: DiseaseProfile,
    hpo: HpoBundle,
    *,
    symmetric: bool = True,
) -> Match:
    """Symmetric best-match average Resnik similarity.

    Forward direction asks "is every finding this patient has explained by the
    disease?"; the reverse asks "does this patient show what the disease is
    known for?". Forward alone rewards a disease annotated to half the
    ontology, so the symmetric average is the default.
    """
    ontology, ic = hpo.ontology, hpo.ic
    disease_terms = list(profile.frequencies)
    if not disease_terms or not patient.terms:
        return Match(patient.patient_id, 0.0)

    contribs: list[TermContribution] = []
    forward_total = 0.0
    for t in patient.terms:
        m, v = _best_match(t, disease_terms, ontology, ic)
        forward_total += v
        contribs.append(
            TermContribution(
                patient_term=t,
                patient_label=ontology.label(t),
                matched_term=m,
                matched_label=ontology.label(m) if m else None,
                contribution=v,
                kind="support" if v > 0 else "unmatched",
            )
        )
    forward = forward_total / len(patient.terms)

    if not symmetric:
        return Match(patient.patient_id, forward, contribs, {"forward": forward})

    reverse_total = sum(
        _best_match(t, patient.terms, ontology, ic)[1] for t in disease_terms
    )
    reverse = reverse_total / len(disease_terms)
    score = 0.5 * (forward + reverse)
    return Match(
        patient.patient_id,
        score,
        contribs,
        {"forward": forward, "reverse": reverse},
    )


def likelihood_score(
    patient: Patient,
    profile: DiseaseProfile,
    hpo: HpoBundle,
    *,
    background: Mapping[str, float] | None = None,
    exclusion_penalty: float = 2.5,
    unmatched_penalty: float = 0.25,
    imprecision_discount: float = 0.6,
    absent_weight: float = 0.0,
) -> Match:
    """A log-likelihood-ratio score: log P(term | disease) / P(term | cohort).

    The comparison is against a background rate, so a finding that half of all
    rare diseases share contributes almost nothing while a rare, specific one
    dominates -- the behaviour you want from a diagnostic score and the
    behaviour plain overlap counting does not have.

    Three details that matter and that students are asked to ablate:

    * A patient term recorded *less* specifically than the disease term still
      counts, discounted -- ancestors are weaker evidence, not absent evidence.
    * A finding the disease explicitly excludes is scored negative.
    * Findings the disease never mentions cost a small constant, so a patient
      with a long list of unexplained problems does not outrank a clean fit.
    * A finding the *patient* was tested for and does not have is scored
      against the disease, in proportion to how often the disease causes it:
      ``log(1 - P(term | disease))``. Absence of a finding the disease shows in
      95% of cases is strong evidence; absence of one it shows in 5% is almost
      none. Real records carry these negatives and sampled ones do not, so this
      channel is dead weight on a synthetic cohort and, on a real one, it is
      **off by default because switching it on makes the diagnosis worse.**

      That is not a bug in the idea; explicit negatives really are evidence.
      It is a confound. A patient's penalty grows with how many findings a
      clinician bothered to record as absent, and the most thoroughly
      phenotyped patient is not usually the right one. On 20 phenopacket
      cohorts, turning it on drops top-1 accuracy from 75% to 30%. Normalising
      the penalty by phenotyping depth is left as an exercise.
    """
    ontology, ic = hpo.ontology, hpo.ic
    if background is None:
        background = {}

    def bg(term: str) -> float:
        if term in background:
            return max(background[term], 1e-4)
        # Fall back to the annotation-derived prevalence of the term.
        c = ic.counts.get(ontology.normalize(term), 1)
        return max(c / ic.n_diseases, 1e-4)

    contribs: list[TermContribution] = []
    total = 0.0

    disease_terms = profile.frequencies
    excluded_closure: set[str] = set()
    for e in profile.excluded:
        excluded_closure |= ontology.descendants(e)

    for t in patient.terms:
        t_norm = ontology.normalize(t)

        if t_norm in excluded_closure:
            v = -exclusion_penalty
            total += v
            contribs.append(
                TermContribution(t, ontology.label(t), None, None, v, "penalty")
            )
            continue

        # Exact, or the patient term is an ancestor/descendant of a disease term.
        best_term, best_p, discount = None, 0.0, 1.0
        if t_norm in disease_terms:
            best_term, best_p, discount = t_norm, disease_terms[t_norm], 1.0
        else:
            t_desc = ontology.descendants(t_norm)
            t_anc = ontology.ancestors(t_norm)
            for d_term, p in disease_terms.items():
                if d_term in t_desc:  # patient recorded a vaguer parent
                    d_ = imprecision_discount
                elif d_term in t_anc:  # patient recorded something more specific
                    d_ = imprecision_discount
                else:
                    continue
                if p * d_ > best_p * discount:
                    best_term, best_p, discount = d_term, p, d_

        if best_term is None:
            v = -unmatched_penalty
            total += v
            contribs.append(
                TermContribution(t, ontology.label(t), None, None, v, "unmatched")
            )
            continue

        p_given_disease = max(min(best_p * discount, 0.999), 1e-3)
        v = math.log(p_given_disease / bg(best_term))
        total += v
        contribs.append(
            TermContribution(
                t,
                ontology.label(t),
                best_term,
                ontology.label(best_term),
                v,
                "support" if v > 0 else "penalty",
            )
        )

    # Explicit negatives: the patient was examined and the finding was absent.
    n_absent = 0
    for t in getattr(patient, "excluded", []) or []:
        t_norm = ontology.normalize(t)
        p = disease_terms.get(t_norm)
        if p is None:
            # A more specific exclusion still rules out the general finding.
            for d_term, dp in disease_terms.items():
                if d_term in ontology.ancestors(t_norm):
                    p = max(p or 0.0, dp * imprecision_discount)
        if not p:
            continue
        v = absent_weight * math.log(max(1.0 - min(p, 0.999), 1e-3))
        total += v
        n_absent += 1
        contribs.append(
            TermContribution(t, f"{ontology.label(t)} (absent)", t_norm,
                             ontology.label(t_norm), v, "absent")
        )

    return Match(
        patient.patient_id,
        total,
        contribs,
        {
            "n_terms": len(patient.terms),
            "n_excluded": len(getattr(patient, "excluded", []) or []),
            "n_absent_scored": n_absent,
            "n_excluded_hits": sum(1 for c in contribs if c.kind == "penalty"),
            "profile_size": len(disease_terms),
        },
    )


Scorer = Callable[[Patient, DiseaseProfile, HpoBundle], Match]


def rank_cohort(
    cohort: Cohort,
    profile: DiseaseProfile,
    hpo: HpoBundle,
    scorer: Scorer = likelihood_score,
    **scorer_kwargs,
) -> list[Match]:
    """Score every patient against one disease profile, best first."""
    matches = [scorer(p, profile, hpo, **scorer_kwargs) for p in cohort.patients]
    return sorted(matches, key=lambda m: -m.score)


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------


@dataclass
class RankingReport:
    top1_correct: bool
    target_rank: int
    n_patients: int
    reciprocal_rank: float
    margin: float
    target_score: float
    runner_up_id: str
    ranking: list[tuple[str, float]]

    def as_dict(self) -> dict:
        return {
            "top1_correct": self.top1_correct,
            "target_rank": self.target_rank,
            "n_patients": self.n_patients,
            "reciprocal_rank": round(self.reciprocal_rank, 4),
            "margin": round(self.margin, 4),
            "target_score": round(self.target_score, 4),
            "runner_up_id": self.runner_up_id,
        }

    def __repr__(self) -> str:  # pragma: no cover - display only
        verdict = "CORRECT" if self.top1_correct else "WRONG"
        return (
            f"<RankingReport {verdict} rank={self.target_rank}/{self.n_patients} "
            f"margin={self.margin:+.3f}>"
        )


def evaluate_ranking(matches: Sequence[Match], target_patient_id: str) -> RankingReport:
    """Where did the true patient land, and by how much?

    ``margin`` is the gap between the target and the best *other* patient. It is
    signed: negative means the method preferred someone else, and its magnitude
    says whether the miss was close or not close at all. Accuracy alone hides
    that, and on a 12-patient cohort accuracy is one bit.
    """
    ranked = sorted(matches, key=lambda m: -m.score)
    ids = [m.patient_id for m in ranked]
    if target_patient_id not in ids:
        raise KeyError(f"{target_patient_id} not scored")

    rank = ids.index(target_patient_id) + 1
    by_id = {m.patient_id: m.score for m in ranked}
    target_score = by_id[target_patient_id]
    others = [(m.patient_id, m.score) for m in ranked if m.patient_id != target_patient_id]
    runner_up_id, runner_up_score = others[0] if others else ("", float("-inf"))

    return RankingReport(
        top1_correct=rank == 1,
        target_rank=rank,
        n_patients=len(ranked),
        reciprocal_rank=1.0 / rank,
        margin=target_score - runner_up_score,
        target_score=target_score,
        runner_up_id=runner_up_id,
        ranking=[(m.patient_id, m.score) for m in ranked],
    )


# --------------------------------------------------------------------------
# Comparing a reconstructed profile against the curated one
# --------------------------------------------------------------------------


@dataclass
class ProfileReport:
    n_predicted: int
    n_reference: int
    exact_precision: float
    exact_recall: float
    exact_f1: float
    lenient_precision: float
    lenient_recall: float
    lenient_f1: float
    frequency_mae: float | None
    frequency_n: int
    missed_high_frequency: list[tuple[str, str, float]]
    spurious: list[tuple[str, str]]

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if not isinstance(v, list)}
        return {
            k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()
        }


def _f1(p: float, r: float) -> float:
    return 2 * p * r / (p + r) if (p + r) else 0.0


def compare_profiles(
    predicted: DiseaseProfile,
    reference: DiseaseProfile,
    hpo: HpoBundle,
    *,
    lenient_distance: int = 1,
    high_frequency: float = 0.5,
) -> ProfileReport:
    """Grade a literature-reconstructed profile against the curated HPO one.

    Exact match on HPO ids is unforgivingly strict -- "Seizure" and "Generalized
    tonic-clonic seizure" score as a total miss. The lenient variant credits a
    prediction that lands within ``lenient_distance`` edges of a reference term,
    which is closer to what a clinician would call right. Report both; the gap
    between them is itself a finding about the extraction.
    """
    ontology = hpo.ontology
    pred = {ontology.normalize(t) for t in predicted.frequencies}
    ref = {ontology.normalize(t) for t in reference.frequencies}

    exact_tp = len(pred & ref)
    ep = exact_tp / len(pred) if pred else 0.0
    er = exact_tp / len(ref) if ref else 0.0

    def neighbourhood(terms: set[str]) -> set[str]:
        out = set(terms)
        frontier = set(terms)
        for _ in range(lenient_distance):
            nxt: set[str] = set()
            for t in frontier:
                nxt |= ontology.parents.get(t, set())
                nxt |= ontology.children.get(t, set())
            out |= nxt
            frontier = nxt
        return out

    ref_neigh = neighbourhood(ref)
    pred_neigh = neighbourhood(pred)
    lp = len(pred & ref_neigh) / len(pred) if pred else 0.0
    lr = len(ref & pred_neigh) / len(ref) if ref else 0.0

    shared = pred & ref
    errs = [
        abs(predicted.frequencies[t] - reference.frequencies[t])
        for t in shared
        if t in predicted.frequencies and t in reference.frequencies
    ]
    mae = sum(errs) / len(errs) if errs else None

    missed = sorted(
        (
            (t, ontology.label(t), reference.frequencies[t])
            for t in ref - pred_neigh
            if reference.frequencies[t] >= high_frequency
        ),
        key=lambda x: -x[2],
    )
    spurious = sorted(
        ((t, ontology.label(t)) for t in pred - ref_neigh),
        key=lambda x: x[1],
    )

    return ProfileReport(
        n_predicted=len(pred),
        n_reference=len(ref),
        exact_precision=ep,
        exact_recall=er,
        exact_f1=_f1(ep, er),
        lenient_precision=lp,
        lenient_recall=lr,
        lenient_f1=_f1(lp, lr),
        frequency_mae=mae,
        frequency_n=len(errs),
        missed_high_frequency=missed,
        spurious=spurious,
    )
