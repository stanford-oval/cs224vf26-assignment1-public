"""Reference enrichment via clibib (https://github.com/delip/clibib).

Codex evidence often carries only a locator (DOI/arXiv/PMID/URL) and a title, so the bibliography ends up
with 'Unknown' authors and 'n.d.' years. clibib fetches the full BibTeX for a locator (CrossRef / arXiv /
PubMed / Zotero); we parse it and fill in the MISSING fields on each SourceRef. Best-effort: any failure or
timeout leaves the existing data untouched. Runs only when clibib is installed.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Resolve clibib even when the venv's bin isn't on PATH (the daemon spawns runs without it) — it lives
# next to the interpreter that's running us.
_CLIBIB = shutil.which("clibib") or (
    str(Path(sys.executable).parent / "clibib") if (Path(sys.executable).parent / "clibib").exists() else None)
_FIELD = re.compile(r'^\s*(\w+)\s*=\s*[{"]?(.*?)[}"]?,?\s*$')


def available() -> bool:
    return bool(_CLIBIB)


def _run_clibib(query: str, timeout: int = 25) -> str:
    if not _CLIBIB or not query:
        return ""
    try:
        r = subprocess.run([_CLIBIB, "--first", query], capture_output=True, text=True, timeout=timeout)
        return r.stdout or ""
    except Exception:
        return ""


def _parse_bibtex(bib: str) -> dict:
    out: dict = {}
    for line in bib.splitlines():
        m = _FIELD.match(line)
        if m and m.group(1).lower() not in ("abstract",):
            out[m.group(1).lower()] = re.sub(r"[{}]", "", m.group(2)).strip().rstrip(",").strip()
    return out


def _authors(author_field: str) -> list[str]:
    names = []
    for a in (author_field or "").split(" and "):
        a = a.strip()
        if not a:
            continue
        names.append(f"{a.split(',',1)[1].strip()} {a.split(',',1)[0].strip()}".strip() if "," in a else a)
    return [n for n in names if n]


def _query_for(sr) -> str:
    """Best locator to hand clibib: DOI > arXiv id > PMID > URL > title."""
    if getattr(sr, "doi", None):
        return str(sr.doi)
    url = getattr(sr, "url", "") or ""
    m = re.search(r"arxiv\.org/abs/([\w.]+)", url) or re.match(r"arx_([\w.]+)", str(getattr(sr, "url", "") or ""))
    if m:
        return m.group(1)
    if getattr(sr, "pmid", None):
        return str(sr.pmid)
    return url or (getattr(sr, "title", "") or "")


def enrich(sr) -> bool:
    """Fill missing author/year/journal/title on one SourceRef. Returns True if anything changed."""
    if getattr(sr, "authors", None) and getattr(sr, "year", None) and getattr(sr, "journal", None):
        return False   # already complete — don't spend a network call
    f = _parse_bibtex(_run_clibib(_query_for(sr)))
    if not f:
        return False
    changed = False
    if not sr.authors and f.get("author"):
        sr.authors = _authors(f["author"]); changed = True
    if not sr.year and f.get("year"):
        try:
            sr.year = int(re.sub(r"\D", "", f["year"])[:4]); changed = True
        except Exception:
            pass
    venue = f.get("journal") or f.get("booktitle") or f.get("publisher")
    if not sr.journal and venue:
        sr.journal = venue; changed = True
    if (not sr.title or len(sr.title) < 6) and f.get("title"):
        sr.title = f["title"]; changed = True
    return changed


def enrich_all(refs, concurrency: int = 8, cap: int = 200) -> int:
    """Concurrently enrich a list of SourceRefs (in place). Returns the number changed."""
    if not _CLIBIB:
        return 0
    todo = list(refs)[:cap]
    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for changed in ex.map(lambda s: enrich(s) if s else False, todo):
            n += 1 if changed else 0
    return n


# ── Final hygiene pass on the generated report ──────────────────────────────
# Enrichment fixes the bibliography, but the report writer sometimes copies a
# placeholder into the prose — "(Unknown, n.d.)", "Unknown et al. (2019)". Those read
# as citations we failed to resolve, so they are stripped from the body before the
# report is saved. Deliberately narrow: only citation-SHAPED text is touched, never
# ordinary prose like "the mechanism is unknown".

_UNK = r"Unknown(?:\s+et\s+al\.?)?\s*,?\s*(?:n\.?d\.?|\d{4})?"
# whole citation is the placeholder: "(Unknown, n.d.)" / "(Unknown et al., 2019)"
_PAREN_UNKNOWN = re.compile(rf"\s*\(\s*{_UNK}\s*\)")
# one entry inside a multi-source group — leading "…; Unknown, n.d.;" or trailing "; Unknown, 2018)"
_GROUP_MID = re.compile(rf"\s*{_UNK}\s*;\s*")
_GROUP_TAIL = re.compile(rf"\s*;\s*{_UNK}\s*(?=\))")
# narrative form: "Unknown et al. (n.d.) reported …" — capitalise the word left behind, and only
# that word (a blanket re-capitalisation would corrupt lower-case notation like c.643T>C).
_NARRATIVE_UNKNOWN = re.compile(r"\bUnknown\s+et\s+al\.?\s*\(\s*(?:n\.?d\.?|\d{4})\s*\)\s*(\w)")


def scrub_unknown_citations(text: str) -> tuple[str, int]:
    """Remove placeholder citations from report prose. Returns (cleaned_text, n_removed)."""
    if not text or "Unknown" not in text:
        return text, 0
    n = 0
    for pat, repl in ((_GROUP_MID, "  "), (_GROUP_TAIL, ""), (_PAREN_UNKNOWN, "")):
        text, k = pat.subn(repl, text)
        n += k
    text, k = _NARRATIVE_UNKNOWN.subn(lambda m: m.group(1).upper(), text)
    n += k
    if n:
        text = re.sub(r"\(\s*;?\s*", "(", text)       # "( Smith" / "(; Smith" → "(Smith"
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\s+([.,;])", r"\1", text)     # space left before punctuation
        text = re.sub(r"\(\s*\)", "", text)           # an emptied citation group
    return text, n


def count_unknowns(text: str) -> int:
    """How many placeholder-looking 'Unknown' tokens remain — used as a finalize assertion."""
    return len(re.findall(r"\bUnknown\b(?=\s*[(,]|\s+et\s+al\.)", text or ""))
