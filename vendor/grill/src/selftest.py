"""Offline self-test — exercises the DETERMINISTIC core (provenance gate, the two-stage test,
the bin and its resurfacing path, budget allocation clamping, metrics, synthesis, steering) with
no codex and no embeddings. Semantic instruments (embeddings + judges) are validated live by the
real run, not here. Run:

    python3 -m src.selftest
"""
from __future__ import annotations

from . import metrics, measure
from .ledger import (Ledger, BINNED, POOLED, PROPOSED, SCREENED,
                     CONFLICTED, REFUTED, SUPPORTED)


def _src(title, author, doi=None, pmid=None):
    return {"title": title, "authors": [author], "year": 2024, "journal": "J",
            "doi": doi, "pmid": pmid, "pmc": None, "url": None, "quote": "q"}


def _ev(text, source, stance="supports", numbers=None):
    return {"text": text, "stance": stance, "source": source, "numbers": numbers or []}


def main() -> int:
    L = Ledger("Which blood-based genomic biomarkers detect early pancreatic cancer, "
               "ranked by validation readiness?")
    L.required_fields = ["biomarker identity", "performance metrics", "validation readiness"]

    # ── INIT: open questions seed directions; candidate answers become HYPOTHESES ──
    seeded = L.seed(open_questions=["ctDNA methylation markers", "fragmentomics signatures"],
                    prior_hypothesis="cfDNA methylation panels lead on validation.",
                    candidate_answers=["ctDNA KRAS mutations"])          # legacy string form still accepted
    assert len(L.directions) == 2, "open questions seed directions"
    assert len(seeded) == 1 and seeded[0].origin == "prior" and seeded[0].status == PROPOSED, \
        "a candidate answer is a hypothesis to test, not a direction to explore"

    Lg = Ledger("q")
    Lg.seed(open_questions=[], prior_hypothesis="h",
            candidate_answers=[{"answer": "high-conf answer", "confidence": 0.9, "aspect": "methylation"},
                               {"answer": "low-conf answer", "confidence": 0.1, "aspect": "mirna"}])
    hs = {h.text: h for h in Lg.hypotheses.values()}
    assert hs["high-conf answer"].confidence == 0.9 and hs["high-conf answer"].aspects == ["methylation"]
    assert len(Lg.prior_candidates) == 2
    assert Ledger.from_json(Lg.to_json()).prior_candidates[0]["answer"] == "high-conf answer"

    # ── EXPLORE ingest: hypotheses, with or without evidence ──────────────────
    d = L.open_directions()[0]
    added = L.ingest_hypotheses([
        {"text": "A cfDNA methylation panel reaches AUC>0.9 for early-stage PDAC.",
         "rationale": "several panels report it", "aspects": ["methylation", "performance metrics"],
         "confidence": 0.8,
         "evidence": [_ev("AUC 0.92 in a 198-patient PDAC cohort",
                          _src("Methylation cfDNA in PDAC", "Wu", doi="10.1/x"),
                          numbers=[{"metric": "AUC", "value": 0.92}, {"metric": "n", "value": 198}])]},
        {"text": "Fragmentomics alone is validation-ready.", "rationale": "worth testing",
         "aspects": ["fragmentomics"], "confidence": 0.4, "evidence": []},
        {"text": "An unsourceable hypothesis.", "rationale": "no locator on its source",
         "aspects": ["misc"], "confidence": 0.3,
         "evidence": [_ev("vague", _src("No locator", "X"))]},        # no DOI/PMID/URL → dropped
    ], direction_id=d.id)
    assert len(added) == 3, "a hypothesis needs no evidence to be admitted — testing decides"
    assert added[0].grounded() and not added[1].grounded()
    assert not added[2].grounded(), "provenance gate: evidence with no resolvable locator is dropped"
    assert d.produced_hypotheses == [h.id for h in added]

    # ── STAGE 1: the screen. Failing BINS (retained), it does not delete ──────
    assert L.apply_screen(added[0], {"plausible": True, "note": "well attested",
                                     "confidence": 0.82, "evidence": []})
    assert added[0].status == SCREENED
    assert not L.apply_screen(added[2], {"plausible": False, "note": "no such literature",
                                         "confidence": 0.05, "evidence": []})
    assert added[2].status == BINNED and "no such literature" in added[2].bin_reason
    assert added[2] in L.binned() and added[2].id in L.hypotheses, "binned == retained, never deleted"

    # ── STAGE 2: the deep test. Supported + uncontradicted → the pool ─────────
    follow = L.apply_deep(added[0], {
        "verdict": "supported", "rationale": "three independent cohorts",
        "conflicts": [], "confidence": 0.88, "new_directions": [],
        "evidence": [_ev("independent validation AUC 0.90",
                         _src("Validation cohort", "Ito", pmid="123456"))]})
    assert follow is None and added[0].status == POOLED and added[0].verdict == SUPPORTED
    assert len(L.evidence_for(added[0])) == 2 and L.support_balance(added[0]) == (2, 0)

    # contradicting evidence blocks the pool even on a "supported" verdict
    L2 = Ledger("q2")
    d2 = L2.add_direction("probe")
    contested = L2.ingest_hypotheses([{"text": "marker M is validated", "rationale": "r",
                                       "aspects": ["m"], "confidence": 0.7, "evidence": []}],
                                     direction_id=d2.id)[0]
    contested.status = SCREENED
    fu = L2.apply_deep(contested, {
        "verdict": "supported", "rationale": "mostly positive",
        "conflicts": ["a 2023 replication failed"], "confidence": 0.5, "new_directions": [],
        "evidence": [_ev("positive", _src("Pos", "A", doi="10.2/pos")),
                     _ev("failed to replicate", _src("Neg", "B", doi="10.2/neg"), stance="contradicts")]})
    assert contested.status == BINNED and contested.verdict == CONFLICTED
    assert L2.support_balance(contested) == (1, 1) and "contested" in contested.bin_reason
    assert fu is not None and fu.question_text.startswith("Resolve the conflict")
    assert fu.tests_hypothesis_id == contested.id

    # refuted → binned with the reason + a bounded re-investigation direction
    ref = L2.ingest_hypotheses([{"text": "marker N detects stage I", "rationale": "r",
                                 "aspects": ["n"], "confidence": 0.6, "evidence": []}],
                               direction_id=d2.id)[0]
    fu2 = L2.apply_deep(ref, {"verdict": "refuted", "rationale": "no supporting literature",
                              "conflicts": [], "confidence": 0.1, "new_directions": [], "evidence": []})
    assert ref.status == BINNED and ref.verdict == REFUTED
    assert fu2.question_text.startswith("Re-investigate") and ref.test_attempts == 1
    # the re-test loop is bounded: past max_attempts no more directions are spawned
    assert L2.apply_deep(ref, {"verdict": "refuted", "rationale": "still nothing", "conflicts": [],
                               "confidence": 0.1, "new_directions": [], "evidence": []}) is not None
    assert L2.apply_deep(ref, {"verdict": "refuted", "rationale": "still nothing", "conflicts": [],
                               "confidence": 0.1, "new_directions": [], "evidence": []}) is None
    assert ref.test_attempts == 3, "bounded re-testing (peeking guard)"

    # a hypothesis regenerated on a re-investigation direction inherits the attempt budget
    child = L2.ingest_hypotheses([{"text": "marker N, restricted to stage I-II", "rationale": "r",
                                   "aspects": ["n"], "confidence": 0.6, "evidence": []}],
                                 direction_id=fu2.id)[0]
    assert child.parent_id == ref.id and child.test_attempts == ref.test_attempts, \
        "attempt budget inherited across regeneration (no infinite retry via fresh hypotheses)"

    # ── the bin is not a grave: corroboration resurfaces ──────────────────────
    binned_h = L2.hypotheses[ref.id]
    before = binned_h.confidence
    fresh = [L2.evidence[e] for e in
             [x.id for x in L2.attach_evidence(contested, [_ev("new independent support",
                                                               _src("New", "C", doi="10.3/new"))])]]
    assert L2.corroborate(binned_h, fresh, per_source=0.30) > 0 and binned_h.confidence > before
    assert L2.corroborate(binned_h, fresh) == 0.0, "the same source cannot corroborate twice"
    L2.unbin(binned_h, reason="independent corroboration")
    assert binned_h.status == SCREENED and binned_h.bin_reason == ""

    # ── metrics over pooled/binned ────────────────────────────────────────────
    assert abs(metrics.quality(L) - 0.5) < 1e-9, "1 pooled / (1 pooled + 1 binned)"
    cov, uncovered = measure.coverage_from_judge(
        [{"field": "biomarker identity", "covered": True, "contributing_aspects": ["methylation"]},
         {"field": "performance metrics", "covered": True, "contributing_aspects": ["performance metrics"]},
         {"field": "validation readiness", "covered": False, "contributing_aspects": []}],
        L.required_fields)
    assert abs(cov - 2 / 3) < 1e-9 and uncovered == ["validation readiness"]
    snap = metrics.build_snapshot(L, cost=1.23, coverage=cov, uncovered=uncovered,
                                  backlog=len(L.pending_screen()) + len(L.pending_deep()),
                                  prev=None, new_hypotheses=3, progress_eps=0.02)
    assert snap.n_pooled == 1 and snap.n_binned == 1 and snap.n_hypotheses == 4
    assert snap.n_evidence == 2 and snap.backlog == 2, "untested hypotheses are backlog, not loss"

    # ── patterns still deepen the frontier ────────────────────────────────────
    rows = L.add_patterns([{"pattern": "methylation+CA19-9 beats either alone", "abstraction": "marker fusion",
                            "instance": "x", "direction": "Quantify the marginal lift of adding CA19-9",
                            "support": "strong", "sources": ["10.1/x"], "hypothesis": "fusion adds ~10pt AUC",
                            "novelty": "medium"}])
    n_before = len(L.directions)
    assert len(L.spawn_from_patterns(rows)) == 1 and len(L.directions) == n_before + 1
    assert "marker fusion" in L.patterns_md() and L.references_md()

    # ── synthesis: the pool leads, the bin is REPORTED (not hidden) ───────────
    ans = L.synthesize()
    assert "AUC=0.92" in ans and "## References" in ans
    assert "cfDNA methylation panel reaches AUC" in ans, "pooled hypothesis in the body"
    assert "Deprioritised hypotheses" in ans and "An unsourceable hypothesis" in ans, \
        "binned hypotheses must be visible in the report, with their reason"
    assert "no such literature" in ans, "the bin reason is shown"
    assert "Untested hypotheses" in ans, "budget-truncated work is disclosed"
    assert ans.count("cfDNA methylation panel reaches AUC") == 1, "no repeat across aspect clusters"
    assert "_(also:" in ans, "secondary aspects show as inline tags"

    # ── serialization round-trip ──────────────────────────────────────────────
    L3 = Ledger.from_json(L2.to_json())
    assert L3.hypotheses[child.id].parent_id == ref.id
    assert L3.directions[fu2.id].tests_hypothesis_id == ref.id
    assert L3.hypotheses[contested.id].status == BINNED
    assert len(L3.evidence_for(L3.hypotheses[contested.id])) == 3
    assert L3._hyp_seq >= len(L3.hypotheses), "id sequences restored — new ids can't collide"

    # ── steering ──────────────────────────────────────────────────────────────
    from .steer import SteerEvent
    from .ledger import OPEN, CLOSED
    Ls = Ledger("steer q")
    Ls.required_fields = ["a", "b"]
    keep = Ls.add_direction("keep me", promise=0.4)
    drop = Ls.add_direction("drop me", promise=0.9)
    ph = Ls.ingest_hypotheses([{"text": "pin me", "rationale": "r", "aspects": ["x"], "confidence": 0.5,
                                "evidence": [_ev("e", _src("PinSrc", "P", doi="10.5/pin"))]}],
                              direction_id=keep.id)[0]
    bh = Ls.ingest_hypotheses([{"text": "bin me", "rationale": "r", "aspects": ["x"],
                                "confidence": 0.5, "evidence": []}], direction_id=keep.id)[0]
    Ls.bin(bh, reason="screen said no")
    ev = SteerEvent.from_dict({
        "directions_add": [{"question_text": "human dir", "rationale": "care about this", "promise": 0.95}],
        "directions_drop": [drop.id, "d999"],          # d999 doesn't exist → skipped, not fatal
        "directions_boost": {keep.id: 0.8},
        "fields_add": ["c"], "fields_remove": ["a"],
        "constraints": ["only since 2020"], "assumptions": ["assume cohort is EGFR+"],
        "hypotheses_pin": [ph.id], "hypotheses_unbin": [bh.id],
        "hypotheses_verdict": [{"hypothesis_id": ph.id, "verdict": "supported"},
                               {"hypothesis_id": "h404", "verdict": "refuted"}],   # missing → dropped
        "artifacts_request": [{"spec": "a csv of every benchmark number", "kind": "data"},
                              "plot the AUCs by marker",          # bare string form
                              {"spec": "  ", "kind": "chart"}],   # empty spec → dropped
        "budget_delta": 10.0, "control": "stop_after_round", "note": "steering test",
    })
    applied = ev.apply_to(Ls)
    human_dirs = [d for d in Ls.directions.values() if d.origin == "human"]
    assert len(human_dirs) == 1 and human_dirs[0].question_text == "human dir"
    assert Ls.directions[drop.id].status == CLOSED and Ls.directions[keep.id].status == OPEN
    assert abs(Ls.directions[keep.id].promise - 0.8) < 1e-9, "boost applied"
    assert Ls.required_fields == ["b", "c"] and Ls.constraints == ["only since 2020"]
    assert ph.pinned and ph.origin == "human"
    assert bh.status == SCREENED, "a human can always pull a hypothesis back out of the bin"
    assert applied.budget_delta == 10.0 and applied.control == "stop_after_round"
    assert [v["hypothesis_id"] for v in applied.verdicts] == [ph.id], "missing-hypothesis verdict dropped"
    # Deliverables are residuals, not ledger state — they never become directions or hypotheses.
    assert [a["spec"] for a in applied.artifacts] == ["a csv of every benchmark number",
                                                      "plot the AUCs by marker"]
    assert applied.artifacts[0]["kind"] == "data" and applied.artifacts[1]["kind"] == ""
    assert not any(d.question_text.startswith("a csv") for d in Ls.directions.values()), \
        "an artifact request must not leak into the research frontier"
    assert Ls.guardrails_md().count("- ") == 2
    # legacy claim-era keys still parse (a deployed portal keeps working)
    legacy = SteerEvent.from_dict({"claims_pin": ["h1"],
                                   "claims_verdict": [{"claim_id": "h1", "verdict": "confirmed"}]})
    assert legacy.hypotheses_pin == ["h1"]
    assert legacy.hypotheses_verdict[0] == {"hypothesis_id": "h1", "verdict": "supported", "note": ""}
    assert SteerEvent.from_dict({}).is_empty()
    assert SteerEvent.from_dict({"control": "garbage"}).control == "continue"

    # ── FileInbox: claim-and-clear drains exactly once (no re-drain) ──────────
    from .steer import FileInbox
    import tempfile as _tf, os as _os
    ibx = _os.path.join(_tf.mkdtemp(prefix="v2_inbox_"), "steer_inbox.json")
    with open(ibx, "w") as _f:
        _f.write('[{"constraints":["s1"]},{"assumptions":["a1"]}]')
    fib = FileInbox(ibx)
    got = fib.poll()
    assert len(got) == 2 and got[0].constraints == ["s1"], "inbox drains queued events"
    assert open(ibx).read().strip() == "[]", "inbox left empty after claim"
    assert fib.poll() == [], "second poll drains nothing (no re-application)"

    # ── WORKSPACE: the per-question git repo the agent builds artifacts in ────
    import csv as _csv_mod
    import json
    import tempfile as _tf2
    from pathlib import Path
    from . import workspace as _ws_mod
    from .workspace import Workspace

    wsroot = Path(_tf2.mkdtemp(prefix="v2_ws_")) / "workspace"
    W = Workspace(wsroot)
    is_repo = W.init(L.question)
    assert (wsroot / "data").is_dir() and (wsroot / "artifacts").is_dir()
    assert (wsroot / "README.md").exists(), "the workspace documents itself for the agent"
    assert W.init(L.question) == is_repo, "init is idempotent (resume calls it again)"

    written = W.export(L, run_meta={"round": 3}, report="# the report\n")
    assert {"data/findings.csv", "data/evidence.csv", "data/metrics.csv",
            "data/findings.json", "data/report.md"} <= set(written)
    fj = json.loads((wsroot / "data" / "findings.json").read_text(encoding="utf-8"))
    assert fj["counts"]["pooled"] == 1 and fj["findings"][0]["status"] == POOLED, \
        "the pool leads the export, same ordering as the report"
    # metrics.csv is the 'give me a csv of all the benchmarks' table: one row per reported number,
    # each still carrying the source it came from.
    with open(wsroot / "data" / "metrics.csv", encoding="utf-8", newline="") as f:
        mrows = list(_csv_mod.DictReader(f))
    assert {r["metric"] for r in mrows} == {"AUC", "n"}
    auc = next(r for r in mrows if r["metric"] == "AUC")
    assert auc["value"] == "0.92" and auc["source_title"] == "Methylation cfDNA in PDAC" \
        and auc["locator"] == "10.1/x", "every number stays traceable to its source"
    assert "findings.csv" in W.data_manifest() and "rows" in W.data_manifest()

    # Artifacts are detected from the FILESYSTEM, so a task that emits no JSON still gets indexed.
    before = W.snapshot()
    (wsroot / "artifacts" / "auc_by_marker.png").write_bytes(b"\x89PNG fake")
    (wsroot / "scripts" / "plot_auc.py").write_text("# builds the chart\n", encoding="utf-8")
    W.export(L)                                   # a re-export must NOT look like a new artifact
    changed = W.changed(before)
    produced = W.artifact_paths(changed)
    assert "data/findings.csv" in changed, "the export did land on disk"
    assert produced == ["artifacts/auc_by_marker.png", "scripts/plot_auc.py"], \
        "harness-owned data/ is committed but never indexed as a deliverable"
    recs = _ws_mod.build_records(W, produced, request="plot the AUCs", declared=[
        {"path": "artifacts/auc_by_marker.png", "title": "AUC by marker", "kind": "chart",
         "description": "from metrics.csv"}], commit=None)
    assert recs[0]["title"] == "AUC by marker" and recs[0]["kind"] == "chart"
    assert recs[1]["title"] == "plot auc" and recs[1]["kind"] == "code", \
        "undeclared files still get a sane title/kind from the path"
    assert recs[0]["bytes"] == 9 and recs[0]["request"] == "plot the AUCs"
    W.write_index(recs)
    assert "AUC by marker" in (wsroot / "ARTIFACTS.md").read_text(encoding="utf-8")
    if is_repo:                                    # git present → every build is a commit
        sha = W.commit("artifact: plot the AUCs")
        assert sha and len(sha) == 40 and W.commit("nothing changed") is None
        subjects = [c["subject"] for c in W.log()]
        assert subjects[0] == "artifact: plot the AUCs" and "workspace: initialise" in subjects

    # ── Budget: one pool, agent-allocated, ceiling-clamped ────────────────────
    import tempfile
    from .orchestrator import Orchestrator, Config, Budget
    B = Budget(20.0)
    B.spend("explore", 5.0)
    B.spend("deep", 3.0)
    assert B.spent == 8.0 and B.remaining() == 12.0
    assert B.by_phase["explore"] == 5.0 and B.by_phase["deep"] == 3.0, "phase tally is bookkeeping only"
    B.add_budget(-100.0)
    assert B.total == 8.0 and B.remaining() == 0.0, "a shrink can never go below what's spent"

    rd = tempfile.mkdtemp(prefix="v2_selftest_")
    cfg = Config(budget=20.0, K=3, alloc_ceiling_frac=0.4, explore_round_frac=0.5,
                 explore_min_usd=1.0)
    orch = Orchestrator("resume q", rd, cfg)
    orch.ledger.required_fields = ["x"]
    # verification is never rationed against exploration: the round pot is only half of what's
    # left, so testing this round's output always has money available.
    assert abs(orch._round_explore_pot() - 10.0) < 1e-9

    dv = orch.ledger.add_direction("dir")
    hv = orch.ledger.ingest_hypotheses([{"text": "test me", "rationale": "r", "aspects": ["x"],
                                         "confidence": 0.7,
                                         "evidence": [_ev("e", _src("VSrc", "V", doi="10.7/v"))]}],
                                       direction_id=dv.id)[0]
    orch.round = 2
    orch.budget.spend("explore", 3.0)
    orch.budget.spend("deep", 1.0)

    # human verdict settles a hypothesis at $0 and pins it; a rejection is BINNED, not deleted
    spent_before = orch.budget.spent
    orch._apply_steer(SteerEvent.from_dict(
        {"hypotheses_verdict": [{"hypothesis_id": hv.id, "verdict": "refuted",
                                 "note": "human says no"}]}), "test")
    assert hv.status == BINNED and hv.pinned and hv.origin == "human"
    assert "human ruling" in hv.bin_reason and hv.id in orch.ledger.hypotheses
    assert abs(orch.budget.spent - spent_before) < 1e-9, "a human ruling costs $0"
    orch._save()

    # an artifact request is queued for the ARTIFACT executor, never applied to the ledger
    dirs_before = len(orch.ledger.directions)
    orch._apply_steer(SteerEvent.from_dict(
        {"artifacts_request": [{"spec": "csv of all the benchmarks", "kind": "data"}]}), "test")
    assert [r["spec"] for r in orch._artifact_requests] == ["csv of all the benchmarks"]
    assert len(orch.ledger.directions) == dirs_before, "a deliverable is not a research direction"
    # asking for a deliverable while saying 'stop' must not drop the request on the floor
    orch._apply_steer(SteerEvent.from_dict(
        {"artifacts_request": ["chart it"], "control": "finalize_now"}), "test")
    assert len(orch._artifact_requests) == 2
    orch._save()
    assert json.loads((Path(rd) / "artifacts.json").read_text(encoding="utf-8"))["pending"]

    # resume rehydrates ledger + runtime state; the test queues are derived, not stored
    orch2 = Orchestrator.resume(rd, cfg)
    assert [r["spec"] for r in orch2._artifact_requests] == ["csv of all the benchmarks", "chart it"], \
        "an unbuilt deliverable survives a resume"
    assert orch2.round == 2 and abs(orch2.budget.spent - 4.0) < 1e-9
    assert orch2.budget.by_phase["explore"] == 3.0 and orch2.budget.by_phase["deep"] == 1.0
    assert orch2.ledger.required_fields == ["x"]
    assert orch2.ledger.hypotheses[hv.id].status == BINNED, "the bin survives a resume"
    assert [h.id for h in orch2.ledger.pending_screen()] == [], "pinned hypotheses are never re-queued"

    # ── the data plane (DESIGN_data_plane.md) — offline, no spend ───────────
    import csv as _csv_mod
    from .ledger import SourceRef as _SourceRef

    dwork = Path(_tf2.mkdtemp(prefix="v2_data_"))
    csv_path = dwork / "genes.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = _csv_mod.writer(f)
        w.writerow(["gene", "sample_a", "sample_b"])
        for row in [("BRCA1", 1, 1), ("TP53", 1, 0), ("EGFR", 0, 1), ("KRAS", 1, 1)]:
            w.writerow(row)

    dws = Workspace(dwork / "run" / "workspace")
    dws.init("data plane selftest")
    dsets = dws.add_inputs([str(csv_path)])
    assert len(dsets) == 1 and dsets[0]["rows"] == 4, "input staged with its real shape"
    assert dsets[0]["columns"] == ["gene", "sample_a", "sample_b"]
    assert dsets[0]["dataset_id"].startswith("genes.csv@"), "dataset_id pins the content digest"
    # a changed file is a DIFFERENT dataset, never a silent redefinition of the old one
    csv_path.write_text(csv_path.read_text(encoding="utf-8") + "MYC,1,1\n", encoding="utf-8")
    assert dws.add_inputs([str(csv_path)])[0]["dataset_id"] != dsets[0]["dataset_id"]
    man = dws.inputs_manifest(dsets)
    assert "gene, sample_a, sample_b" in man and "BRCA1" in man, "manifest = shape + a head sample"
    assert dws.artifact_paths(["inputs/genes.csv", "artifacts/out.csv"]) == ["artifacts/out.csv"], \
        "the researcher's own inputs are never indexed as agent-produced artifacts"

    dl = Ledger("which genes overlap?")
    dh = dl.add_hypothesis("BRCA1 and KRAS are present in both samples", origin="data")
    dsrc = {"kind": "dataset", "dataset_id": dsets[0]["dataset_id"],
            "query": "intersect sample_a and sample_b", "script": "scripts/overlap.py",
            "assumptions": ["present = value 1"], "rows": 2, "title": "", "authors": []}
    dl.attach_evidence(dh, [_ev("2 genes overlap", dsrc)], phase="data")
    assert dl.evidence_for(dh)[0].resolvable(), \
        "data evidence is resolvable via dataset_id + operation, NOT a DOI (§2.1)"
    assert dl.is_data_claim(dh) and dh not in dl.pending_screen(), \
        "a data claim never enters the literature test queue (§2.2)"
    # three DIFFERENT queries on ONE file: three findings, but ONE independent source (§2.3)
    for q in ("count non-null per gene", "dedupe gene symbols"):
        dl.attach_evidence(dh, [_ev(q, {**dsrc, "query": q})], phase="data")
    assert len(dh.evidence_ids) == 3, "distinct operations are distinct evidence"
    assert dl.support_balance(dh) == (1, 0), "…but one dataset is ONE independent source"
    dl.attach_evidence(dh, [_ev("dup", {**dsrc, "query": "intersect sample_a and sample_b"})])
    assert len(dh.evidence_ids) == 3, "an identical operation dedupes"
    dl.attach_evidence(dh, [_ev("a paper agrees", _src("A paper", "Kim", doi="10.1/x"))])
    assert dl.support_balance(dh) == (2, 0), "a real paper IS a second independent source"
    dh.status = POOLED
    assert "10.1/x" in dl.references_md() and "genes.csv@" not in dl.references_md(), \
        "datasets are not bibliography entries"
    dmd = dl.data_sources_md()
    assert "scripts/overlap.py" in dmd and "assumed: present = value 1" in dmd, \
        "data provenance = the script + the assumptions it declared (§6)"
    assert _SourceRef.from_json(dsrc).is_dataset(), "dataset SourceRefs round-trip"
    dl2 = Ledger.from_json(json.loads(json.dumps(dl.to_json())))
    assert dl2.support_balance(dl2.hypotheses[dh.id]) == (2, 0), "independence survives persistence"

    print("SELFTEST OK")
    print(f"  hypotheses={snap.n_hypotheses} pooled={snap.n_pooled} binned={snap.n_binned} "
          f"evidence={snap.n_evidence} coverage={snap.coverage:.2f} quality={snap.quality:.2f}")
    print(f"  budget: one pool, agent-allocated, ceiling {cfg.alloc_ceiling_frac:.0%} of the round pot")
    print(f"  steer: +{len(human_dirs)} human dir, unbin works, resume round={orch2.round}")
    print(f"  workspace: {'git repo' if is_repo else 'plain dir (no git)'}, "
          f"{len(written)} data files exported, {len(recs)} artifact(s) indexed, "
          f"{len(mrows)} benchmark rows")
    print(f"  data plane: {dsets[0]['dataset_id']} staged; 3 queries = 1 independent source; "
          f"data claims skip the literature test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
