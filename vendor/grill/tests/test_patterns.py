"""Abstract-pattern extraction (Lever 3): one LLM call -> stored, grouped patterns."""

from __future__ import annotations

import json

from graph_search import patterns, stop_judge


def _fake_resp(rows):
    return {"choices": [{"message": {"content": json.dumps({"patterns": rows})}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500}}


_ROWS = [
    {"pattern": "perturb→phenotype", "abstraction": "removing a node lowers a downstream readout",
     "instance": "HRH1 knockdown reduces metastasis", "direction": "decrease", "support": "direct",
     "sources": "Zhao 2019", "hypothesis": "knocking out the node abolishes the readout",
     "novelty": "established"},
    {"pattern": "two methods agree", "abstraction": "genetic and chemical blockade give the same effect",
     "instance": "shRNA and azelastine both raise MHC-I", "direction": "increase", "support": "direct",
     "sources": "Zhong 2024", "hypothesis": "a third modality will also raise it", "novelty": "established"},
    {"pattern": "perturb→phenotype", "abstraction": "removing a node lowers a downstream readout",
     "instance": "ADAM9 loss lowers invasion", "direction": "decrease", "support": "indirect",
     "sources": "Ding 2025", "hypothesis": "restoring the node rescues invasion", "novelty": "novel"},
]


def test_extract_patterns_stores_and_costs(tmp_path, monkeypatch):
    monkeypatch.setattr(stop_judge, "_post", lambda msgs: _fake_resp(_ROWS))
    res = patterns.extract_patterns(tmp_path, "compare genetic vs drug blockade")
    assert res["error"] is None
    assert len(res["rows"]) == 3
    assert res["usd"] > 0                       # 1500 tokens * $10/Mtok
    stored = patterns.read_patterns(tmp_path)
    assert len(stored) == 3
    assert stored[0]["pattern"] == "perturb→phenotype"


def test_extract_patterns_soft_fails(tmp_path, monkeypatch):
    def boom(msgs):
        raise RuntimeError("judge endpoint down")
    monkeypatch.setattr(stop_judge, "_post", boom)
    res = patterns.extract_patterns(tmp_path, "q")
    assert res["rows"] == [] and res["error"] and res["usd"] == 0.0


def test_format_groups_by_pattern():
    out = patterns.format_patterns(_ROWS)
    # the recurring abstract structure is grouped (2 instances) and listed first
    assert "perturb→phenotype  (2 instances)" in out
    assert "two methods agree  (1 instance)" in out
    assert "hypothesis:" in out


def test_read_patterns_empty(tmp_path):
    assert patterns.read_patterns(tmp_path) == []
