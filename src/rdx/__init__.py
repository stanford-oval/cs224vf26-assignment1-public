"""Rare-disease diagnosis with an agentic literature pipeline (CS224V).

Layers, bottom up:

    hpo      the Human Phenotype Ontology and its disease annotations
    cohort   synthetic patients sampled from those annotations
    scoring  patient-vs-disease matching and the metrics that grade it
    grill    driving and dissecting the GRILL literature-research agent
    sliders  driving and dissecting the SLIDERS extraction engine
"""

from .hpo import (
    Annotation,
    AnnotationStore,
    DiseaseProfile,
    HpoBundle,
    InformationContent,
    Ontology,
    load_hpo,
    parse_frequency,
)
from .cohort import (
    Cohort,
    CohortKey,
    Patient,
    build_cohort,
    cohort_overlap,
    render_cohort,
    render_patient,
    sample_patient_terms,
)
from .scoring import (
    Match,
    ProfileReport,
    RankingReport,
    TermContribution,
    compare_profiles,
    evaluate_ranking,
    likelihood_score,
    rank_cohort,
    resnik_score,
)

__all__ = [
    "Annotation", "AnnotationStore", "DiseaseProfile", "HpoBundle",
    "InformationContent", "Ontology", "load_hpo", "parse_frequency",
    "Cohort", "CohortKey", "Patient", "build_cohort", "cohort_overlap",
    "render_cohort", "render_patient", "sample_patient_terms",
    "Match", "ProfileReport", "RankingReport", "TermContribution",
    "compare_profiles", "evaluate_ranking", "likelihood_score",
    "rank_cohort", "resnik_score",
]

# System adapters. Imported lazily inside functions, so importing rdx does not
# require GRILL or SLIDERS to be present.
from . import disease, extract, grill, phenopackets, rag, serper, workflow  # noqa: E402,F401
from .hpo import TermMatch, TermMatcher  # noqa: E402

__all__ += ["disease", "extract", "grill", "phenopackets", "rag", "serper", "workflow",
            "TermMatch", "TermMatcher"]
