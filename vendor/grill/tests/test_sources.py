"""Surfaced-works harvest: parse search results, dedupe/rank, exclude the read set."""

from __future__ import annotations

from graph_search import sources

PAPERCLIP = """===== paperclip [abstracts] : HRH1 cancer =====
Found 2 papers  [s_0c7b4250]

  1. Histamine H1 Receptor: A target for pancreatic cancer
     oa_4409201453 · abstracts · 2025
     https://doi.org/10.1016/j.jpet.2025.103573
     "Patients with PDAC have a dismal survival..."

  2. HRH1-ADAM9-Snail axis in oral squamous cell carcinoma
     PMC11926216 · pmc · 2025
     https://pmc.ncbi.nlm.nih.gov/articles/PMC11926216/
     "Cyclic increase..."
"""

WEB = """===== web [scholar] : HRH1 antihistamine =====
Found 2 results  [serper:scholar]

  1. Novel analogs targeting histamine receptor H1 in colorectal cancer
     https://pmc.ncbi.nlm.nih.gov/articles/PMC13174198/
     [year=2026  D Veeragoni - Cancer Drug, 2026 - pmc.ncbi.nlm.nih.gov]

  2. Histamine signaling and antihistamines in cancer progression
     https://www.sciencedirect.com/science/article/pii/S3117702626000071
     ... anti-EMT effects ...
"""


def test_parse_paperclip_and_web():
    pc = sources.parse_hits(PAPERCLIP)
    assert {h["id"] for h in pc} == {"oa_4409201453", "PMC11926216"}
    assert pc[0]["year"] == "2025" and pc[0]["title"].startswith("Histamine H1")
    web = sources.parse_hits(WEB)
    ids = {h["id"] for h in web}
    assert "PMC13174198" in ids                        # id derived from the URL
    assert any(h["year"] == "2026" for h in web)       # year from [year=...]


def test_record_and_surface_rank_and_exclude(tmp_path):
    # surface the same paperclip set twice + web once -> PMC11926216 seen twice
    sources.record_hits(tmp_path, "q1", "paperclip:abstracts", PAPERCLIP)
    sources.record_hits(tmp_path, "q2", "paperclip:abstracts", PAPERCLIP)
    sources.record_hits(tmp_path, "q3", "web:scholar", WEB)

    # exclude one as "already fully read"
    sw = sources.surfaced_works(tmp_path, exclude_ids={"oa_4409201453"})
    ids = [w["id"] for w in sw]
    assert "oa_4409201453" not in ids                  # excluded (read)
    assert ids[0] == "PMC11926216" and sw[0]["seen"] == 2   # most-surfaced first
    assert "PMC13174198" in ids


def test_exclude_by_title(tmp_path):
    sources.record_hits(tmp_path, "q", "paperclip:abstracts", PAPERCLIP)
    sw = sources.surfaced_works(tmp_path, exclude_titles={"HRH1-ADAM9-Snail axis in oral squamous cell carcinoma"})
    assert all("11926216" not in w["id"] for w in sw)  # excluded by normalized title


def test_empty_run(tmp_path):
    assert sources.surfaced_works(tmp_path) == []
