"""The run inbox: monotonic ids, torn-line tolerance, single-writer cursor,
concurrent multi-process appends, and the user-CLI views."""

from __future__ import annotations

import json
import multiprocessing
from pathlib import Path

from graph_search import interaction as ix


def test_ask_reply_steer_roundtrip(tmp_path):
    q1 = ix.ask(tmp_path, "human or mouse data?", "assume human")
    q2 = ix.ask(tmp_path, "which cancer?", "assume breast")
    assert (q1, q2) == (1, 2)  # monotonic qids
    g1 = ix.steer(tmp_path, "prioritize in-vivo studies")
    assert g1 == 1
    ix.reply(tmp_path, q1, "mouse only")

    events, new = ix.read_since_cursor(tmp_path)
    kinds = [(e["kind"], e.get("qid") or e.get("gid")) for e in events]
    assert kinds == [("question", 1), ("question", 2), ("guidance", 1), ("answer", 1)]
    assert new > 0


def test_cursor_marks_seen_once(tmp_path):
    ix.steer(tmp_path, "focus on resistance")
    assert ix.has_pending(tmp_path)
    events, new = ix.read_since_cursor(tmp_path)
    assert len(events) == 1
    ix.advance_cursor(tmp_path, new)
    # after advancing, nothing new
    assert not ix.has_pending(tmp_path)
    assert ix.read_since_cursor(tmp_path)[0] == []
    # a later event surfaces again
    ix.steer(tmp_path, "more")
    assert ix.has_pending(tmp_path)


def test_torn_trailing_line_is_ignored(tmp_path):
    ix.steer(tmp_path, "complete event")
    # append a partial (un-terminated) line as if a writer were mid-append
    with ix._inbox_path(tmp_path).open("a", encoding="utf-8") as fh:
        fh.write('{"kind":"guidance","gid":2,"text":"half')
    events, new = ix.read_since_cursor(tmp_path)
    assert [e["text"] for e in events] == ["complete event"]  # torn line skipped
    # cursor only advanced past the complete line, so the torn bytes remain unseen
    assert new == ix._complete_size(tmp_path)
    # once the writer finishes the line, it becomes visible
    with ix._inbox_path(tmp_path).open("a", encoding="utf-8") as fh:
        fh.write(' done"}\n')
    ix.advance_cursor(tmp_path, new)
    events2, _ = ix.read_since_cursor(tmp_path)
    assert [e["text"] for e in events2] == ["half done"]


def test_open_questions_and_list_inbox(tmp_path):
    ix.ask(tmp_path, "q1", "a1")
    ix.ask(tmp_path, "q2", "a2")
    ix.reply(tmp_path, 1, "answer to q1")
    ix.steer(tmp_path, "g")
    open_qs = ix.open_questions(tmp_path)
    assert [q["qid"] for q in open_qs] == [2]  # q1 answered, q2 still open
    snap = ix.list_inbox(tmp_path)
    assert len(snap["guidance"]) == 1 and snap["total_events"] == 4


def _spam_appends(run_dir, kind_text):
    for i in range(50):
        ix.append_event(run_dir, {"kind": "guidance", "gid": i, "text": f"{kind_text}-{i}"})


def test_concurrent_multiprocess_appends_dont_corrupt(tmp_path):
    procs = [multiprocessing.Process(target=_spam_appends, args=(str(tmp_path), w))
             for w in ("A", "B", "C")]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    # every line must be valid JSON (no interleaving/corruption), and we get all of them
    lines = ix._inbox_path(tmp_path).read_text(encoding="utf-8").splitlines()
    parsed = [json.loads(ln) for ln in lines if ln.strip()]
    assert len(parsed) == 150
    assert {p["text"].split("-")[0] for p in parsed} == {"A", "B", "C"}


def test_long_text_truncated_under_pipe_buf(tmp_path):
    ix.steer(tmp_path, "x" * 9000)
    line = ix._inbox_path(tmp_path).read_bytes()
    assert len(line) < 4096  # stays atomic-appendable
    ev = ix._read_events(tmp_path)[0]
    assert ev["text"].endswith("…[truncated]")
