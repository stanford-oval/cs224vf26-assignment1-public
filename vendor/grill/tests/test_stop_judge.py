"""request_stop flow (approve / continue-with-gaps / budget short-circuit /
rejection cap) with a mocked judge, plus the judge's fail-open behavior."""

from __future__ import annotations

import graph_search.mcp_server as srv
from graph_search import sliders_digest, stop_judge


def _setup(tmp_path, budget=50.0, spent=1.0):
    srv.RUN_DIR = tmp_path
    srv.BUDGET = budget
    srv._db_footer = lambda: ""
    srv._spent = lambda: spent
    (tmp_path / "question.txt").write_text("which genes are synthetically lethal with CDH1?")


def test_request_stop_approves_and_charges(tmp_path, monkeypatch):
    _setup(tmp_path)
    monkeypatch.setattr(stop_judge, "judge_stop",
                        lambda *a, **k: {"stop": True, "gaps": [], "rationale": "good coverage", "usd": 0.02})
    out = srv.request_stop("covered every category")
    assert "Stop approved by supervisor" in out
    assert sliders_digest.sliders_spent_usd(tmp_path) == 0.02  # judge cost hit the budget


def test_request_stop_continues_with_gaps(tmp_path, monkeypatch):
    _setup(tmp_path)
    monkeypatch.setattr(stop_judge, "judge_stop",
                        lambda *a, **k: {"stop": False, "gaps": ["check colon cancer", "try serper for X"],
                                         "rationale": "categories missing", "usd": 0.02})
    out = srv.request_stop("I think I'm done")
    assert "DO NOT STOP" in out and "check colon cancer" in out
    assert (tmp_path / ".stop_attempts").read_text() == "1"


def test_budget_shortcircuit_skips_judge(tmp_path, monkeypatch):
    _setup(tmp_path, budget=50.0, spent=45.0)  # 90% > 85%
    called = []
    monkeypatch.setattr(stop_judge, "judge_stop",
                        lambda *a, **k: called.append(1) or {"stop": False, "gaps": ["x"], "usd": 0})
    out = srv.request_stop("done")
    assert "budget is nearly spent" in out and not called  # judge not consulted near the cap


def test_rejection_cap_allows_stop_when_budget_used(tmp_path, monkeypatch):
    _setup(tmp_path, budget=50.0, spent=40.0)  # 80% used — past the 60% gate
    (tmp_path / ".stop_attempts").write_text(str(srv.MAX_STOP_REJECTIONS))
    called = []
    monkeypatch.setattr(stop_judge, "judge_stop",
                        lambda *a, **k: called.append(1) or {"stop": False, "gaps": ["x"], "usd": 0})
    out = srv.request_stop("done")
    assert "most of the budget is used" in out and not called  # cap fires, never trapped


def test_rejection_cap_deferred_while_budget_remains(tmp_path, monkeypatch):
    # Past the rejection cap BUT lots of budget left -> still defer to the judge so it
    # can push a valuable direction (the point of the budget-aware cap).
    _setup(tmp_path, budget=50.0, spent=5.0)  # 10% used — below the 60% gate
    (tmp_path / ".stop_attempts").write_text(str(srv.MAX_STOP_REJECTIONS + 2))
    monkeypatch.setattr(stop_judge, "judge_stop",
                        lambda *a, **k: {"stop": False, "gaps": ["explore mechanism Y"],
                                         "rationale": "budget left; valuable direction open", "usd": 0.02})
    out = srv.request_stop("I think I'm done")
    assert "DO NOT STOP" in out and "explore mechanism Y" in out


def test_judge_prompt_includes_belief_ledger_and_remaining_budget(tmp_path, monkeypatch):
    (tmp_path / "state.md").write_text(
        "# θ — candidates / categories\n| cand | #docs | conf | status |\n"
        "| PARP1 | 0 | — | open |\n\n# D — angles\n- tried: synthetic-lethal screens\n")
    captured = {}

    def fake_post(messages):
        captured["messages"] = messages
        return {"choices": [{"message": {"content": '{"stop": false, "gaps": ["g"], "rationale": "r"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

    monkeypatch.setattr(stop_judge, "_post", fake_post)
    stop_judge.judge_stop(tmp_path, "Q?", "reason", budget=50.0, spent=10.0)
    user = captured["messages"][1]["content"]
    assert "BELIEF LEDGER" in user and "PARP1" in user and "open" in user   # ledger surfaced
    assert "$40.00 remaining" in user and "80%" in user                     # remaining budget surfaced


def test_judge_fails_open_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_DOCUSET_API_KEY", raising=False)
    v = stop_judge.judge_stop(tmp_path, "q", "reason")
    assert v["stop"] is True and v["usd"] == 0.0  # broken judge never traps the agent
