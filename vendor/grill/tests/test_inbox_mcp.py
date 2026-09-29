"""The inbox MCP surface: ask_user (non-blocking), check_inbox (drain), the
footer flag, and request_stop's soft-block + never-trap guarantee."""

from __future__ import annotations

import graph_search.mcp_server as srv
from graph_search import db
from graph_search import interaction as ix


def _fn(tool):
    return tool.fn if hasattr(tool, "fn") else tool


def _setup(tmp_path, budget=50.0, spent=1.0):
    srv.RUN_DIR = tmp_path
    srv.NOTES_DB = tmp_path / "notes.sqlite"
    srv.BUDGET = budget
    srv._spent = lambda: spent
    db.connect(srv.NOTES_DB).close()
    (tmp_path / "question.txt").write_text("q")


def test_ask_user_is_non_blocking_and_tags(tmp_path):
    _setup(tmp_path)
    r = _fn(srv.ask_user)("human or mouse?", "assume human")
    assert "Q1" in r and "assumeQ1" in r
    assert srv._inbox_flag() == ""  # the agent's own question doesn't raise the flag


def test_footer_flag_appears_then_clears(tmp_path):
    _setup(tmp_path)
    _fn(srv.ask_user)("human or mouse?", "assume human")
    ix.reply(tmp_path, 1, "mouse only")
    ix.steer(tmp_path, "focus in-vivo")
    footer = srv._db_footer()
    assert "⚑ INBOX" in footer and "1 answer(s)" in footer and "1 guidance" in footer
    ci = _fn(srv.check_inbox)()
    assert "ANSWER to Q1: mouse only" in ci and "GUIDANCE: focus in-vivo" in ci
    assert srv._inbox_flag() == ""  # drained


def test_request_stop_soft_blocks_on_undrained_input(tmp_path, monkeypatch):
    _setup(tmp_path)
    monkeypatch.setattr("graph_search.stop_judge.judge_stop",
                        lambda *a, **k: {"stop": True, "rationale": "ok"})
    ix.steer(tmp_path, "late guidance")
    blocked = _fn(srv.request_stop)("done")
    assert "DO NOT STOP YET" in blocked and "check_inbox" in blocked
    _fn(srv.check_inbox)()  # drain
    assert "Stop approved" in _fn(srv.request_stop)("done")


def test_budget_cap_overrides_soft_block_never_traps(tmp_path):
    _setup(tmp_path, budget=10.0, spent=100.0)  # past the 0.85*budget short-circuit
    ix.steer(tmp_path, "guidance the user never gets drained")
    # even with undrained input, the never-trap cap approves the stop
    assert "Stop approved" in _fn(srv.request_stop)("done")
