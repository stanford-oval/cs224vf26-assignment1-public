"""Budget hard-kill: the watchdog reads real spend (codex tokens + digest) and
kills the shard at the cap. We unit-test the spend reader + threshold here."""

from __future__ import annotations

from graph_search import codex_runner


def test_research_spend_sums_codex_and_digest(monkeypatch):
    from graph_search import sliders_digest, spend
    monkeypatch.setattr(spend, "spent_usd", lambda rd: 40.0)
    monkeypatch.setattr(sliders_digest, "reconcile_spend", lambda rd: 2.5)
    assert codex_runner._research_spend_usd("/run") == 42.5


def test_research_spend_tolerates_missing_usage(monkeypatch):
    from graph_search import sliders_digest, spend
    monkeypatch.setattr(spend, "spent_usd", lambda rd: None)        # no rollout yet
    monkeypatch.setattr(sliders_digest, "reconcile_spend", lambda rd: 0.0)
    assert codex_runner._research_spend_usd("/run") == 0.0


def test_research_spend_swallows_errors(monkeypatch):
    from graph_search import spend
    def boom(rd):
        raise RuntimeError("rollout glob failed")
    monkeypatch.setattr(spend, "spent_usd", boom)
    assert codex_runner._research_spend_usd("/run") == 0.0


def test_kill_threshold(monkeypatch):
    # spend >= budget * factor -> over budget
    monkeypatch.setattr(codex_runner, "_research_spend_usd", lambda rd: 50.01)
    monkeypatch.setattr(codex_runner, "BUDGET_KILL_FACTOR", 1.0)
    budget = 50.0
    assert codex_runner._research_spend_usd("/r") >= budget * codex_runner.BUDGET_KILL_FACTOR
    # under budget -> not over
    monkeypatch.setattr(codex_runner, "_research_spend_usd", lambda rd: 49.0)
    assert not (codex_runner._research_spend_usd("/r") >= budget * codex_runner.BUDGET_KILL_FACTOR)
