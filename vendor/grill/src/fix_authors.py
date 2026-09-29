#!/usr/bin/env python3
"""Replace 'Unknown' authors in a staged v2 report's Sources list with real authors
fetched from OpenAlex (by DOI, else a confident title-search match). Author-less web
resources (product pages, registries, code pages) have their 'Unknown' dropped rather
than fabricated.

    python3 -m methodology_v2.fix_authors <report.md> [--apply] [--ledger ledger.json]
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "research@stanford.edu"
# non-article domains: product/marketing pages, registries, code lists — no real authors,
# so never title-search-match them to a paper (that would fabricate attribution).
NON_ARTICLE_HOSTS = {"avantect.com", "www.avantect.com", "esmo.org", "www.esmo.org",
                     "clinicaltrials.gov", "www.clinicaltrials.gov", "aapc.com", "www.aapc.com"}
DOI_RE = re.compile(r"10\.\d{4,9}/\S+")
URL_RE = re.compile(r"https?://\S+")
UNKNOWN_LINE = re.compile(r"^(\d+)\.\s+Unknown\s+\(([^)]*)\)\.\s+(.*)$")


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": f"mailto:{MAILTO}"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def authors_str(authorships: list) -> str:
    names = [a.get("author", {}).get("display_name", "") for a in (authorships or []) if a.get("author")]
    names = [n for n in names if n]
    if not names:
        return ""
    return names[0] + (" et al." if len(names) > 1 else "")


def by_doi(doi: str) -> str:
    doi = doi.rstrip(").,;").replace("https://doi.org/", "")
    try:
        d = _get(f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}?select=authorships,title&mailto={MAILTO}")
        return authors_str(d.get("authorships"))
    except Exception:
        return ""


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def by_title(title: str) -> str:
    """Confident title-search: accept only if the top hit's title closely matches."""
    t = title.strip().rstrip(".")
    if len(t) < 25:
        return ""
    try:
        d = _get(f"https://api.openalex.org/works?filter=title.search:{urllib.parse.quote(t)}&per-page=1&select=authorships,title&mailto={MAILTO}")
        res = d.get("results") or []
        if not res:
            return ""
        got = _norm(res[0].get("title", ""))
        want = _norm(t)
        # require strong overlap (one contains the other, or >=85% token overlap)
        a, b = set(got.split()), set(want.split())
        if not a or not b:
            return ""
        jac = len(a & b) / len(a | b)
        if got in want or want in got or jac >= 0.7:
            return authors_str(res[0].get("authorships"))
    except Exception:
        return ""
    return ""


def title_of(rest: str) -> str:
    # rest = "TITLE. JOURNAL LOC" — title is up to the first '. ' that precedes journal/url
    # take everything before a double-space (journal sep) or ' http' or the DOI
    cut = rest
    for sep in ["  ", " http", " 10."]:
        i = cut.find(sep)
        if i > 0:
            cut = cut[:i]
    return cut.rstrip(". ").strip()


def main() -> int:
    path = sys.argv[1]
    apply = "--apply" in sys.argv
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    fixes = {}  # locator -> author (for ledger)
    out = []
    n_fix = n_drop = 0
    for ln in lines:
        m = UNKNOWN_LINE.match(ln)
        if not m:
            out.append(ln)
            continue
        num, year, rest = m.group(1), m.group(2), m.group(3)
        doi = DOI_RE.search(ln)
        url = URL_RE.search(ln)
        title = title_of(rest)
        author = ""
        host = (urllib.parse.urlparse(url.group(0)).netloc.lower() if url else "")
        if doi:
            author = by_doi(doi.group(0))
            time.sleep(0.3)
        if not author and host not in NON_ARTICLE_HOSTS:   # don't fabricate authors for product/registry pages
            author = by_title(title)
            time.sleep(0.3)
        loc = (doi.group(0) if doi else (url.group(0) if url else "")).rstrip(").,;")
        if author:
            out.append(f"{num}. {author} ({year}). {rest}")
            fixes[loc] = author
            n_fix += 1
            print(f"  [{num}] FETCHED  {author:<28} | {title[:60]}")
        else:
            # author-less web resource → drop the 'Unknown' token
            out.append(f"{num}. ({year}). {rest}")
            n_drop += 1
            print(f"  [{num}] no-author (web) → dropped Unknown | {title[:55]}")
    print(f"\n{n_fix} authors fetched, {n_drop} dropped (author-less).")

    if apply:
        open(path, "w", encoding="utf-8").write("\n".join(out) + ("\n" if text.endswith("\n") else ""))
        print(f"patched {path}")
        lj = None
        for i, a in enumerate(sys.argv):
            if a == "--ledger" and i + 1 < len(sys.argv):
                lj = sys.argv[i + 1]
        if lj:
            L = json.load(open(lj, encoding="utf-8"))
            patched = 0
            for c in L.get("claims", {}).values():
                for s in c.get("evidence", []):
                    if s.get("authors"):
                        continue
                    key = s.get("doi") or s.get("url") or ""
                    key = (key or "").rstrip(").,;")
                    if key in fixes:
                        s["authors"] = [fixes[key].replace(" et al.", "")]
                        patched += 1
            json.dump(L, open(lj, "w", encoding="utf-8"), indent=2)
            print(f"patched {patched} SourceRefs in {lj}")
    else:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
