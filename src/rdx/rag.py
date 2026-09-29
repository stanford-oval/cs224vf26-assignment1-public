"""Retrieval-augmented generation, the plain version, as a foil.

Before GRILL and SLIDERS, the simplest thing a student could build: search the
web for the gene, paste the top snippets into a prompt, ask a model to write a
summary with citations. It works well for *what is this gene*. The same
machinery is then pointed at *which of these patients has the disease*, and
the point of the section is watching where it stops helping.

Every function returns the prompt it sent alongside the answer, so the
notebook can show both. Nothing here is cached: a second run costs a second
call, which is itself part of the lesson.

    hits   = web_search("RNU4-2 ReNU syndrome")
    result = summarize_gene("RNU4-2", "ReNU syndrome", hits)
    result.answer, result.prompt, result.hits
"""

from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass, field
from typing import Sequence

from .serper import Hit, search

DEFAULT_MODEL = "gemini-3.8-flash"


@dataclass
class RagResult:
    """One retrieve-then-generate round, with everything that went into it."""

    question: str
    query: str
    hits: list[Hit]
    prompt: str
    answer: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    retrieved: bool = True

    def cited(self) -> list[int]:
        """Which [n] markers the answer actually used."""
        import re  # noqa: PLC0415

        return sorted({int(m) for m in re.findall(r"\[(\d+)\]", self.answer)
                       if 1 <= int(m) <= len(self.hits)})

    def show(self, width: int = 88) -> None:
        print(f"question : {self.question}")
        if self.retrieved:
            print(f"search   : {self.query!r}  ->  {len(self.hits)} results")
            for i, h in enumerate(self.hits, 1):
                mark = "*" if i in self.cited() else " "
                print(f"  {mark}[{i}] {h.title[:70]}")
                print(f"       {h.url[:84]}")
        else:
            print("search   : none (closed book)")
        print(f"model    : {self.model}   {self.input_tokens} in / {self.output_tokens} out")
        print("\nanswer:\n")
        print(textwrap.indent(textwrap.fill(self.answer, width) if "\n" not in self.answer
                              else self.answer, "  "))


# --------------------------------------------------------------------------
# The two halves
# --------------------------------------------------------------------------


def web_search(query: str, n: int = 6, source: str = "search") -> list[Hit]:
    """Plain web search via Serper. ``source="scholar"`` for Google Scholar."""
    return search(query, source=source, limit=n)


def llm(prompt: str, *, model: str = DEFAULT_MODEL, system: str | None = None,
        max_tokens: int = 4000) -> tuple[str, int, int]:
    """One chat completion through the proxy. Returns (text, in_tokens, out_tokens)."""
    from openai import OpenAI  # noqa: PLC0415

    base_url = os.environ.get("OPENAI_BASE_URL")
    key = os.environ.get("OPENAI_API_KEY")
    if not (base_url and key):
        raise RuntimeError("Run the credentials cell first (OPENAI_BASE_URL / OPENAI_API_KEY).")
    client = OpenAI(base_url=base_url, api_key=key)
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}]
    r = client.chat.completions.create(model=model, messages=messages,
                                       max_tokens=max_tokens, temperature=0)
    u = r.usage
    return (r.choices[0].message.content or "").strip(), \
        (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


def snippets_block(hits: Sequence[Hit]) -> str:
    out = []
    for i, h in enumerate(hits, 1):
        out.append(f"[{i}] {h.title}\n    {h.url}\n    {h.snippet}")
    return "\n\n".join(out) if out else "(no search results)"


# --------------------------------------------------------------------------
# What RAG is good at: describing a gene
# --------------------------------------------------------------------------

GENE_SYSTEM = ("You are a careful biomedical writer. Use only the numbered sources "
               "given. Cite each claim as [n]. If the sources do not support a "
               "statement, say that it is not covered rather than filling it in.")

GENE_PROMPT = """\
Sources:

{snippets}

Task: In about 150 words, describe the gene {gene} and its relation to
{disease}. Cover what the gene product is, what it does in the cell, and how
variants in it cause disease. Every sentence needs a citation like [2].
"""


def summarize_gene(gene: str, disease: str, hits: Sequence[Hit] | None = None,
                   *, model: str = DEFAULT_MODEL, n: int = 6) -> RagResult:
    """Search (unless ``hits`` given), then summarise with citations."""
    query = f"{gene} gene {disease}"
    if hits is None:
        hits = web_search(query, n=n)
    prompt = GENE_PROMPT.format(snippets=snippets_block(hits), gene=gene, disease=disease)
    answer, i, o = llm(prompt, model=model, system=GENE_SYSTEM)
    return RagResult(question=f"What is {gene}?", query=query, hits=list(hits),
                     prompt=prompt, answer=answer, model=model,
                     input_tokens=i, output_tokens=o)


def summarize_gene_closed_book(gene: str, disease: str, *,
                               model: str = DEFAULT_MODEL) -> RagResult:
    """The same question with no sources: what the model says from memory."""
    prompt = (f"In about 150 words, describe the gene {gene} and its relation to "
              f"{disease}: what the gene product is, what it does, how variants "
              f"cause disease. Give the year the disease was first described and "
              f"cite the paper.")
    answer, i, o = llm(prompt, model=model)
    return RagResult(question=f"What is {gene}? (no retrieval)", query="", hits=[],
                     prompt=prompt, answer=answer, model=model,
                     input_tokens=i, output_tokens=o, retrieved=False)


# --------------------------------------------------------------------------
# Where RAG stops helping: matching patients
# --------------------------------------------------------------------------

MATCH_SYSTEM = ("You are a clinical geneticist. Use only the numbered sources given. "
                "Cite each claim as [n]. Be explicit about what the sources do not tell you.")

MATCH_PROMPT = """\
Sources:

{snippets}

Below are {k} patients described by Human Phenotype Ontology terms. Exactly
one of them has {disease} ({gene}).

{patients}

Task:
1. For each patient, say whether the sources give you enough to rule them in
   or out, and cite the source.
2. Name the single most likely patient, and give a probability.
3. List the specific facts you would need, and do not have, to be confident:
   for example, how often each finding occurs in affected individuals.
"""


def render_patients_brief(cohort, hpo, patient_ids: Sequence[str] | None = None,
                          max_terms: int = 40) -> str:
    lines = []
    for p in cohort.patients:
        if patient_ids and p.patient_id not in patient_ids:
            continue
        terms = ", ".join(hpo.label(t) for t in p.terms[:max_terms])
        more = f" (+{len(p.terms) - max_terms} more)" if len(p.terms) > max_terms else ""
        lines.append(f"{p.patient_id}: {terms}{more}")
    return "\n".join(lines)


def match_patients(disease: str, gene: str, cohort, hpo, hits: Sequence[Hit],
                   *, patient_ids: Sequence[str] | None = None,
                   model: str = DEFAULT_MODEL) -> RagResult:
    """Point the same snippets at the diagnostic question."""
    patients = render_patients_brief(cohort, hpo, patient_ids)
    k = len(patient_ids) if patient_ids else len(cohort)
    prompt = MATCH_PROMPT.format(snippets=snippets_block(hits), k=k,
                                 disease=disease, gene=gene, patients=patients)
    answer, i, o = llm(prompt, model=model, system=MATCH_SYSTEM, max_tokens=6000)
    return RagResult(question=f"Which patient has {disease}?", query="(reused)",
                     hits=list(hits), prompt=prompt, answer=answer, model=model,
                     input_tokens=i, output_tokens=o)


# --------------------------------------------------------------------------
# A first look at the patients
# --------------------------------------------------------------------------


def patients_preview(cohort, hpo, n_patients: int = 4, n_terms: int = 6) -> None:
    """A few rows: id, age, sex, the first findings with their labels."""
    for p in cohort.patients[:n_patients]:
        head = f"{p.patient_id}  age {p.age_years}  {p.sex or '?'}   " \
               f"{len(p.terms)} findings, {len(p.excluded)} recorded absent"
        print(head)
        for t in p.terms[:n_terms]:
            print(f"      {t}  {hpo.label(t)}")
        if len(p.terms) > n_terms:
            print(f"      ... {len(p.terms) - n_terms} more")
        print()
