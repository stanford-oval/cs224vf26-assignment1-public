"""Per-action activity + cost ledger reconstruction from a codex rollout."""

from __future__ import annotations

import json

from graph_search import activity, spend


def _fc(name, args):
    return {"type": "response_item", "payload": {"type": "function_call", "name": name, "arguments": json.dumps(args)}}


def _patch(name, inp):
    return {"type": "response_item", "payload": {"type": "custom_tool_call", "name": name, "input": inp}}


def _tok(total_eff):
    return {"type": "event_msg", "payload": {"type": "token_count",
            "info": {"total_token_usage": {"input_tokens": total_eff, "cached_input_tokens": 0, "output_tokens": 0}}}}


STATE_V1 = ("*** Begin Patch\n*** Add File: x/state.md\n"
            "+# theta — candidates / categories\n"
            "+| candidate or category | #indep docs | conf | status |\n"
            "+| --- | ---: | --- | --- |\n"
            "+| PARP1 | 0 | — | open |\n"
            "*** End Patch")
STATE_V2 = ("*** Begin Patch\n*** Update File: x/state.md\n@@\n"
            " | --- | ---: | --- | --- |\n"
            "-| PARP1 | 0 | — | open |\n"
            "+| PARP1 | 3 | high | confirmed |\n"
            "*** End Patch")


def _write_rollout(tmp_path):
    rec = [
        {"type": "session_meta", "payload": {"type": "session_meta", "cwd": str(tmp_path)}},
        _fc("paperclip_search", {"query": "PARP1 synthetic lethal"}),
        _tok(100_000),                       # 100k tokens -> $1.00 for the search turn
        _patch("apply_patch", STATE_V1),
        _tok(150_000),                       # +50k -> $0.50 for the state write turn
        _fc("fetch", {"doc_id": "PMC7033043"}),
        _tok(250_000),                       # +100k -> $1.00 for the fetch turn
        _patch("apply_patch", STATE_V2),
        _tok(300_000),                       # +50k -> $0.50
    ]
    roll = tmp_path / "rollout-test.jsonl"
    roll.write_text("\n".join(json.dumps(r) for r in rec), encoding="utf-8")
    # final on-disk state.md (authoritative)
    (tmp_path / "state.md").write_text(
        "# Question\nAre PARP genes SL?\n\n# theta — candidates / categories\n"
        "| candidate or category | #indep docs | conf | status |\n"
        "| --- | ---: | --- | --- |\n"
        "| PARP1 | 3 | high | confirmed |\n", encoding="utf-8")
    return roll


def test_activity_attributes_cost_and_parses_ledger(tmp_path, monkeypatch):
    roll = _write_rollout(tmp_path)
    monkeypatch.setattr(spend, "_select_rollout", lambda rd: str(roll))
    a = activity.build_activity(tmp_path)
    assert a is not None

    # per-action cost sums to the run total (300k tokens * $10/Mtok = $3.00)
    assert abs(a["summary"]["total_usd"] - 3.0) < 1e-6
    assert abs(sum(r["usd"] for r in a["timeline"]) - 3.0) < 1e-6

    kinds = {r["kind"] for r in a["timeline"]}
    assert {"search", "read", "state"} <= kinds
    # the search action carries its turn's $1.00
    search = next(r for r in a["timeline"] if r["kind"] == "search")
    assert abs(search["usd"] - 1.0) < 1e-6
    assert "PARP1" in search["summary"]

    # cumulative cost is monotonic
    cums = [r["cum_usd"] for r in a["timeline"]]
    assert cums == sorted(cums)

    # belief ledger parsed from the on-disk final state.md
    assert a["ledger"]["theta"] == [{"candidate": "PARP1", "indep": "3", "conf": "high", "status": "confirmed"}]

    # two state.md updates reconstructed; the value evolves 0/open -> 3/confirmed
    assert len(a["ledger_versions"]) == 2
    assert a["ledger_versions"][0]["theta"][0]["status"] == "open"
    assert a["ledger_versions"][1]["theta"][0]["status"] == "confirmed"


def test_v4a_apply_replaces_and_appends():
    base = "a\nb\nc"
    patched = activity._apply_v4a(base, "@@\n a\n-b\n+B\n c")
    assert patched == "a\nB\nc"


def test_build_activity_no_rollout(tmp_path, monkeypatch):
    monkeypatch.setattr(spend, "_select_rollout", lambda rd: None)
    assert activity.build_activity(tmp_path) is None
