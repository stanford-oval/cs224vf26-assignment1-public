---
name: litsearch
description: Search the scientific literature. Two separate tools — paperclip_search (PMC, abstracts, preprints) and serper_search (Google Scholar / web). Use when you need to find documents or papers relevant to a research question.
metadata:
  short-description: Literature search (paperclip + serper, separately)
---

# litsearch

Two **separate** search tools on the MCP server `research`:

- **`paperclip_search(query, paperclip_source="pmc", num=10)`** — the paperclip
  biomedical corpus. `paperclip_source`: `pmc` (default), `abstracts`, `biorxiv`,
  `medrxiv`, `arxiv`. Returns titles, ids, snippets. `fetch` a result by id to read it.
- **`serper_search(query, num=10, mode="scholar")`** — Google Scholar / open web.
  A **discovery** channel: use it to find a title / PMID / DOI that paperclip misses
  or under-ranks, then `paperclip_search` that exact title/id and `fetch` it so your
  citations stay grounded in full text you actually read.

## Two channels, different jobs

- **`serper_search` = discovery / coverage.** Broadest reach — surfaces documents
  paperclip doesn't contain or ranks poorly (older, cross-domain, long-tail). Tells
  you **what exists** and gives a title / id / link, but **only titles + snippets**,
  not readable full text.
- **`paperclip_search` + `fetch` = reading.** paperclip gives grep-able, citeable
  full text; `paperclip_search` finds documents in that corpus.

**The handoff:** when serper surfaces a promising document, get it into full text —
`fetch` its id if the link exposes one, else `paperclip_search` its **exact title**
to resolve a fetchable id, then `fetch`. This recovers documents paperclip *has* but
didn't rank for your query. If a document isn't in paperclip at all (fetch +
title-search both fail), you may record the serper title+snippet as a snippet-only
**Class 3** lead — but prefer full text whenever reachable.

Tips:

- Run **both** tools with several phrasings, then de-duplicate hits by document id.
- Early on, search broadly to map the answer-space; as new-document yield falls,
  narrow to the specific gaps still missing notes.
- Each search call costs research budget; `notes` queries are free, so check what
  you already have before searching again.
