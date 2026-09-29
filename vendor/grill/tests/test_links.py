"""Citation / link frontier (Lever 2): mine refs from fetched text, rank the
unread co-cited ones."""

from __future__ import annotations

from graph_search import links


def test_extract_refs_all_id_types_and_dedupe():
    text = ("See PMC1234567 and pmid: 7654321. Also doi:10.1038/s41586-020-2649-2 "
            "and arXiv: 2401.01234. PMC1234567 again (dup).")
    refs = links.extract_refs(text)
    ids = {r["id"] for r in refs}
    assert "PMC1234567" in ids
    assert "PMID:7654321" in ids
    assert "10.1038/s41586-020-2649-2" in ids
    assert "arXiv:2401.01234" in ids
    assert sum(r["id"] == "PMC1234567" for r in refs) == 1  # deduped


def test_record_links_skips_self_and_persists(tmp_path):
    n = links.record_links(tmp_path, "PMC900100", "cites PMC900200 and PMC900100 (self) and PMC900300")
    assert n >= 2
    edges = (tmp_path / links.LINKS_FILE).read_text().splitlines()
    refs = {__import__("json").loads(e)["ref"] for e in edges}
    assert refs == {"PMC900200", "PMC900300"}  # self-citation dropped


def test_frontier_ranks_unread_by_cocitation(tmp_path):
    # PMC900001 and PMC900002 both cite PMC900009 (co-cited x2); PMC900001 also cites PMC900008 (x1).
    links.record_links(tmp_path, "PMC900001", "refs PMC900009 PMC900008")
    links.record_links(tmp_path, "PMC900002", "refs PMC900009")
    # PMC900008 later gets read -> it becomes a source and drops off the frontier.
    links.record_links(tmp_path, "PMC900008", "refs PMC900007")
    fr = links.frontier(tmp_path)
    ids = [r["ref"] for r in fr]
    assert ids[0] == "PMC900009" and fr[0]["cited_by"] == 2     # most co-cited first
    assert "PMC900008" not in ids                               # now read -> excluded
    assert "PMC900007" in ids                                   # new unread ref surfaced
