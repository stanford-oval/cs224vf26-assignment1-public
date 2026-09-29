"""Test the research session: harness snapshots the DB + attaches the research
MCP server; agent stores findings via the notes SQL tool."""

from __future__ import annotations

import json
import sqlite3

from graph_search import agent, db


class _Result:
    def __init__(self, cwd, code=0):
        self.returncode = code
        self.transcript_path = cwd / "t.log"


def _fake_session(inv):
    # The harness snapshots the notes DB into the run dir and attaches the
    # research MCP server (scoped to this budget) — no scripts are dropped.
    assert (inv.cwd / "notes.sqlite").is_file()
    assert inv.research_budget == 2.0  # MCP search/read budget enforced
    assert "SMC3" in inv.prompt  # the question reached the session
    assert "{db_stats}" not in inv.prompt  # the DB-stats placeholder was filled

    # Simulate the agent storing findings via the notes SQL tool.
    conn = sqlite3.connect(inv.cwd / "notes.sqlite")
    conn.execute(
        "INSERT INTO notes (doc_name, source, note, tags) VALUES (?,?,?,?)",
        ("Paper A", "paperclip", "PARP1 SL with cohesin loss.", json.dumps(["parp", "human"])),
    )
    conn.execute(
        "INSERT INTO notes (doc_name, note, tags) VALUES (?,?,?)",
        ("Paper B", "WNT stimulation SL.", json.dumps(["wnt"])),
    )
    conn.commit()
    conn.close()
    return _Result(inv.cwd)


def test_run_session(tmp_path):
    db_path = tmp_path / "notes.sqlite"
    total = agent.run_session(
        "which genes are synthetically lethal with SMC3?",
        db_path,
        cwd=tmp_path / "s1",
        budget=2.0,
        run_codex_fn=_fake_session,
    )
    assert total == 2  # the session's SQL writes were copied back to the canonical DB

    with db.connect(db_path) as conn:
        assert db.doc_names(conn) == {"Paper A", "Paper B"}
        assert db.summarize_by_tag(conn)["parp"]  # tag clustering works
