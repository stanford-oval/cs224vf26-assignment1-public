"""GA4GH Phenopackets as the patient cohort.

A *phenopacket* is the GA4GH standard for sharing one individual's phenotype
and genotype in a machine-readable form. `Phenopacket Store
<https://github.com/monarch-initiative/phenopacket-store>`_ is a corpus of them
curated from published case reports: 10,377 individuals across 780 Mendelian
diseases, each carrying HPO terms, an OMIM diagnosis, the causative variant and
the PMID it came from. Danis et al., *HGG Advances* 2025.

Using it changes what this assignment is. A synthetic patient sampled from a
disease's own frequency vector is a draw from the answer key, and matching it
back is closer to a lookup than a diagnosis. A phenopacket is a person somebody
published, with the phenotyping they actually received.

Two consequences worth stating before you look at any numbers.

**Real records are unevenly phenotyped.** The median patient here has seven
observed findings; some have forty. A scorer that sums evidence over observed
terms will prefer the thoroughly examined patient over the right one, and that
is a property of the data, not a bug you can tune away.

**Real records contain explicit negatives.** 87% of these patients have at
least one *excluded* finding — a clinician looked for nystagmus and recorded
its absence. That is evidence, and it is the kind synthetic cohorts never have.
An excluded finding that the candidate disease reports in nearly everyone is
strong evidence against, and no amount of matching on what the patient *does*
have can substitute for it.
"""

from __future__ import annotations

import json
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

#: Resolved against the repository, not the working directory, so a notebook
#: started from anywhere (Colab runs from /content) finds the same file.
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = REPO_ROOT / "data" / "phenopackets" / "all_phenopackets.zip"

#: Where to fetch it, if the archive is not on disk.
STORE_URL = (
    "https://github.com/monarch-initiative/phenopacket-store/releases/"
    "download/0.1.27/all_phenopackets.zip"
)


@dataclass
class Phenopacket:
    """One published individual."""

    packet_id: str
    path: str
    disease_id: str
    disease_label: str
    observed: list[str]
    excluded: list[str]
    gene: str | None = None
    variant: str | None = None
    pmid: str | None = None
    sex: str | None = None
    age_iso: str | None = None
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def cohort(self) -> str:
        """The gene directory this packet lives under."""
        parts = self.path.split("/")
        return parts[1] if len(parts) > 1 else ""

    @property
    def age_years(self) -> float | None:
        """ISO-8601 duration to years, approximately. ``P10Y6M`` -> 10.5."""
        s = self.age_iso or ""
        if not s.startswith("P"):
            return None
        import re  # noqa: PLC0415

        y = re.search(r"(\d+)Y", s)
        m = re.search(r"(\d+)M", s)
        d = re.search(r"(\d+)D", s)
        if not (y or m or d):
            return None
        return round(
            (int(y.group(1)) if y else 0)
            + (int(m.group(1)) if m else 0) / 12
            + (int(d.group(1)) if d else 0) / 365.25,
            1,
        )

    def __len__(self) -> int:
        return len(self.observed)


def _parse(path: str, raw: bytes) -> Phenopacket | None:
    d = json.loads(raw)
    diseases = d.get("diseases") or []
    if not diseases:
        return None
    term = (diseases[0] or {}).get("term") or {}
    disease_id = term.get("id")
    if not disease_id:
        return None

    observed: list[str] = []
    excluded: list[str] = []
    labels: dict[str, str] = {}
    for p in d.get("phenotypicFeatures") or []:
        t = p.get("type") or {}
        hid = t.get("id")
        if not hid:
            continue
        labels[hid] = t.get("label", hid)
        (excluded if p.get("excluded") else observed).append(hid)

    gene = variant = None
    for interp in d.get("interpretations") or []:
        for gi in ((interp.get("diagnosis") or {}).get("genomicInterpretations") or []):
            vd = (gi.get("variantInterpretation") or {}).get("variationDescriptor") or {}
            gene = gene or ((vd.get("geneContext") or {}).get("symbol"))
            variant = variant or vd.get("id")

    pmid = None
    for ref in (d.get("metaData") or {}).get("externalReferences") or []:
        if str(ref.get("id", "")).startswith("PMID:"):
            pmid = ref["id"].split(":", 1)[1]
            break

    subject = d.get("subject") or {}
    age = ((subject.get("timeAtLastEncounter") or {}).get("age") or {})

    return Phenopacket(
        packet_id=d.get("id") or Path(path).stem,
        path=path,
        disease_id=disease_id,
        disease_label=term.get("label", disease_id),
        observed=observed,
        excluded=excluded,
        gene=gene,
        variant=variant,
        pmid=pmid,
        sex=(subject.get("sex") or "").lower() or None,
        age_iso=age.get("iso8601duration"),
        labels=labels,
    )


class PhenopacketStore:
    """The corpus, indexed by disease."""

    def __init__(self, packets: Sequence[Phenopacket]):
        self.packets = list(packets)
        self.by_disease: dict[str, list[Phenopacket]] = defaultdict(list)
        self.disease_label: dict[str, str] = {}
        for p in self.packets:
            self.by_disease[p.disease_id].append(p)
            self.disease_label.setdefault(p.disease_id, p.disease_label)

    @classmethod
    def load(cls, path: str | Path = DEFAULT_STORE, ontology=None,
             fetch: bool = True) -> "PhenopacketStore":
        """Read the release archive. ``ontology`` normalises obsolete HPO ids.

        The archive is not committed (19MB, a versioned release). If it is
        missing and ``fetch`` is true, it is downloaded once from the pinned
        release URL; on a fresh clone or a Colab runtime this is the normal
        first-run path.
        """
        path = Path(path)
        if not path.exists():
            if not fetch:
                raise FileNotFoundError(
                    f"{path} not found. Fetch it once:\n"
                    f"    python3 scripts/fetch_phenopackets.py"
                )
            print(f"phenopacket store not on disk; fetching {STORE_URL} (19MB) ...", flush=True)
            fetch_store(path)
        out: list[Phenopacket] = []
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if not name.endswith(".json"):
                    continue
                try:
                    p = _parse(name, z.read(name))
                except (json.JSONDecodeError, KeyError):
                    continue
                if p is None:
                    continue
                if ontology is not None:
                    p.observed = [ontology.normalize(t) for t in p.observed
                                  if ontology.exists(t)]
                    p.excluded = [ontology.normalize(t) for t in p.excluded
                                  if ontology.exists(t)]
                out.append(p)
        return cls(out)

    # -- queries -----------------------------------------------------------

    def diseases(self, min_patients: int = 1) -> list[str]:
        return [d for d, v in self.by_disease.items() if len(v) >= min_patients]

    def summary(self, top: int = 10) -> list[tuple[str, str, int]]:
        rows = [(d, self.disease_label[d], len(v)) for d, v in self.by_disease.items()]
        return sorted(rows, key=lambda r: -r[2])[:top]

    def observed_profile(self, disease_id: str) -> dict[str, float]:
        """Empirical P(term | disease) from the cohort itself.

        Denominator counts only patients where the term was *recorded at all*,
        observed or excluded. Counting silence as absence would read an
        unexamined finding as a negative one, which is the single most common
        way to get a phenotype frequency wrong.
        """
        obs: Counter[str] = Counter()
        seen: Counter[str] = Counter()
        for p in self.by_disease.get(disease_id, ()):
            for t in set(p.observed):
                obs[t] += 1
                seen[t] += 1
            for t in set(p.excluded):
                seen[t] += 1
        return {t: obs[t] / seen[t] for t in seen if seen[t]}

    def __len__(self) -> int:
        return len(self.packets)

    def __repr__(self) -> str:  # pragma: no cover - display only
        return (f"<PhenopacketStore {len(self.packets)} patients, "
                f"{len(self.by_disease)} diseases>")


# --------------------------------------------------------------------------
# Choosing the distractors
# --------------------------------------------------------------------------


def confusable_diseases(
    store: PhenopacketStore,
    target: str,
    hpo,
    *,
    n: int = 12,
    min_patients: int = 8,
    min_terms: int = 4,
) -> list[tuple[float, str, str, int]]:
    """Diseases whose *patients* look most like the target's, by IC-weighted overlap.

    Selected from the cohort data rather than from curated annotations, so the
    distractors are hard in the way the actual records are hard. Picking them
    by hand, or from an unrelated part of the ontology, makes every method look
    good and hides every interesting failure.
    """
    ont, ic = hpo.ontology, hpo.ic

    def closure(disease_id: str) -> set[str]:
        out: set[str] = set()
        for p in store.by_disease.get(disease_id, ()):
            for t in p.observed:
                out |= ont.ancestors(t)
        return out

    tgt = closure(target)
    if not tgt:
        return []
    tw = sum(ic.ic(t) for t in tgt)

    rows = []
    for d in store.diseases(min_patients):
        if d == target:
            continue
        pats = store.by_disease[d]
        if sum(len(p.observed) for p in pats) / len(pats) < min_terms:
            continue
        c = closure(d)
        if not c:
            continue
        num = sum(ic.ic(t) for t in tgt & c)
        den = (tw * sum(ic.ic(t) for t in c)) ** 0.5
        if den:
            rows.append((num / den, d, store.disease_label[d], len(pats)))
    return sorted(rows, reverse=True)[:n]


def fetch_store(dest: str | Path = DEFAULT_STORE, url: str = STORE_URL) -> Path:
    """Download the release archive. Prints nothing on success."""
    import urllib.request  # noqa: PLC0415

    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    return dest


# --------------------------------------------------------------------------
# Building a cohort of real patients
# --------------------------------------------------------------------------


def build_phenopacket_cohort(
    store: PhenopacketStore,
    hpo,
    target_disease: str,
    *,
    n_patients: int = 12,
    seed: int = 224,
    distractors: Sequence[str] | None = None,
    n_distractor_pool: int = 14,
    min_terms: int = 6,
    prefix: str = "P",
):
    """One real patient with ``target_disease``, the rest real and confusable.

    Every patient is a published individual: their observed findings, their
    recorded negatives, their age and sex as the case report gave them. The
    answer key is the phenopacket's own OMIM diagnosis, so it is a fact about
    the record rather than a property of how we sampled.

    ``min_terms`` filters out patients with almost nothing recorded. That is a
    real bias and worth naming: it removes exactly the hardest cases, the ones
    where a clinician had little to go on. Set it to 0 to put them back.
    """
    import random  # noqa: PLC0415

    from .cohort import Cohort, CohortKey, Patient  # noqa: PLC0415

    rng = random.Random(seed)

    if distractors is None:
        distractors = [d for _, d, _, _ in
                       confusable_diseases(store, target_disease, hpo,
                                           n=n_distractor_pool)]
    if not distractors:
        raise ValueError("no distractor diseases found")

    def pick(disease_id: str) -> Phenopacket | None:
        pool = [p for p in store.by_disease.get(disease_id, ())
                if len(p.observed) >= min_terms]
        return rng.choice(pool) if pool else None

    target = pick(target_disease)
    if target is None:
        raise ValueError(f"no {target_disease} patient with >= {min_terms} findings")

    chosen: list[tuple[Phenopacket, str]] = [(target, target_disease)]
    pool = list(distractors)
    rng.shuffle(pool)
    i = 0
    while len(chosen) < n_patients and i < len(pool) * 4:
        d = pool[i % len(pool)]
        i += 1
        pk = pick(d)
        if pk and all(pk.path != c.path for c, _ in chosen):
            chosen.append((pk, d))

    rng.shuffle(chosen)

    patients, source, target_pid = [], {}, ""
    for i, (pk, disease_id) in enumerate(chosen):
        pid = f"{prefix}{i + 1:02d}"
        patients.append(Patient(
            patient_id=pid,
            terms=list(dict.fromkeys(pk.observed)),
            excluded=list(dict.fromkeys(pk.excluded)),
            age_years=pk.age_years,
            sex=pk.sex,
            source={"phenopacket": pk.packet_id, "path": pk.path, "pmid": pk.pmid},
        ))
        source[pid] = disease_id
        if disease_id == target_disease:
            target_pid = pid

    key = CohortKey(
        target_disease_id=target_disease,
        target_disease_name=store.disease_label.get(target_disease, target_disease),
        target_patient_id=target_pid,
        source_disease=source,
        seed=seed,
        params={"n_patients": n_patients, "min_terms": min_terms,
                "distractors": list(distractors), "source": "phenopacket-store"},
    )
    return Cohort(patients=patients, key=key)
