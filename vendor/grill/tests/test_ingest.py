"""Generic off-corpus ingestion: extract text from URL/file/PDF/HTML, then route it
through the read-size guardrail (full text in .fulltext/, capped excerpt in papers/)."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_search import ingest, mcp_server, sliders_digest


def test_sniff_and_extract_html_strips_scripts():
    html = b"<html><head><style>x{}</style></head><body><h1>T</h1><p>Hello.</p><script>bad()</script></body></html>"
    text, kind = ingest.extract_text(html, "text/html", "x.html")
    assert kind == "html"
    assert "Hello." in text and "bad()" not in text and "x{}" not in text
    assert text.startswith("L1: ")            # Lxx-numbered for citations


def test_extract_text_plain_and_pdf_sniff():
    text, kind = ingest.extract_text(b"line a\nline b", "text/plain", "n.txt")
    assert kind == "text" and "L2: line b" in text
    # PDF detected by magic bytes even without a content-type
    assert ingest._sniff(b"%PDF-1.7 ...", "", "thing") == "pdf"


def test_source_id_stable_and_safe():
    a = ingest.source_id("https://radar.brookes.ac.uk/items/abc.pdf")
    b = ingest.source_id("https://radar.brookes.ac.uk/items/abc.pdf")
    assert a == b and a.startswith("ext_") and "/" not in a


def test_load_local_file(tmp_path):
    f = tmp_path / "note.txt"
    f.write_text("alpha\nbeta\ngamma")
    text, kind, n = ingest.load_source(str(f))
    assert kind == "text" and "L3: gamma" in text and n > 0


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        ingest.load_source(str(tmp_path / "nope.txt"))


def test_ingested_source_flows_through_guardrail(tmp_path, monkeypatch):
    # a large off-corpus text, ingested, must be capped in papers/ but full in .fulltext/
    monkeypatch.setattr(mcp_server, "RUN_DIR", tmp_path)
    monkeypatch.setattr(mcp_server, "SHELL_READ_CAP_CHARS", 4000)
    monkeypatch.setattr(mcp_server, "FULLTEXT_GUARD", True)
    big = "\n".join(f"finding {i} about HRH1" for i in range(2000))   # ~40k chars
    text, _ = ingest.extract_text(big.encode(), "text/plain", "thesis.txt")
    sid = ingest.source_id("https://repo.example/thesis.pdf")
    rel, n_lines, capped, full = mcp_server._save_fetched(sid, text)
    assert capped is True
    assert "TRUNCATED" in (tmp_path / "papers" / f"{sid}.txt").read_text()
    assert (tmp_path / ".fulltext" / f"{sid}.txt").read_text() == text   # full text preserved
    # digest sees the full ingested text (union of papers/ + .fulltext/)
    mds = sliders_digest.convert_papers_to_md(tmp_path)
    assert any(Path(m).stem == sid for m in mds)
    assert "TRUNCATED" not in (tmp_path / "papers_md" / f"{sid}.md").read_text()
