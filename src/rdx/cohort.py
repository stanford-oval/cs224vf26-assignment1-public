"""Synthetic patient cohorts sampled from real HPO disease annotations.

A patient is a bag of HPO terms. We sample one from a disease profile, then
degrade it the way a real clinic note degrades a textbook description:

``noise``       terms that have nothing to do with the disease (comorbidity,
                incidental findings, a sibling's problem in the family history)
``imprecision`` a specific finding recorded as a vaguer ancestor
                ("Seizure" where the paper says "Focal impaired awareness seizure")
``dropout``     findings simply never written down

Without that degradation the task is a set-equality check and every method
scores 1.0, which teaches nothing. The defaults below are deliberately harsh.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from .hpo import DiseaseProfile, HpoBundle, Ontology


@dataclass
class Patient:
    patient_id: str
    terms: list[str]
    age_years: float | None = None
    sex: str | None = None
    notes: str = ""
    #: Findings a clinician looked for and recorded as ABSENT. Real records
    #: carry these; sampled ones do not. An excluded finding that the candidate
    #: disease reports in nearly everyone is strong evidence against, and no
    #: amount of matching on what the patient does have replaces it.
    excluded: list[str] = field(default_factory=list)
    #: Where this patient came from, when they are a real published case.
    source: dict = field(default_factory=dict)

    def labelled(self, ontology: Ontology) -> list[tuple[str, str]]:
        return [(t, ontology.label(t)) for t in self.terms]


@dataclass
class CohortKey:
    """The answer key. Never show this to the diagnosing agent."""

    target_disease_id: str
    target_disease_name: str
    target_patient_id: str
    source_disease: dict[str, str]  # patient_id -> disease the patient was drawn from
    seed: int
    params: dict = field(default_factory=dict)


@dataclass
class Cohort:
    patients: list[Patient]
    key: CohortKey | None = None

    def __len__(self) -> int:
        return len(self.patients)

    def __iter__(self):
        return iter(self.patients)

    def get(self, patient_id: str) -> Patient:
        for p in self.patients:
            if p.patient_id == patient_id:
                return p
        raise KeyError(patient_id)

    # -- serialization -----------------------------------------------------

    def save(self, cohort_path: str | Path, key_path: str | Path | None = None) -> None:
        cohort_path = Path(cohort_path)
        cohort_path.parent.mkdir(parents=True, exist_ok=True)
        cohort_path.write_text(
            json.dumps([asdict(p) for p in self.patients], indent=2) + "\n"
        )
        if key_path and self.key:
            key_path = Path(key_path)
            key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(json.dumps(asdict(self.key), indent=2) + "\n")

    @classmethod
    def load(cls, cohort_path: str | Path, key_path: str | Path | None = None) -> "Cohort":
        patients = [Patient(**d) for d in json.loads(Path(cohort_path).read_text())]
        key = None
        if key_path and Path(key_path).exists():
            key = CohortKey(**json.loads(Path(key_path).read_text()))
        return cls(patients=patients, key=key)


# --------------------------------------------------------------------------
# Sampling
# --------------------------------------------------------------------------


def sample_patient_terms(
    profile: DiseaseProfile,
    ontology: Ontology,
    rng: random.Random,
    *,
    noise_terms: Sequence[str] = (),
    n_noise: int = 3,
    p_imprecision: float = 0.25,
    p_dropout: float = 0.20,
    min_terms: int = 5,
    max_terms: int = 30,
) -> list[str]:
    """Draw one patient from ``profile`` and degrade the observation."""
    drawn = [t for t, p in profile.frequencies.items() if rng.random() < p]

    # A patient with almost nothing recorded is not interesting; top up with
    # the most frequent findings until the note is plausible.
    if len(drawn) < min_terms:
        ranked = sorted(profile.frequencies, key=profile.frequencies.get, reverse=True)
        for t in ranked:
            if t not in drawn:
                drawn.append(t)
            if len(drawn) >= min_terms:
                break

    observed: list[str] = []
    for t in drawn:
        if rng.random() < p_dropout:
            continue
        if rng.random() < p_imprecision:
            parents = [
                p
                for p in ontology.parents.get(t, ())
                if ontology.is_phenotype(p)
            ]
            if parents:
                t = rng.choice(parents)
        observed.append(t)

    for _ in range(n_noise):
        if noise_terms:
            observed.append(rng.choice(noise_terms))

    # Order carries no signal; shuffling stops a model keying on position.
    unique = list(dict.fromkeys(observed))
    rng.shuffle(unique)
    return unique[:max_terms]


def build_cohort(
    hpo: HpoBundle,
    target_disease: str,
    distractor_diseases: Sequence[str],
    *,
    n_patients: int = 12,
    seed: int = 224,
    n_noise: int = 3,
    p_imprecision: float = 0.25,
    p_dropout: float = 0.20,
    min_ic_for_noise: float = 1.5,
    default_frequency: float = 0.35,
    prefix: str = "P",
) -> Cohort:
    """Build a cohort in which exactly one patient has ``target_disease``.

    ``distractor_diseases`` should be genuinely confusable -- other syndromes
    that share the target's headline findings. Drawing the negatives from
    unrelated diseases makes the task trivial and hides every interesting
    failure mode.
    """
    rng = random.Random(seed)
    ontology = hpo.ontology

    noise_pool = [
        t
        for t in ontology.name
        if ontology.is_phenotype(t)
        and t not in ontology.obsolete
        and hpo.ic.ic(t) >= min_ic_for_noise
    ]

    if n_patients < 2:
        raise ValueError("a cohort needs at least one target and one distractor")

    assignments: list[str] = [target_disease]
    for i in range(n_patients - 1):
        assignments.append(distractor_diseases[i % len(distractor_diseases)])
    rng.shuffle(assignments)

    patients: list[Patient] = []
    source: dict[str, str] = {}
    target_patient_id = ""

    for i, disease_id in enumerate(assignments):
        pid = f"{prefix}{i + 1:02d}"
        profile = hpo.store.profile(disease_id, default_frequency=default_frequency)
        terms = sample_patient_terms(
            profile,
            ontology,
            rng,
            noise_terms=noise_pool,
            n_noise=n_noise,
            p_imprecision=p_imprecision,
            p_dropout=p_dropout,
        )
        patients.append(
            Patient(
                patient_id=pid,
                terms=terms,
                age_years=round(rng.uniform(1.5, 17.0), 1),
                sex=rng.choice(["male", "female"]),
            )
        )
        source[pid] = disease_id
        if disease_id == target_disease:
            target_patient_id = pid

    key = CohortKey(
        target_disease_id=target_disease,
        target_disease_name=hpo.store.disease_name.get(target_disease, target_disease),
        target_patient_id=target_patient_id,
        source_disease=source,
        seed=seed,
        params=dict(
            n_patients=n_patients,
            n_noise=n_noise,
            p_imprecision=p_imprecision,
            p_dropout=p_dropout,
            default_frequency=default_frequency,
            distractors=list(distractor_diseases),
        ),
    )
    return Cohort(patients=patients, key=key)


# --------------------------------------------------------------------------
# Rendering -- what the diagnosing agent actually reads
# --------------------------------------------------------------------------


def render_patient(patient: Patient, ontology: Ontology) -> str:
    lines = [f"### Patient {patient.patient_id}"]
    if patient.age_years is not None:
        lines.append(f"- age: {patient.age_years} years")
    if patient.sex:
        lines.append(f"- sex: {patient.sex}")
    lines.append("- phenotypes:")
    for t in patient.terms:
        lines.append(f"    - {t}  {ontology.label(t)}")
    return "\n".join(lines)


def render_cohort(cohort: Cohort, ontology: Ontology) -> str:
    return "\n\n".join(render_patient(p, ontology) for p in cohort.patients)


def cohort_overlap(cohort: Cohort, ontology: Ontology) -> dict[str, float]:
    """Jaccard overlap of each patient against the rest of the cohort.

    A sanity check on difficulty: if the target patient shares almost nothing
    with the distractors, the cohort is too easy.
    """
    sets = {p.patient_id: set(p.terms) for p in cohort.patients}
    out = {}
    for pid, s in sets.items():
        others: set[str] = set().union(*(v for k, v in sets.items() if k != pid))
        out[pid] = len(s & others) / max(len(s | others), 1)
    return out
