"""Read-size guardrail: fetched papers over the cap expose only a capped excerpt to
the agent (papers/), while the full text is kept in .fulltext/ for digest + read."""

from __future__ import annotations

from pathlib import Path

import pytest

from graph_search import mcp_server, sliders_digest


@pytest.fixture
def run_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(mcp_server, "RUN_DIR", tmp_path)
    monkeypatch.setattr(mcp_server, "SHELL_READ_CAP_CHARS", 4000)
    monkeypatch.setattr(mcp_server, "FULLTEXT_GUARD", True)
    return tmp_path


def test_large_paper_is_capped_in_papers_full_in_fulltext(run_dir):
    big = "\n".join(f"L{i}: histamine receptor finding line {i}" for i in range(2000))  # ~70k chars
    rel, n_lines, capped, full_chars = mcp_server._save_fetched("PMC999", big)

    assert capped is True
    assert full_chars == len(big)

    papers_txt = (run_dir / "papers" / "PMC999.txt").read_text()
    assert len(papers_txt) < 5000                       # capped (~4000 + footer)
    assert "TRUNCATED" in papers_txt
    assert "read(doc_id, question)" in papers_txt and "digest(question)" in papers_txt

    full_txt = (run_dir / ".fulltext" / "PMC999.txt").read_text()
    assert full_txt == big                              # full text preserved for digest

    # the read sub-agent / digest source resolves to the FULL text, not the excerpt
    assert mcp_server._fulltext_path("PMC999") == run_dir / ".fulltext" / "PMC999.txt"


def test_small_paper_under_cap_is_not_capped(run_dir):
    small = "L1: short note\nL2: another line\n"
    rel, n_lines, capped, full_chars = mcp_server._save_fetched("PMC1", small)
    assert capped is False
    assert (run_dir / "papers" / "PMC1.txt").read_text() == small
    assert not (run_dir / ".fulltext" / "PMC1.txt").exists()   # no fulltext copy needed
    assert mcp_server._fulltext_path("PMC1") == run_dir / "papers" / "PMC1.txt"


def test_guard_off_writes_full_to_papers(run_dir, monkeypatch):
    monkeypatch.setattr(mcp_server, "FULLTEXT_GUARD", False)
    big = "x\n" * 5000
    _, _, capped, _ = mcp_server._save_fetched("PMC2", big)
    assert capped is False
    assert (run_dir / "papers" / "PMC2.txt").read_text() == big
    assert not (run_dir / ".fulltext").exists()


def test_digest_reads_fulltext_not_the_excerpt(run_dir):
    # one big paper (capped -> .fulltext) + one small (papers/ only): digest must see BOTH
    # in full and never the truncated excerpt.
    big = "\n".join(f"L{i}: full body sentence {i}" for i in range(2000))
    mcp_server._save_fetched("PMCBIG", big)
    mcp_server._save_fetched("PMCSMALL", "L1: tiny paper body\n")

    mds = sliders_digest.convert_papers_to_md(run_dir)
    stems = {Path(m).stem for m in mds}
    assert stems == {"PMCBIG", "PMCSMALL"}              # union of both sources

    big_md = (run_dir / "papers_md" / "PMCBIG.md").read_text()
    assert "TRUNCATED" not in big_md                    # got full text, not the excerpt
    assert "full body sentence 1999" in big_md          # the tail the agent never saw
