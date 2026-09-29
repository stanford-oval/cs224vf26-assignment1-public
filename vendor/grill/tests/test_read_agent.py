"""Reading sub-agent: distill small text; abstracts vs full papers by size."""

from __future__ import annotations

import json

from graph_search import read_agent, stop_judge


def _resp(findings, relevant=True):
    return {"choices": [{"message": {"content": json.dumps({"relevant": relevant, "findings": findings})}}],
            "usage": {"prompt_tokens": 800, "completion_tokens": 200}}


def test_distill_returns_findings_and_cost(monkeypatch):
    monkeypatch.setattr(stop_judge, "_post", lambda m: _resp(["HRH1 knockdown lowers metastasis (L12)"]))
    res = read_agent.distill("…short abstract text…", "genetic vs drug blockade", label="PMC1")
    assert res["error"] is None
    assert res["relevant"] is True
    assert res["findings"] == ["HRH1 knockdown lowers metastasis (L12)"]
    assert res["usd"] > 0


def test_distill_soft_fails(monkeypatch):
    def boom(m):
        raise RuntimeError("endpoint down")
    monkeypatch.setattr(stop_judge, "_post", boom)
    res = read_agent.distill("x", "q")
    assert res["findings"] == [] and res["error"] and res["usd"] == 0.0


def test_abstract_from_meta_json_and_fallback():
    assert read_agent.abstract_from_meta(json.dumps({"abstract": "the abstract"})) == "the abstract"
    assert read_agent.abstract_from_meta(json.dumps({"snippet": "snip"})) == "snip"
    # non-JSON -> returns the (small) raw text, capped at SMALL_LIMIT
    raw = "not json " * 10
    assert read_agent.abstract_from_meta(raw) == raw


def test_read_limits():
    # the sub-agent reads out-of-context, so a full paper is distilled directly;
    # only a book-length doc exceeds the hard cap and is routed to digest.
    abstract = "a" * 2000
    full_paper = "L1: word " * 8_000          # ~64k chars — a normal full paper
    book = "x" * 200_000
    assert len(abstract) <= read_agent.SMALL_LIMIT
    assert len(full_paper) <= read_agent.READ_HARD_LIMIT   # read() distills it
    assert len(book) > read_agent.READ_HARD_LIMIT          # too big -> digest
