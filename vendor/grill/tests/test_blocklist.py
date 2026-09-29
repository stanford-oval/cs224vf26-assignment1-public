"""Blocklist: classification, field matching, and the three enforcement points
(paperclip text filtering, serper item filtering, fetch-time refusal)."""

from __future__ import annotations

from graph_search.blocklist import Blocklist, _classify, extract_ids
from graph_search.codex_runner import _research_mcp_overrides

STUDY = "Epithelial tumor cells utilize mast cell-derived histamine to regulate perineural invasion"

# A realistic paperclip search block (the format the server filters).
PAPERCLIP_RAW = """Found 2 papers  [s_abc123]

  1. Histamine and TH2 cytokines regulate cysteinyl-leukotriene biosynthesis in mast cells
     Patricia Gehlhaar, Katrin Schaper-Gerhardt, Ralf Gutzmer
     PMC11785601 · PMC · 2025
     https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11785601/

  2. Epithelial tumor cells utilize mast cell-derived histamine to regulate perineural invasion
     A Author, B Author
     PMC9054321 · PMC · 2022
     https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9054321/
     "Tumor cells co-opt mast-cell histamine to drive perineural invasion."

[120ms, saved to s_abc123]

💡 Extract data across these results with: map --from s_abc123 "your question\""""


# ── classification + id extraction ───────────────────────────────────────────
def test_classify_bare_tokens():
    assert _classify("https://pubmed.ncbi.nlm.nih.gov/35536234/") == "url"
    assert _classify("pubmed.ncbi.nlm.nih.gov/35536234") == "url"
    assert _classify("10.1016/j.ccell.2022.01.002") == "doi"
    assert _classify("PMC9054321") == "pmcid"
    assert _classify("35536234") == "pmid"
    assert _classify("Some long paper title about histamine") == "title"


def test_extract_ids():
    ids = extract_ids("see PMC9054321 and https://pubmed.ncbi.nlm.nih.gov/35536234/ doi 10.1016/j.x.2022.01.002")
    assert "pmc9054321" in ids
    assert "pmid:35536234" in ids
    assert "doi:10.1016/j.x.2022.01.002" in ids


# ── field matching ───────────────────────────────────────────────────────────
def test_title_match_is_case_and_punct_insensitive():
    bl = Blocklist.from_lines([f"title: {STUDY}"])
    # exact, plus a noisy real-world rendering of the same title
    assert bl.is_blocked(title=STUDY)
    assert bl.is_blocked(title="EPITHELIAL TUMOR CELLS UTILIZE MAST CELL-DERIVED HISTAMINE TO REGULATE PERINEURAL INVASION.")
    assert bl.match(text=f"  2. {STUDY}\n  PMC9054321") is not None
    # an unrelated paper is not blocked
    assert not bl.is_blocked(title="Organic cation transporter-3 mediates histamine uptake")


def test_url_pmid_pmcid_doi_match():
    bl = Blocklist.from_lines([
        "url: https://pubmed.ncbi.nlm.nih.gov/35536234/",
        "pmcid: PMC9054321",
        "doi: 10.1016/j.ccell.2022.01.002",
    ])
    assert bl.is_blocked(url="https://pubmed.ncbi.nlm.nih.gov/35536234")  # trailing slash differs
    assert bl.is_blocked(ids=["PMC9054321"])
    assert bl.is_blocked(text="available at https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9054321/")
    assert bl.is_blocked(doi="10.1016/j.ccell.2022.01.002")
    assert not bl.is_blocked(title="unrelated", url="https://example.com/other")


def test_bare_pmid_matches_pubmed_link():
    bl = Blocklist.from_lines(["35536234"])  # auto-classified as pmid
    assert bl.is_blocked(url="https://pubmed.ncbi.nlm.nih.gov/35536234/")
    assert not bl.is_blocked(url="https://pubmed.ncbi.nlm.nih.gov/99999999/")


def test_empty_blocklist_is_noop():
    bl = Blocklist()
    assert bl.empty
    assert bl.match(title=STUDY) is None
    assert bl.filter_paperclip(PAPERCLIP_RAW) == (PAPERCLIP_RAW, 0)
    assert bl.filter_serper_items([{"title": STUDY}]) == ([{"title": STUDY}], 0)


def test_short_title_rule_is_ignored():
    # too-short title rules must not match everything
    bl = Blocklist.from_lines(["title: a"])
    assert bl.rules == []


# ── enforcement point 1: paperclip text filtering ────────────────────────────
def test_filter_paperclip_drops_blocked_block_and_renumbers():
    bl = Blocklist.from_lines([f"title: {STUDY}"])
    out, hidden = bl.filter_paperclip(PAPERCLIP_RAW)
    assert hidden == 1
    assert STUDY not in out                       # blocked paper fully hidden
    assert "PMC9054321" not in out
    assert "Histamine and TH2 cytokines" in out   # the other result survives
    assert "Found 2 papers" in out and "saved to s_abc123" in out  # header+footer kept
    assert "[blocklist: 1 result(s) hidden]" in out


def test_filter_paperclip_by_pmcid():
    bl = Blocklist.from_lines(["pmcid: PMC9054321"])
    out, hidden = bl.filter_paperclip(PAPERCLIP_RAW)
    assert hidden == 1 and STUDY not in out


# ── enforcement point 2: serper item filtering ───────────────────────────────
def test_filter_serper_items():
    bl = Blocklist.from_lines([f"title: {STUDY}"])
    items = [
        {"title": "Unrelated mast cell review", "link": "https://x.org/a", "snippet": "..."},
        {"title": STUDY, "link": "https://pubmed.ncbi.nlm.nih.gov/35536234/", "snippet": "..."},
    ]
    kept, hidden = bl.filter_serper_items(items)
    assert hidden == 1
    assert [it["title"] for it in kept] == ["Unrelated mast cell review"]


# ── enforcement point 3: fetch-time refusal ──────────────────────────────────
def test_fetch_meta_match_blocks_even_with_opaque_id():
    # The agent holds an opaque id; the title rule fires off the paper's metadata.
    bl = Blocklist.from_lines([f"title: {STUDY}"])
    meta = f'{{"id": "bio_dca47d15", "title": "{STUDY}", "year": 2022}}'
    assert bl.match(text=meta, ids=extract_ids(meta) | {"bio_dca47d15"}) is not None
    # an unrelated paper's metadata is not blocked
    other = '{"id": "bio_999", "title": "A different paper entirely"}'
    assert bl.match(text=other, ids={"bio_999"}) is None


# ── wiring: per-run blocklist reaches the MCP server args ─────────────────────
def test_research_mcp_overrides_includes_blocklist(tmp_path):
    bl_file = tmp_path / "blocklist.txt"
    bl_file.write_text(f"title: {STUDY}\n", encoding="utf-8")
    overrides = _research_mcp_overrides(tmp_path, budget=2.0, blocklist=bl_file)
    args_line = next(o for o in overrides if o.startswith("mcp_servers.research.args="))
    assert "--blocklist" in args_line and str(bl_file.resolve()) in args_line
    # absent when no blocklist is passed
    plain = _research_mcp_overrides(tmp_path, budget=2.0)
    assert not any("--blocklist" in o for o in plain)
