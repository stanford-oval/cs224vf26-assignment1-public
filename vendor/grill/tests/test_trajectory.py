"""Trajectory reconstruction: a synthetic run dir with every artifact populated
should yield a portal-renderable node-link graph."""

from __future__ import annotations

import json
import sqlite3

from graph_search import db, trajectory


def _make_run(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "question.txt").write_text("Are X and Y synthetic lethal?", encoding="utf-8")

    # notes.sqlite — 3 notes across 2 docs
    with db.connect(run / "notes.sqlite") as c:
        for doc, au, yr, ident, note in [
            ("Paper A", "Zhao et al.", "2019", "PMC7033043", "X knockdown kills Y-mut cells (L10)."),
            ("Paper A", "Zhao et al.", "2019", "PMC7033043", "Rescue restores viability (L22)."),
            ("Paper B", "Li et al.", "2022", "PMID:34822775", "Drug Z phenocopies X loss (L5)."),
        ]:
            c.execute("INSERT INTO notes (doc_name, authors, doc_time, source, url, note, tags) "
                      "VALUES (?,?,?,?,?,?,?)", (doc, au, yr, "pmc", ident, note, "sl"))
        c.commit()

    # .events.jsonl — 2 searches + 1 stop-judge verdict
    with (run / ".events.jsonl").open("w", encoding="utf-8") as f:
        f.write(json.dumps({"kind": "search", "channel": "paperclip:pmc", "query": "X synthetic lethal Y"}) + "\n")
        f.write(json.dumps({"kind": "search", "channel": "serper:scholar", "query": "X Y SL screen"}) + "\n")
        f.write(json.dumps({"kind": "judge", "reason": "covered", "stop": False,
                            "rationale": "needs orthogonal assay", "gaps": ["CRISPR screen?"], "attempt": 1}) + "\n")

    # memory.sqlite — a reconciled evidence table (with cols that must be filtered out)
    with sqlite3.connect(run / "memory.sqlite") as c:
        c.execute("CREATE TABLE evidence (cell_model TEXT, perturbation TEXT, effect TEXT, "
                  "effect_quote TEXT, reconciliation_context TEXT, _job TEXT)")
        c.execute("INSERT INTO evidence VALUES ('KP2','knockdown','lethal','\"...\"','ctx','j1')")
        c.execute("INSERT INTO evidence VALUES ('SW','drug Z','lethal','\"...\"','ctx','j1')")
        c.commit()

    # finalize/answer.md — section 1 candidate table
    (run / "finalize").mkdir()
    (run / "finalize" / "answer.md").write_text(
        "### 1. Final candidate list\n\n"
        "| Entity (requested form) | Class | Basis |\n"
        "|---|---:|---|\n"
        "| X | 1 | direct |\n"
        "| Z | 2 | inferred |\n", encoding="utf-8")
    return run


def test_build_trajectory_full(tmp_path):
    run = _make_run(tmp_path)
    g = trajectory.build_trajectory(run)
    assert g is not None
    for k in ("nodes", "edges", "kinds", "detail", "panel", "ev", "cands", "viewBox"):
        assert k in g

    kinds = {n["kind"] for n in g["nodes"]}
    assert {"question", "search", "paper", "note", "digest", "judge", "answer"} <= kinds

    # 2 distinct docs -> 2 paper nodes; 3 notes -> 3 note nodes
    assert sum(n["kind"] == "paper" for n in g["nodes"]) == 2
    assert sum(n["kind"] == "note" for n in g["nodes"]) == 3

    # evidence table: bookkeeping / provenance columns filtered out
    assert g["ev"]["cols"] == ["cell_model", "perturbation", "effect"]
    assert len(g["ev"]["rows"]) == 2
    assert g["panel"]["dg"]["type"] == "table" and g["panel"]["dg"]["total"] == 2

    # stop-judge verdict surfaced
    jpanel = next(p for p in g["panel"].values() if p.get("type") == "judge")
    assert jpanel["stop"] is False and jpanel["gaps"] == ["CRISPR screen?"]

    # candidates parsed (entity, class)
    assert g["cands"] == [["X", 1], ["Z", 2]]

    # search queries captured
    spanel = next(p for p in g["panel"].values() if p.get("type") == "search")
    assert any("synthetic lethal" in q for q in spanel["queries"])

    # graph integrity: no dangling edges
    ids = {n["id"] for n in g["nodes"]}
    assert all(e["a"] in ids and e["b"] in ids for e in g["edges"])


def test_build_trajectory_thin_returns_none(tmp_path):
    run = tmp_path / "empty"
    run.mkdir()
    assert trajectory.build_trajectory(run) is None


def test_write_trajectory_emits_file(tmp_path):
    run = _make_run(tmp_path)
    dest = tmp_path / "portal" / "h1_db" / "trajectory.json"
    out = trajectory.write_trajectory(run, dest=dest)
    assert out and out.is_file()
    assert dest.is_file()
    assert json.loads(dest.read_text())["viewBox"].startswith("0 0 ")
