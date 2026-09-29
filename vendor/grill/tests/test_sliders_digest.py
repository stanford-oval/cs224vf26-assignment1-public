"""sliders digest integration: pricing, the per-run cost ledger, paper→md
conversion, and SQL over the reconciled table — all offline (no sliders/LLM)."""

from __future__ import annotations

import json

from graph_search import sliders_digest as sd


def test_price_usage_with_cache_discount():
    usage = {
        "gpt-4.1-2025-04-14": {"input_tokens": 1_000_000, "output_tokens": 1_000_000,
                               "input_token_details": {"cache_read": 0}},
    }
    usd, breakdown = sd.price_usage(usage)
    # 1M input @ $2 + 1M output @ $8 = $10.00
    assert usd == 10.0
    # cached input is billed cheaper than fresh input
    cached = {"m-4.1-x": {"input_tokens": 1_000_000, "output_tokens": 0,
                          "input_token_details": {"cache_read": 1_000_000}}}
    usd_cached, _ = sd.price_usage(cached)
    assert usd_cached == 0.5  # all-cached input @ $0.50/M, not $2/M


def test_unknown_model_uses_fallback_price():
    usd, _ = sd.price_usage({"some-random-model": {"input_tokens": 1_000_000, "output_tokens": 0,
                                                    "input_token_details": {}}})
    assert usd == 2.0  # fallback input price


def test_convert_papers_to_md_strips_line_prefixes(tmp_path):
    (tmp_path / "papers").mkdir()
    (tmp_path / "papers" / "PMCX.txt").write_text("L1: Title here\nL2: Body line\nplain line\n")
    md = sd.convert_papers_to_md(tmp_path)
    assert len(md) == 1
    text = (tmp_path / "papers_md" / "PMCX.md").read_text()
    assert "L1:" not in text and "Title here" in text and "Body line" in text


def _fake_job(tmp_path, job, usage, csv_text):
    job_dir = tmp_path / sd.SLIDERS_SUBDIR / job
    job_dir.mkdir(parents=True)
    csv = job_dir / "table.csv"
    csv.write_text(csv_text)
    (job_dir / "meta.json").write_text(json.dumps({"job": job, "n_papers": 2, "started": 0}))
    (job_dir / "result.json").write_text(json.dumps({
        "ok": True, "answer": "a", "table_id": "t", "usage": usage,
        "tables": [{"name": "HRH1Experiment", "csv": str(csv),
                    "columns": csv_text.splitlines()[0].split(","),
                    "n_rows": len(csv_text.splitlines()) - 1}],
    }))
    return job_dir


CSV = (
    "model_name,perturbation_type,drug_name,effect,effect_quote\n"
    "KP2,genetic_knockdown,UNKNOWN,increase,\"shHRH1 raised MHC-I\"\n"
    "MIAPaCa2,antihistamine_drug,Azelastine,increase,\"azelastine 20uM\"\n"
    "AsPC1,antihistamine_drug,Promethazine,increase,\"promethazine\"\n"
)


def test_ledger_is_idempotent_and_summed(tmp_path):
    _fake_job(tmp_path, "20260101_000000", {"gpt-4.1-mini-x": {
        "input_tokens": 1_000_000, "output_tokens": 0, "input_token_details": {"cache_read": 0}}}, CSV)
    st = sd.digest_status(tmp_path)
    assert st["state"] == "done" and st["newly_charged"] is True
    assert st["usd"] == 0.4  # 1M input @ $0.40/M (mini)
    # second read must not double-charge
    assert sd.digest_status(tmp_path)["newly_charged"] is False
    assert sd.sliders_spent_usd(tmp_path) == 0.4
    # reconcile_spend is also idempotent and returns the same total
    assert sd.reconcile_spend(tmp_path) == 0.4


def test_reconcile_spend_picks_up_unpolled_job(tmp_path):
    _fake_job(tmp_path, "20260101_010101", {"gpt-4.1-x": {
        "input_tokens": 500_000, "output_tokens": 0, "input_token_details": {"cache_read": 0}}}, CSV)
    # never called digest_status — reconcile_spend must still record it for the budget
    assert sd.sliders_spent_usd(tmp_path) == 0.0
    total = sd.reconcile_spend(tmp_path)
    assert total == 1.0  # 0.5M input @ $2/M (gpt-4.1)


def test_query_reconciled(tmp_path):
    _fake_job(tmp_path, "20260101_000000", {}, CSV)
    out = sd.query_reconciled(tmp_path, "SELECT perturbation_type, COUNT(*) FROM hrh1experiment GROUP BY perturbation_type ORDER BY 1")
    assert "antihistamine_drug" in out and "genetic_knockdown" in out
    # grounding columns survive
    cols = [t["columns"] for t in sd.available_tables(tmp_path)][0]
    assert "effect_quote" in cols


def test_query_reconciled_no_tables(tmp_path):
    assert "no reconciled evidence yet" in sd.query_reconciled(tmp_path, "SELECT 1")


def test_memory_is_single_canonical_latest_digest(tmp_path):
    # an older digest, then a newer one — the maintained DB reflects only the LATEST
    _fake_job(tmp_path, "20260101_000000", {}, "a,a_quote\nold,q\n")
    _fake_job(tmp_path, "20260102_000000", {}, "b,b_quote\nnew1,q\nnew2,q\n")
    # rename the second job's table so we can tell them apart
    res = tmp_path / sd.SLIDERS_SUBDIR / "20260102_000000" / "result.json"
    import json as _j
    d = _j.loads(res.read_text()); d["tables"][0]["name"] = "NewerTable"; res.write_text(_j.dumps(d))
    names = sorted(t["name"] for t in sd.available_tables(tmp_path))
    assert names == ["newertable"]  # old snapshot is NOT unioned in
    assert sd.query_reconciled(tmp_path, "SELECT COUNT(*) FROM newertable").splitlines()[-1] == "2"


def test_memory_ignores_failed_latest_digest(tmp_path):
    _fake_job(tmp_path, "20260101_000000", {}, CSV)  # ok, table HRH1Experiment
    # a newer FAILED job must not wipe the maintained table
    bad = tmp_path / sd.SLIDERS_SUBDIR / "20260103_000000"
    bad.mkdir(parents=True)
    (bad / "meta.json").write_text(json.dumps({"job": "20260103_000000", "n_papers": 1}))
    (bad / "result.json").write_text(json.dumps({"ok": False, "error": "boom", "tables": []}))
    assert [t["name"] for t in sd.available_tables(tmp_path)] == ["hrh1experiment"]


def test_incremental_digest_accumulates(tmp_path):
    """init digest (base) + incremental digest → maintained table is the UNION (append)."""
    HDR = "model,perturbation_type\n"

    def job(jid, mode, docs, csv_text):
        d = tmp_path / sd.SLIDERS_SUBDIR / jid
        d.mkdir(parents=True)
        csv = d / "t.csv"
        csv.write_text(csv_text)
        (d / "meta.json").write_text(json.dumps({"job": jid, "docs": docs, "started": 0}))
        (d / "result.json").write_text(json.dumps({
            "ok": True, "mode": mode,
            "tables": [{"name": "Evidence", "csv": str(csv),
                        "columns": csv_text.splitlines()[0].split(","),
                        "n_rows": len(csv_text.splitlines()) - 1}]}))

    job("20260101_000000", "init", ["a.md"], HDR + "A1,genetic_knockdown\nA2,antihistamine_drug\n")
    job("20260101_010000", "incremental", ["b.md"], HDR + "B1,genetic_knockdown\n")
    # maintained evidence = base (2 rows) + increment (1 row)
    assert sd.query_reconciled(tmp_path, "SELECT COUNT(*) FROM evidence").splitlines()[-1] == "3"
    assert sd.query_reconciled(tmp_path,
        "SELECT COUNT(*) FROM evidence WHERE perturbation_type='genetic_knockdown'").splitlines()[-1] == "2"
    # both papers tracked → a re-digest of only b.md would be 'nothing new'
    assert sd._digested_papers(tmp_path) == {"a.md", "b.md"}


def test_evidence_markdown_drops_quote_columns(tmp_path):
    _fake_job(tmp_path, "20260101_000000", {}, CSV)
    md = sd.evidence_markdown(tmp_path)
    assert "perturbation_type" in md and "genetic_knockdown" in md
    assert "effect_quote" not in md  # companion grounding columns dropped from the view


def test_status_running_then_timeout(tmp_path):
    import time
    # a started job with no result.json yet, recent → running (not a false 'failed')
    job_dir = tmp_path / sd.SLIDERS_SUBDIR / "20260101_000000"
    job_dir.mkdir(parents=True)
    (job_dir / "meta.json").write_text(json.dumps({"job": "20260101_000000", "n_papers": 1,
                                                    "started": time.time()}))
    assert sd.digest_status(tmp_path)["state"] == "running"
    # same job but started long ago → timed-out failure
    (job_dir / "meta.json").write_text(json.dumps({"job": "20260101_000000", "n_papers": 1,
                                                    "started": time.time() - 99999}))
    assert sd.digest_status(tmp_path)["state"] == "failed"
