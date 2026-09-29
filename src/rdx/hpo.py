"""Human Phenotype Ontology: loading, propagation, information content, similarity.

Everything here is pure Python over the two files in ``data/``:

* ``hp.json``          -- the ontology graph (OBO Graphs JSON release).
* ``phenotype.hpoa``   -- disease -> phenotype annotations, with frequencies.

No network, no LLM. This module is the *deterministic* half of the assignment:
it defines what "this patient looks like this disease" means, so that the
agentic half (GRILL + SLIDERS) can be measured against something fixed.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping, Sequence

# --------------------------------------------------------------------------
# Ontology
# --------------------------------------------------------------------------

_OBO_ID = re.compile(r"HP_(\d{7})$")

PHENOTYPIC_ABNORMALITY = "HP:0000118"


def _curie(obo_url: str) -> str | None:
    m = _OBO_ID.search(obo_url)
    return f"HP:{m.group(1)}" if m else None


@dataclass(eq=False)  # identity hash, so the lru_cache below can key on self
class Ontology:
    """The HPO DAG, with the parent/child closure precomputed."""

    name: dict[str, str] = field(default_factory=dict)
    definition: dict[str, str] = field(default_factory=dict)
    parents: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    children: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    obsolete: set[str] = field(default_factory=set)
    alt_to_main: dict[str, str] = field(default_factory=dict)
    synonyms: dict[str, list[str]] = field(default_factory=dict)
    #: Broad and related synonyms, kept separately. They are looser than exact
    #: and narrow ones -- "Epilepsy" is a *related* synonym of "Seizure", not a
    #: rename -- so using them trades precision for recall. TermMatcher ignores
    #: this field; deciding whether to use it is part of the assignment.
    related_synonyms: dict[str, list[str]] = field(default_factory=dict)

    # -- construction ------------------------------------------------------

    @classmethod
    def load(cls, hp_json: str | Path) -> "Ontology":
        raw = json.loads(Path(hp_json).read_text())
        graph = raw["graphs"][0]
        ont = cls()

        for node in graph.get("nodes", []):
            hid = _curie(node.get("id", ""))
            if hid is None:
                continue
            meta = node.get("meta", {}) or {}
            if meta.get("deprecated"):
                ont.obsolete.add(hid)
                for repl in meta.get("basicPropertyValues", []):
                    if repl.get("pred", "").endswith("term_replaced_by"):
                        target = _curie(repl.get("val", "")) or repl.get("val")
                        if target:
                            ont.alt_to_main[hid] = target
            ont.name[hid] = node.get("lbl") or hid
            syns = [
                s["val"]
                for s in meta.get("synonyms", [])
                if s.get("val") and s.get("pred") in ("hasExactSynonym", "hasNarrowSynonym")
            ]
            if syns:
                ont.synonyms[hid] = syns
            loose = [
                s["val"]
                for s in meta.get("synonyms", [])
                if s.get("val")
                and s.get("pred") in ("hasBroadSynonym", "hasRelatedSynonym")
            ]
            if loose:
                ont.related_synonyms[hid] = loose
            if meta.get("definition"):
                ont.definition[hid] = meta["definition"].get("val", "")
            for xref in meta.get("basicPropertyValues", []):
                if xref.get("pred", "").endswith("hasAlternativeId"):
                    ont.alt_to_main[xref["val"]] = hid

        for edge in graph.get("edges", []):
            if edge.get("pred") != "is_a":
                continue
            child, parent = _curie(edge["sub"]), _curie(edge["obj"])
            if child and parent:
                ont.parents[child].add(parent)
                ont.children[parent].add(child)

        return ont

    # -- graph queries -----------------------------------------------------

    def normalize(self, term: str) -> str:
        """Map an obsolete/alternate id onto its current primary id."""
        seen = set()
        while term in self.alt_to_main and term not in seen:
            seen.add(term)
            term = self.alt_to_main[term]
        return term

    def exists(self, term: str) -> bool:
        return self.normalize(term) in self.name

    def label(self, term: str) -> str:
        return self.name.get(self.normalize(term), term)

    @lru_cache(maxsize=None)
    def ancestors(self, term: str, include_self: bool = True) -> frozenset[str]:
        """All is_a ancestors, transitively. Cached -- the hot path in scoring."""
        term = self.normalize(term)
        out: set[str] = {term} if include_self else set()
        stack = list(self.parents.get(term, ()))
        while stack:
            node = stack.pop()
            if node in out:
                continue
            out.add(node)
            stack.extend(self.parents.get(node, ()))
        return frozenset(out)

    @lru_cache(maxsize=None)
    def descendants(self, term: str, include_self: bool = True) -> frozenset[str]:
        term = self.normalize(term)
        out: set[str] = {term} if include_self else set()
        stack = list(self.children.get(term, ()))
        while stack:
            node = stack.pop()
            if node in out:
                continue
            out.add(node)
            stack.extend(self.children.get(node, ()))
        return frozenset(out)

    def is_phenotype(self, term: str) -> bool:
        """True for terms under Phenotypic abnormality (excludes modifiers,
        inheritance, frequency and clinical-course branches)."""
        return PHENOTYPIC_ABNORMALITY in self.ancestors(self.normalize(term))

    def depth(self, term: str) -> int:
        return len(self.ancestors(term)) - 1

    def __len__(self) -> int:  # pragma: no cover - convenience
        return len(self.name)


# --------------------------------------------------------------------------
# Disease annotations
# --------------------------------------------------------------------------

#: HPO frequency-term CURIEs -> representative probability.
_FREQ_TERM = {
    "HP:0040280": 1.00,  # Obligate
    "HP:0040281": 0.90,  # Very frequent (80-99%)
    "HP:0040282": 0.55,  # Frequent (30-79%)
    "HP:0040283": 0.17,  # Occasional (5-29%)
    "HP:0040284": 0.025,  # Very rare (<4-5%)
    "HP:0040285": 0.0,  # Excluded
}


def parse_frequency(raw: str | None) -> float | None:
    """``"38/50"`` -> 0.76, ``"76%"`` -> 0.76, ``"HP:0040281"`` -> 0.9.

    Returns ``None`` when the annotation states no frequency, which is not the
    same as stating zero -- callers decide what an unknown frequency means.
    """
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith("HP:"):
        return _FREQ_TERM.get(raw)
    if raw.endswith("%"):
        try:
            return max(0.0, min(1.0, float(raw[:-1]) / 100.0))
        except ValueError:
            return None
    if "/" in raw:
        num, _, den = raw.partition("/")
        try:
            n, d = float(num), float(den)
        except ValueError:
            return None
        return max(0.0, min(1.0, n / d)) if d > 0 else None
    return None


@dataclass
class Annotation:
    """One row of ``phenotype.hpoa``."""

    disease_id: str
    disease_name: str
    hpo_id: str
    frequency: float | None
    frequency_raw: str
    n_observed: int | None
    n_total: int | None
    negated: bool
    aspect: str
    references: tuple[str, ...]


@dataclass
class DiseaseProfile:
    """A disease's phenotype fingerprint: term -> P(term | disease)."""

    disease_id: str
    disease_name: str
    frequencies: dict[str, float]
    excluded: set[str] = field(default_factory=set)
    references: tuple[str, ...] = ()

    @property
    def terms(self) -> set[str]:
        return set(self.frequencies)

    def __len__(self) -> int:
        return len(self.frequencies)


class AnnotationStore:
    """All disease -> phenotype annotations, indexed both ways."""

    def __init__(self, annotations: Sequence[Annotation]):
        self.annotations = list(annotations)
        self.by_disease: dict[str, list[Annotation]] = defaultdict(list)
        self.disease_name: dict[str, str] = {}
        for a in self.annotations:
            self.by_disease[a.disease_id].append(a)
            self.disease_name.setdefault(a.disease_id, a.disease_name)

    # -- construction ------------------------------------------------------

    @classmethod
    def load(
        cls,
        hpoa: str | Path,
        ontology: Ontology | None = None,
        prefixes: tuple[str, ...] = ("OMIM:",),
        phenotypes_only: bool = True,
    ) -> "AnnotationStore":
        rows: list[Annotation] = []
        with Path(hpoa).open() as fh:
            header: list[str] | None = None
            for line in fh:
                if line.startswith("#"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if header is None:
                    header = parts
                    continue
                rec = dict(zip(header, parts))
                did = rec.get("database_id", "")
                if prefixes and not did.startswith(prefixes):
                    continue
                if phenotypes_only and rec.get("aspect") != "P":
                    continue
                hid = rec.get("hpo_id", "")
                if ontology is not None:
                    hid = ontology.normalize(hid)
                    if not ontology.exists(hid):
                        continue
                raw = rec.get("frequency", "")
                n_obs = n_tot = None
                if "/" in raw:
                    a, _, b = raw.partition("/")
                    try:
                        n_obs, n_tot = int(a), int(b)
                    except ValueError:
                        n_obs = n_tot = None
                rows.append(
                    Annotation(
                        disease_id=did,
                        disease_name=rec.get("disease_name", ""),
                        hpo_id=hid,
                        frequency=parse_frequency(raw),
                        frequency_raw=raw,
                        n_observed=n_obs,
                        n_total=n_tot,
                        negated=rec.get("qualifier", "") == "NOT",
                        aspect=rec.get("aspect", ""),
                        references=tuple(
                            r for r in rec.get("reference", "").split(";") if r
                        ),
                    )
                )
        return cls(rows)

    # -- queries -----------------------------------------------------------

    @property
    def diseases(self) -> list[str]:
        return list(self.by_disease)

    def profile(
        self,
        disease_id: str,
        default_frequency: float = 0.35,
        min_frequency: float = 0.0,
        smoothing: float = 1.0,
    ) -> DiseaseProfile:
        """Collapse a disease's rows into term -> probability.

        ``default_frequency`` is used where the curator recorded a term but no
        frequency. Rows with ``0/N`` (or the *Excluded* frequency term) become
        explicit exclusions rather than probability-zero observations: they are
        evidence *against*, and the scorers use them that way.

        ``smoothing`` is Laplace shrinkage on the curated counts:
        ``(n + s) / (m + 2s)``. It matters far more than it looks.

        HPO records "Anxiety 2/2" and "Gray matter heterotopia 1/1" for this
        disease. Read literally those are certainties, and a scorer that
        charges for expected-but-absent findings then bills a real patient
        ``log(1 - 0.999) = -6.9`` for not having a finding attested in a single
        case. Four such terms cost the true patient 28 points and dropped them
        from rank 1 to rank 3.

        With ``smoothing=1`` those become 0.75 and 0.67, while 38/50 moves only
        to 0.75 -- small denominators shrink toward the prior and large ones
        barely move, which is the whole point. Set it to 0 to see the damage.
        """
        freqs: dict[str, float] = {}
        excluded: set[str] = set()
        refs: set[str] = set()
        for a in self.by_disease.get(disease_id, ()):
            refs.update(a.references)
            if (smoothing and a.n_total and a.n_observed is not None
                    and a.n_observed > 0):
                p = (a.n_observed + smoothing) / (a.n_total + 2 * smoothing)
            else:
                p = a.frequency if a.frequency is not None else default_frequency
            if a.negated or (a.n_observed == 0 and a.n_total) or p == 0.0:
                excluded.add(a.hpo_id)
                continue
            if p < min_frequency:
                continue
            freqs[a.hpo_id] = max(freqs.get(a.hpo_id, 0.0), p)
        excluded -= set(freqs)
        return DiseaseProfile(
            disease_id=disease_id,
            disease_name=self.disease_name.get(disease_id, disease_id),
            frequencies=freqs,
            excluded=excluded,
            references=tuple(sorted(refs)),
        )

    def without(self, disease_ids: Iterable[str]) -> "AnnotationStore":
        """A copy with these diseases removed.

        This is how the assignment builds a *pre-discovery* knowledge base: the
        target disease is held out, so phenotype matching alone cannot find it
        and the literature pipeline has to supply the missing profile.
        """
        drop = set(disease_ids)
        return AnnotationStore([a for a in self.annotations if a.disease_id not in drop])

    def search(self, pattern: str) -> list[tuple[str, str]]:
        rx = re.compile(pattern, re.I)
        return sorted(
            {(d, n) for d, n in self.disease_name.items() if rx.search(n)}
        )


# --------------------------------------------------------------------------
# Information content
# --------------------------------------------------------------------------


class InformationContent:
    """IC(t) = -log P(t), with P estimated over diseases, propagated up the DAG.

    A term's probability counts every disease annotated to it *or to any of its
    descendants* -- otherwise a specific term would look rarer than its own
    children, which breaks the similarity measures downstream.
    """

    def __init__(self, ontology: Ontology, store: AnnotationStore):
        self.ontology = ontology
        counts: dict[str, int] = defaultdict(int)
        n_diseases = 0
        for disease_id, rows in store.by_disease.items():
            n_diseases += 1
            closure: set[str] = set()
            for a in rows:
                if a.negated:
                    continue
                closure |= ontology.ancestors(a.hpo_id)
            for t in closure:
                counts[t] += 1
        self.n_diseases = max(n_diseases, 1)
        self.counts = dict(counts)
        self._ic = {
            t: -math.log(max(c, 1) / self.n_diseases) for t, c in counts.items()
        }
        self.max_ic = max(self._ic.values()) if self._ic else 1.0

    def ic(self, term: str) -> float:
        """IC of a term; an unseen term is treated as maximally informative."""
        return self._ic.get(self.ontology.normalize(term), self.max_ic)

    __call__ = ic

    def mica(self, a: str, b: str) -> tuple[str | None, float]:
        """Most informative common ancestor of two terms, and its IC."""
        common = self.ontology.ancestors(a) & self.ontology.ancestors(b)
        if not common:
            return None, 0.0
        best = max(common, key=self.ic)
        return best, self.ic(best)

    def most_informative(self, terms: Iterable[str], k: int = 10):
        return sorted(terms, key=self.ic, reverse=True)[:k]


# --------------------------------------------------------------------------
# Convenience loader
# --------------------------------------------------------------------------


@dataclass
class HpoBundle:
    ontology: Ontology
    store: AnnotationStore
    ic: InformationContent

    def label(self, term: str) -> str:
        return self.ontology.label(term)

    def describe(self, terms: Iterable[str]) -> list[tuple[str, str, float]]:
        return [(t, self.label(t), round(self.ic.ic(t), 2)) for t in terms]


def load_hpo(data_dir: str | Path = "data") -> HpoBundle:
    data_dir = Path(data_dir)
    ontology = Ontology.load(data_dir / "hp.json")
    store = AnnotationStore.load(data_dir / "phenotype.hpoa", ontology=ontology)
    return HpoBundle(ontology=ontology, store=store, ic=InformationContent(ontology, store))


# --------------------------------------------------------------------------
# Grounding free text onto HPO terms
# --------------------------------------------------------------------------


def _norm_phrase(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_STOP = frozenset(
    "a an the of and or with in on to for is are was were has have had "
    "abnormal abnormality patient patients individual individuals".split()
)


@dataclass
class TermMatch:
    query: str
    hpo_id: str | None
    label: str | None
    score: float
    method: str  # exact | synonym | token


class TermMatcher:
    """Map a phenotype phrase onto an HPO id, offline.

    Deliberately simple: exact name, then exact synonym, then Jaccard over
    content tokens. It is the weakest link in the whole pipeline and it is
    meant to be -- the assignment asks students to measure how much accuracy
    this step costs and to replace it with something better.
    """

    def __init__(self, ontology: Ontology, phenotypes_only: bool = True):
        self.ontology = ontology
        self.exact: dict[str, str] = {}
        self.token_index: dict[str, set[str]] = defaultdict(set)
        self.term_tokens: dict[str, frozenset[str]] = {}

        for hid, label in ontology.name.items():
            if hid in ontology.obsolete:
                continue
            if phenotypes_only and not ontology.is_phenotype(hid):
                continue
            surfaces = [label] + ontology.synonyms.get(hid, [])
            toks: set[str] = set()
            for surface in surfaces:
                norm = _norm_phrase(surface)
                if norm:
                    self.exact.setdefault(norm, hid)
                    toks |= set(norm.split())
            toks -= _STOP
            self.term_tokens[hid] = frozenset(toks)
            for t in toks:
                self.token_index[t].add(hid)

    def match(self, text: str, min_score: float = 0.5) -> TermMatch:
        norm = _norm_phrase(text)
        if not norm:
            return TermMatch(text, None, None, 0.0, "none")
        if norm in self.exact:
            hid = self.exact[norm]
            return TermMatch(text, hid, self.ontology.label(hid), 1.0, "exact")

        qtoks = frozenset(norm.split()) - _STOP
        if not qtoks:
            return TermMatch(text, None, None, 0.0, "none")

        candidates: set[str] = set()
        for t in qtoks:
            candidates |= self.token_index.get(t, set())
        best_id, best = None, 0.0
        for hid in candidates:
            ttoks = self.term_tokens[hid]
            if not ttoks:
                continue
            j = len(qtoks & ttoks) / len(qtoks | ttoks)
            if j > best:
                best_id, best = hid, j
        if best_id is None or best < min_score:
            return TermMatch(text, None, None, best, "none")
        return TermMatch(text, best_id, self.ontology.label(best_id), best, "token")

    def match_many(self, texts: Iterable[str], min_score: float = 0.5) -> list[TermMatch]:
        return [self.match(t, min_score) for t in texts]
