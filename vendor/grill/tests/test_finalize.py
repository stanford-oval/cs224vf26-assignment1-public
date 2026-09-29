"""Finalize step: notes are injected into the prompt; answer.md is captured."""

from __future__ import annotations

import json
import sqlite3

from graph_search import db, finalize


class _Result:
    def __init__(self, cwd, code=0):
        self.returncode = code
        self.transcript_path = cwd / "t.log"


def test_finalize_reads_notes_and_writes_answer(tmp_path):
    db_path = tmp_path / "notes.sqlite"
    with db.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO notes (doc_name, source, note, tags) VALUES (?,?,?,?)",
            ("Paper A", "paperclip", "PARP1 SL with SMC3 loss (L40-L50).", json.dumps(["parp"])),
        )
        conn.commit()

    captured = {}

    def fake_codex(inv):
        # The recorded note must be injected into the finalize prompt.
        assert "PARP1 SL with SMC3 loss" in inv.prompt
        assert "Paper A" in inv.prompt
        captured["prompt"] = inv.prompt
        (inv.cwd / "answer.md").write_text("# Answer\nPARP1 (see Paper A, L40-L50).\n")
        return _Result(inv.cwd)

    text = finalize.finalize("which genes are SL with SMC3?", db_path,
                             cwd=tmp_path / "fin", run_codex_fn=fake_codex)
    assert text is not None and "PARP1" in text
    # Saved next to the DB.
    assert (tmp_path / "notes.answer.md").read_text() == text


def test_doc_url_builds_links_from_identifiers():
    assert finalize._doc_url("PMC7033043") == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7033043/"
    assert finalize._doc_url("PMID:34822775") == "https://pubmed.ncbi.nlm.nih.gov/34822775/"
    assert finalize._doc_url("oa_4405553299") == "https://openalex.org/W4405553299"
    assert finalize._doc_url("2791196982") == "https://openalex.org/W2791196982"
    assert finalize._doc_url("10.1038/s41586-020-2649-2") == "https://doi.org/10.1038/s41586-020-2649-2"
    assert finalize._doc_url("https://example.com/x") == "https://example.com/x"
    assert finalize._doc_url("not-an-id") == ""
    assert finalize._doc_url(None) == ""


def test_format_sources_dedupes_numbers_and_links():
    from graph_search.models import Note
    notes = [
        Note(doc_name="Paper A", authors="Zhao et al.", doc_time="2019", url="PMC7033043", note="x (L1)"),
        Note(doc_name="Paper A", authors="Zhao et al.", doc_time="2019", url="PMC7033043", note="y (L2)"),
        Note(doc_name="Paper B", authors="Li et al.", doc_time="2022", url="PMID:34822775", note="z (L3)"),
    ]
    src = finalize._format_sources(notes)
    lines = src.splitlines()
    assert len(lines) == 2  # Paper A deduped
    assert lines[0].startswith("- [1] Zhao et al. · 2019. Paper A")
    assert "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7033043/" in lines[0]
    assert lines[1].startswith("- [2] Li et al. · 2022. Paper B")
    # The numbered Sources list is injected into the rendered prompt.
    assert "{sources}" not in finalize.render_prompt("q?", notes)
