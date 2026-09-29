"""One directory per disease, one answer key outside all of them.

    assignments/
        OMIM_620851/
            disease.json        what the pair is told: the disease, its gene,
                                the research question
            cohort.json         10 patients, nothing that names a disease
        OMIM_619488/
            ...
    data/answer_key.csv         which patient in which directory, and where
                                every patient really came from

The cohort files are *scrubbed*: a patient is an id, an age, a sex, the HPO
terms observed and the HPO terms recorded absent. The phenopacket id, the path
it lived under (Phenopacket Store files by gene, so the path is the diagnosis)
and the PMID all move to the CSV. Provenance is preserved, one level up.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Sequence

from .cohort import Cohort, Patient
from .disease import DiseaseBrief
from .phenopackets import PhenopacketStore, build_phenopacket_cohort

ASSIGNMENTS_DIR = Path("assignments")
ANSWER_KEY = Path("data/answer_key.csv")
#: The one-line-per-directory version: directory, disease, target patient.
TARGETS_KEY = Path("data/assignment_targets.csv")

#: What the answer key records, one row per patient.
KEY_COLUMNS = (
    "directory", "omim", "disease", "gene",
    "patient_id", "is_target",
    "source_disease_id", "source_disease",
    "phenopacket", "phenopacket_path", "pmid",
)

#: What a patient looks like to a student. Everything else is stripped.
PUBLIC_FIELDS = ("patient_id", "age_years", "sex", "terms", "excluded")


def directory_name(omim: str) -> str:
    """``OMIM:620851`` -> ``OMIM_620851``. Names the disease, which the pair is told anyway."""
    return omim.replace(":", "_")


def public_patient(p: Patient) -> dict:
    """The record a student sees: no source, no notes, no path."""
    d = asdict(p)
    return {k: d[k] for k in PUBLIC_FIELDS}


def scrub(cohort: Cohort) -> list[dict]:
    return [public_patient(p) for p in cohort.patients]


def key_rows(directory: str, brief: DiseaseBrief, cohort: Cohort,
             store: PhenopacketStore) -> list[dict]:
    """One row per patient, with everything ``scrub`` removed."""
    key = cohort.key
    rows = []
    for p in cohort.patients:
        src = key.source_disease[p.patient_id]
        rows.append({
            "directory": directory,
            "omim": brief.omim,
            "disease": brief.label,
            "gene": brief.gene or "",
            "patient_id": p.patient_id,
            "is_target": int(p.patient_id == key.target_patient_id),
            "source_disease_id": src,
            "source_disease": store.disease_label.get(src, src),
            "phenopacket": p.source.get("phenopacket", ""),
            "phenopacket_path": p.source.get("path", ""),
            "pmid": p.source.get("pmid") or "",
        })
    return rows


def write_assignment(omim: str, store: PhenopacketStore, hpo, *,
                     root: Path = ASSIGNMENTS_DIR, n_patients: int = 10,
                     seed: int = 224) -> tuple[Path, DiseaseBrief, Cohort]:
    """Write ``root/OMIM_xxx/{disease.json,cohort.json}``. Returns the key rows' inputs."""
    brief = DiseaseBrief.resolve(omim, store, hpo)
    if not brief.usable:
        raise ValueError("\n".join(brief.warnings))
    cohort = build_phenopacket_cohort(store, hpo, omim,
                                      n_patients=n_patients, seed=seed)

    out = root / directory_name(omim)
    out.mkdir(parents=True, exist_ok=True)
    (out / "disease.json").write_text(json.dumps({
        "omim": brief.omim,
        "label": brief.label,
        "gene": brief.gene,
        "gene_info": brief.gene_info.as_dict() if brief.gene_info else None,
        "n_patients_in_store": brief.n_patients,
        # The papers themselves are not listed: finding them is Part 2's job.
        "n_case_reports": len(brief.pmids),
        "curated_hpo_terms": brief.n_curated_terms,
        "corpus_query": brief.corpus_query,
        "corpus_query_clinical": brief.corpus_query_clinical,
        "grill_question": brief.grill_question,
    }, indent=2) + "\n")
    (out / "cohort.json").write_text(json.dumps(scrub(cohort), indent=2) + "\n")
    return out, brief, cohort


def write_answer_key(rows: Iterable[dict], path: Path = ANSWER_KEY) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=KEY_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


TARGET_COLUMNS = ("directory", "omim", "disease", "gene", "target_patient_id",
                  "source_pmid", "phenopacket")


def write_targets_key(rows: Iterable[dict], path: Path = TARGETS_KEY) -> Path:
    """Derive the compact key from the full one: one row per directory."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=TARGET_COLUMNS)
        w.writeheader()
        for r in rows:
            if str(r["is_target"]) == "1":
                w.writerow({"directory": r["directory"], "omim": r["omim"],
                            "disease": r["disease"], "gene": r["gene"],
                            "target_patient_id": r["patient_id"],
                            "source_pmid": r["pmid"], "phenopacket": r["phenopacket"]})
    return path


def merge_answer_key(new_rows: Sequence[dict], path: Path = ANSWER_KEY) -> Path:
    """Replace the rows for the directories in ``new_rows``; keep every other directory."""
    path = Path(path)
    touched = {r["directory"] for r in new_rows}
    kept: list[dict] = []
    if path.exists():
        with path.open(newline="") as f:
            kept = [r for r in csv.DictReader(f) if r["directory"] not in touched]
    out = write_answer_key(kept + list(new_rows), path)
    write_targets_key(kept + list(new_rows), path.with_name(TARGETS_KEY.name))
    return out


# --------------------------------------------------------------------------
# Reading, from the notebook
# --------------------------------------------------------------------------


def load_assignment(omim: str, root: Path = ASSIGNMENTS_DIR) -> tuple[dict, Cohort]:
    """The disease brief and the scrubbed cohort for one directory."""
    d = Path(root) / directory_name(omim)
    if not d.exists():
        raise FileNotFoundError(
            f"{d} does not exist. Build it with\n"
            f"    python3 scripts/make_assignments.py {omim}"
        )
    disease = json.loads((d / "disease.json").read_text())
    cohort = Cohort.load(d / "cohort.json")
    return disease, cohort


def load_answer(omim: str, path: Path = ANSWER_KEY) -> dict:
    """The answer for one directory, from the CSV kept outside it.

    Returns ``{"target_patient_id": ..., "source_disease": {pid: omim}}`` in the
    same shape the old ``answer_key.json`` had, so grading code is unchanged.
    """
    directory = directory_name(omim)
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; this copy has no answer key.")
    with path.open(newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["directory"] == directory]
    if not rows:
        raise KeyError(f"{directory} is not in {path}")
    target = [r for r in rows if r["is_target"] == "1"]
    return {
        "target_disease_id": rows[0]["omim"],
        "target_disease_name": rows[0]["disease"],
        "target_patient_id": target[0]["patient_id"] if target else "",
        "source_disease": {r["patient_id"]: r["source_disease_id"] for r in rows},
        "provenance": {r["patient_id"]: {"phenopacket": r["phenopacket"],
                                         "path": r["phenopacket_path"],
                                         "pmid": r["pmid"]} for r in rows},
    }
