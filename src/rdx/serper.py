"""Serper-backed retrieval for GRILL.

GRILL's EXPLORE, SCREEN and DEEP executors run with codex's own ``web_search``
tool, and optionally with a block of pre-retrieved literature injected into the
prompt. That injection is ``src/search.py``, which talks to paperclip. This
module is a drop-in alternative that talks to `Serper <https://serper.dev>`_,
so retrieval is a plain HTTP call the harness makes rather than a tool the
model has to decide to use.

Why that distinction is worth having. If the model never invokes ``web_search``
-- and some models do not, reliably -- the run is left arguing from parametric
memory, and the provenance gate then strips the support from every claim it
makes. Retrieving in the harness removes the model's discretion from the step
that decides whether there is any evidence at all.

Needs ``SERPER_API_KEY``. Without it every function here returns empty and
GRILL falls back to ``web_search`` alone, which is a supported mode rather
than a broken one.

    from rdx import serper
    block, papers = serper.source_context(["scholar"], "RNU4-2 phenotype frequency")
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Iterable, Sequence

SERPER_URL = "https://google.serper.dev"

#: Which Serper endpoint each source name maps to. ``scholar`` is the one that
#: matters for this assignment; plain ``search`` pulls in a lot of patient-group
#: and news pages that read as authoritative and are not citable.
ENDPOINTS = {"scholar": "scholar", "search": "search", "news": "news"}

_PMID = re.compile(r"/pubmed/(\d+)|[?&]pmid=(\d+)|\bPMID:?\s*(\d+)", re.I)
_PMC = re.compile(r"(PMC\d{6,})", re.I)
_DOI = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.I)


def available() -> bool:
    return bool(os.environ.get("SERPER_API_KEY"))


@dataclass
class Hit:
    """One search result, with any locator we could recover from it."""

    title: str
    url: str
    snippet: str = ""
    year: int | None = None
    source: str = "scholar"
    doi: str | None = None
    pmid: str | None = None
    pmc: str | None = None
    authors: str = ""
    cited_by: int | None = None

    @property
    def id(self) -> str:
        """A stable identity: the best locator, else the URL."""
        return self.pmid or self.doi or self.pmc or self.url

    def resolvable(self) -> bool:
        """Would GRILL's provenance gate accept a SourceRef built from this?"""
        return bool(self.doi or self.pmid or self.pmc or self.url)

    def as_source_ref(self) -> dict:
        """The shape GRILL's schemas expect inside an evidence item."""
        return {
            "title": self.title,
            "authors": [a.strip() for a in self.authors.split(",") if a.strip()][:8],
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "pmc": self.pmc,
            "url": self.url,
        }


def _locators(*texts: str) -> tuple[str | None, str | None, str | None]:
    blob = " ".join(t for t in texts if t)
    doi = m.group(1) if (m := _DOI.search(blob)) else None
    pmc = m.group(1).upper() if (m := _PMC.search(blob)) else None
    pmid = None
    if m := _PMID.search(blob):
        pmid = next((g for g in m.groups() if g), None)
    return doi, pmid, pmc


def search(
    query: str,
    source: str = "scholar",
    limit: int = 8,
    *,
    timeout: int = 30,
) -> list[Hit]:
    """One Serper query. Returns ``[]`` on any failure, never raises.

    Failing soft is deliberate: a retrieval outage should degrade a run to
    ``web_search`` only, not abort it halfway through a paid budget.
    """
    key = os.environ.get("SERPER_API_KEY")
    if not key:
        return []

    endpoint = ENDPOINTS.get(source, "search")
    body = json.dumps({"q": query, "num": max(1, min(limit, 20))}).encode()
    req = urllib.request.Request(
        f"{SERPER_URL}/{endpoint}",
        data=body,
        method="POST",
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as fh:
            data = json.loads(fh.read())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return []

    rows = data.get("organic") or data.get("news") or []
    hits: list[Hit] = []
    for r in rows[:limit]:
        url = r.get("link") or ""
        title = (r.get("title") or "").strip()
        snippet = (r.get("snippet") or "").strip()
        doi, pmid, pmc = _locators(url, snippet, r.get("publicationInfo", ""))
        year = r.get("year")
        if year is None and (pi := r.get("publicationInfo")):
            year = int(m.group(0)) if (m := re.search(r"\b(19|20)\d{2}\b", pi)) else None
        hits.append(
            Hit(
                title=title,
                url=url,
                snippet=snippet,
                year=int(year) if year else None,
                source=source,
                doi=doi,
                pmid=pmid,
                pmc=pmc,
                authors=(r.get("publicationInfo") or "").split("-")[0].strip(),
                cited_by=(r.get("citedBy") or {}).get("total")
                if isinstance(r.get("citedBy"), dict)
                else r.get("citedBy"),
            )
        )
    return hits


def source_context(
    sources: Sequence[str] = ("scholar",),
    query: str = "",
    per_source: int = 6,
    cap: int = 12,
    *,
    resolvable_only: bool = True,
) -> tuple[str, list[Hit]]:
    """Retrieve, de-duplicate, and format a prompt block.

    Signature-compatible with ``src/search.py``'s ``source_context`` so it can
    be swapped in, but it returns ``Hit`` objects rather than dicts.

    A known gap: DOIs are recovered only when they appear in the URL or the
    snippet. A ScienceDirect PII link carries none, so a paper that is in fact
    gold comes back identified by URL alone. GRILL's gate accepts a URL, so the
    evidence still passes -- but a URL is a weaker locator than a DOI, and
    matching retrieved results against a gold PMID set will under-count. Worth
    measuring before trusting a recall number.

    ``resolvable_only`` drops results carrying no locator at all. A result the
    provenance gate would reject anyway is worse than nothing in the prompt:
    the model cites it, the evidence is stripped at ingest, and the claim is
    left looking unsupported for a reason nobody can see from the ledger.
    """
    if not sources or not query:
        return "", []

    hits: list[Hit] = []
    seen: set[str] = set()
    for s in sources:
        for h in search(query, s, per_source):
            if resolvable_only and not h.resolvable():
                continue
            if h.id in seen:
                continue
            seen.add(h.id)
            hits.append(h)

    hits = hits[:cap]
    if not hits:
        return "", []

    lines = []
    for h in hits:
        loc = h.pmid and f"PMID:{h.pmid}" or h.doi or h.pmc or h.url
        year = f", {h.year}" if h.year else ""
        snip = f" — {h.snippet[:200]}" if h.snippet else ""
        lines.append(f"- [{h.source}] {h.title} ({loc}{year}){snip}")

    block = (
        "RETRIEVED LITERATURE (via Serper — prefer these and CITE them by "
        "PMID/DOI/URL in your evidence; you may also web_search for more):\n"
        + "\n".join(lines)
    )
    return block, hits


def install_into_grill(sources: Sequence[str] = ("scholar",)):
    """Make GRILL's executors retrieve through Serper. Returns an undo.

    GRILL injects literature by calling ``search.source_context(ledger.sources,
    ...)`` inside EXPLORE. Replacing that one function redirects retrieval
    without touching the orchestrator, and the executors keep receiving exactly
    the prompt block shape they already expect.

    Two conditions, and both bite:

    * ``Config.sources`` must be non-empty, or EXPLORE never calls this at all.
    * It patches **this process**. ``run_grill`` shells out to a subprocess, so
      the patch does not reach it. Use it with an in-process ``Orchestrator``;
      for a subprocess run, set ``PAPERCLIP_API_KEY`` and use GRILL's own
      backend, or edit ``vendor/grill/src/search.py``.
    """
    from . import grill as G  # noqa: PLC0415

    G.add_grill_to_path()
    import src.search as grill_search  # noqa: PLC0415

    original = grill_search.source_context

    def patched(srcs, query, per_source=4, cap=12):
        block, hits = source_context(
            srcs or list(sources), query, per_source=per_source, cap=cap
        )
        # GRILL expects dicts; give it the fields its formatter reads.
        papers = [
            {
                "id": h.id,
                "title": h.title,
                "authors": h.authors,
                "source": h.source,
                "date": str(h.year or ""),
                "url": h.url,
                "snippet": h.snippet,
            }
            for h in hits
        ]
        return block, papers

    grill_search.source_context = patched

    def undo() -> None:
        grill_search.source_context = original

    return undo


def selftest() -> dict:
    """Parsing and formatting, exercised offline on a canned payload."""
    rows = [
        {
            "title": "De novo variants in the RNU4-2 snRNA cause a frequent NDD",
            "link": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11338827/",
            "snippet": "doi:10.1038/s41586-024-07773-7 ... 42 of 48 had hypotonia.",
            "publicationInfo": "Y Chen, et al - Nature, 2024",
        },
        {"title": "A page with no locator", "link": "", "snippet": "nothing here"},
    ]
    hits = []
    for r in rows:
        doi, pmid, pmc = _locators(r["link"], r["snippet"], r.get("publicationInfo", ""))
        hits.append(Hit(title=r["title"], url=r["link"], snippet=r["snippet"],
                        doi=doi, pmid=pmid, pmc=pmc))
    return {
        "doi_found": hits[0].doi,
        "pmc_found": hits[0].pmc,
        "first_resolvable": hits[0].resolvable(),
        "second_resolvable": hits[1].resolvable(),
        "key_present": available(),
    }
