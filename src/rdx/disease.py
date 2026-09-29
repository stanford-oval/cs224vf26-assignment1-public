"""Resolve one OMIM id into everything the assignment needs.

Each pair is given a different rare disease. Everything else — the gene, the
literature search, the research question handed to GRILL, the cohort of real
patients, the curated answer key — is derived from that one identifier, so a
pair changes a single line and the whole notebook re-targets.

    brief = DiseaseBrief.resolve("OMIM:620851", store, hpo)
    brief.gene            # 'RNU4-2'
    brief.pmids           # the case reports the patients came from
    brief.grill_question  # ready to hand to the research agent

Nothing here invents facts. The gene and the source PMIDs come from the
phenopackets themselves; the label and the curated phenotype profile come from
HPO. If a disease is missing from either, ``resolve`` says so rather than
guessing.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .gene import GeneInfo, gene_info

QUESTION_TEMPLATE = """\
For {label} (OMIM {omim}){gene_clause}: how can one identify which patients
have this disease from their phenotypes alone?

Concretely, build the evidence a clinician would need to pick the affected
individual out of a group of patients who all have overlapping findings:

  1. Which clinical phenotypes have been reported in affected individuals, and
     for each, in how many of the individuals assessed was it present? Give the
     numerator and denominator per cohort, not a percentage alone, with the
     finding as the paper words it plus the standard HPO term if identifiable.
  2. Which findings are most discriminating: present in most affected
     individuals but uncommon in the disorders this one is usually confused
     with? Name those disorders and say how confident the distinction is.
  3. Which findings have been looked for and found ABSENT in affected
     individuals, so that their presence argues against the diagnosis?
  4. Whether the phenotype differs by variant type, position, age or sex.
  5. Any finding one paper reports and another explicitly contradicts.

Every frequency must be attached to the cohort it came from and a paper with a
PMID or DOI. Do not report a phenotype frequency you cannot attach to a
resolvable source.
"""


@dataclass
class DiseaseBrief:
    """Everything derived from one OMIM identifier."""

    omim: str
    label: str
    gene: str | None
    n_patients: int
    pmids: tuple[str, ...]
    n_curated_terms: int
    curated_refs: tuple[str, ...]
    warnings: list[str] = field(default_factory=list)
    gene_info: "GeneInfo | None" = None

    # -- derived -----------------------------------------------------------

    @property
    def omim_number(self) -> str:
        return self.omim.split(":", 1)[-1]

    @property
    def corpus_query(self) -> str:
        """A PubMed Central query for this disease's literature."""
        terms = []
        if self.gene:
            terms.append(f'"{self.gene}"')
        short = self.label.split(",")[0].split(";")[0].strip()
        if short and short.lower() not in (self.gene or "").lower():
            terms.append(f'"{short}"')
        return " OR ".join(terms) or f'"{self.label}"'

    @property
    def corpus_query_clinical(self) -> str:
        """The same, narrowed to papers likely to carry phenotype counts."""
        return (f"({self.corpus_query}) AND (phenotype OR cohort OR "
                f'"case report" OR clinical)')

    @property
    def grill_question(self) -> str:
        gene_clause = f", caused by variants in {self.gene}" if self.gene else ""
        return QUESTION_TEMPLATE.format(
            label=self.label, omim=f"#{self.omim_number}", gene_clause=gene_clause
        )

    @property
    def usable(self) -> bool:
        return not self.warnings

    # -- construction ------------------------------------------------------

    @classmethod
    def resolve(cls, omim: str, store, hpo, *, min_patients: int = 8) -> "DiseaseBrief":
        """Look the disease up in both sources and report what is missing."""
        warnings: list[str] = []

        packets = store.by_disease.get(omim, [])
        if not packets:
            warnings.append(
                f"{omim} has no patients in Phenopacket Store. "
                f"Pick from suggest_diseases()."
            )
        elif len(packets) < min_patients:
            warnings.append(
                f"{omim} has only {len(packets)} patients "
                f"(want >= {min_patients}); the cohort will repeat individuals."
            )

        genes = Counter(p.gene for p in packets if p.gene)
        gene = genes.most_common(1)[0][0] if genes else None
        if not gene:
            warnings.append(f"no causative gene recorded for {omim}")

        pmids = tuple(sorted({p.pmid for p in packets if p.pmid}))

        profile = hpo.store.profile(omim)
        if len(profile) == 0:
            warnings.append(
                f"{omim} has no HPO phenotype annotations, so there is no "
                f"answer key to grade the reconstruction against."
            )

        label = (store.disease_label.get(omim)
                 or hpo.store.disease_name.get(omim) or omim)

        return cls(
            omim=omim,
            label=label,
            gene=gene,
            n_patients=len(packets),
            pmids=pmids,
            n_curated_terms=len(profile),
            curated_refs=profile.references,
            warnings=warnings,
            gene_info=gene_info(gene),
        )

    def summary(self) -> str:
        lines = [
            f"{self.label}  ({self.omim})",
            (self.gene_info.describe() if self.gene_info
             else f"  gene                 {self.gene or '(none recorded)'}"),
            f"  curated HPO terms    {self.n_curated_terms}",
            f"  case reports         {len(self.pmids)} PMIDs",
            f"  curated from         {len(self.curated_refs)} references",
            f"  literature query     {self.corpus_query}",
        ]
        for w in self.warnings:
            lines.append(f"  WARNING  {w}")
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover - display only
        ok = "ok" if self.usable else f"{len(self.warnings)} warning(s)"
        return f"<DiseaseBrief {self.omim} {self.label[:40]!r} gene={self.gene} {ok}>"


def suggest_diseases(store, hpo, *, min_patients: int = 10,
                     min_terms: int = 30, limit: int = 40,
                     recent_omim: int = 620000, older_omim: int = 617500) -> list[dict]:
    """Diseases this assignment will work for, best first.

    A disease needs enough published patients to build a cohort from, and
    enough curated HPO annotations to grade a reconstruction against. Beyond
    that the ordering is deliberate, because it decides what the course is
    about:

    1. named 2024 or later (OMIM number >= ``recent_omim``), with at least two
       source papers, so SLIDERS has something to reconcile;
    2. named 2018-2023, at least two papers;
    3. named 2024 or later, a single paper;
    4. everything else.

    Within a tier, more patients first. The premise of the exercise is a
    disease described *after* the knowledge base was assembled; sorting by
    patient count alone fills the list with NF1 and Marfan, which every model
    already knows by heart.
    """
    rows = []
    for omim, packets in store.by_disease.items():
        if len(packets) < min_patients or not omim.startswith("OMIM:"):
            continue
        profile = hpo.store.profile(omim)
        if len(profile) < min_terms:
            continue
        genes = Counter(p.gene for p in packets if p.gene)
        number = int(omim.split(":")[1])
        n_pmids = len({p.pmid for p in packets if p.pmid})
        if number >= recent_omim and n_pmids >= 2:
            tier = 0
        elif number >= older_omim and n_pmids >= 2:
            tier = 1
        elif number >= recent_omim:
            tier = 2
        else:
            tier = 3
        rows.append({
            "omim": omim,
            "label": store.disease_label.get(omim, omim),
            "gene": genes.most_common(1)[0][0] if genes else None,
            "patients": len(packets),
            "curated_terms": len(profile),
            "pmids": n_pmids,
            "tier": tier,
        })
    rows.sort(key=lambda r: (r["tier"], -r["patients"], -r["curated_terms"]))
    return rows[:limit]
