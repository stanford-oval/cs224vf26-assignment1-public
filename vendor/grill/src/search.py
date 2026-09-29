"""Source-aware paperclip literature search for the agent's explore/verify steps.

When a run is launched with `sources` (arxiv / pmc / biorxiv / trials / …), the harness retrieves real,
cited papers from those corpora and injects them into the executor prompt, so codex reasons over
structured literature in ADDITION to its native web_search. Requires the paperclip SDK (~/.paperclip/lib)
and PAPERCLIP_API_KEY in the environment; degrades to empty (web_search only) on any failure.
"""
from __future__ import annotations

import os
import re
import sys

_PID = re.compile(r"^(\S+)\s+·\s+(\S+)\s+·\s+(\S+)")


def _client():
    lib = os.path.expanduser("~/.paperclip/lib")
    if lib not in sys.path:
        sys.path.insert(0, lib)
    from gxl_paperclip import PaperclipClient
    return PaperclipClient.from_env()


def paperclip_search(query: str, source: str, limit: int = 4) -> list[dict]:
    """Search one paperclip source. Returns a list of {id,title,authors,source,date,url,snippet}."""
    try:
        res = _client().search(query, source=source, limit=limit)
    except Exception:
        return []
    text = getattr(res, "output", "") or ""
    out: list[dict] = []
    for b in re.split(r"\n\s*\d+\.\s", "\n" + text)[1:]:
        lines = [ln.strip() for ln in b.strip().splitlines() if ln.strip()]
        if not lines:
            continue
        title = lines[0]
        authors = lines[1] if len(lines) > 1 else ""
        pid = src = date = url = snippet = ""
        for ln in lines[2:]:
            m = _PID.match(ln)
            if m and not pid:
                pid, src, date = m.group(1), m.group(2), m.group(3)
                continue
            if ln.startswith("http") and not url:
                url = ln
                continue
            if ln.startswith('"'):
                snippet = ln.strip('"')
        if pid:
            out.append({"id": pid, "title": title, "authors": authors, "source": src,
                        "date": date, "url": url, "snippet": snippet})
    return out


def source_context(sources: list[str], query: str, per_source: int = 4, cap: int = 12) -> tuple[str, list[dict]]:
    """Search every source for `query`, de-dupe by id, and format a prompt block + the paper list.
    Returns ("", []) when there are no sources or nothing is found."""
    if not sources:
        return "", []
    papers: list[dict] = []
    seen: set[str] = set()
    for s in sources:
        for p in paperclip_search(query, s, per_source):
            if p["id"] not in seen:
                seen.add(p["id"])
                papers.append(p)
    papers = papers[:cap]
    if not papers:
        return "", []
    lines = [f"- [{p['source']}] {p['title']} ({p['id']}"
             + (f", {p['date']}" if p['date'] else "") + ")"
             + (f" — {p['snippet'][:220]}" if p['snippet'] else "") for p in papers]
    block = ("RETRIEVED LITERATURE (from " + ", ".join(sources) + " via paperclip — prefer these and "
             "CITE them by id/url in your evidence; you may also web_search for more):\n" + "\n".join(lines))
    return block, papers
