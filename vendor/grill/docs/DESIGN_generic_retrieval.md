# DESIGN: simple generic research agent

Barebones. Not production-ready. The agent does three things; the planner
decides what to do next using IDS/BOED reasoning.

## The agent's three verbs

- **search** — `paperclip`, `serper`, or any other API. Returns a list of
  documents (name, authors, date, id/url, snippet). Agent picks the source.
- **read** — fetch a document's text and reason about it.
- **store** — write the interesting bits to the notes DB.

## The notes DB (one table)

```sql
CREATE TABLE notes (
    id          INTEGER PRIMARY KEY,
    doc_name    TEXT,
    authors     TEXT,
    doc_time    TEXT,        -- publication date
    source      TEXT,        -- paperclip | serper | ...
    url         TEXT,
    note        TEXT,        -- the evidence / interesting thing
    tags        TEXT,        -- list; used to bring similar notes together
    created_at  TEXT
);
```

`tags` is the only clustering mechanism — similar notes share tags, so the
planner can see what's well-covered vs thin.

## The loop

```
while not done:
    action = planner(root_question, notes_grouped_by_tag)   # IDS/BOED
    if action.done: break
    results = search(action.query, action.source)           # agent
    docs    = read(pick relevant results)                   # agent
    store(notes from docs)                                  # agent -> DB
```

## The planner (IDS / BOED)

A codex shard. Given the root question + the current notes summarized by
tag, it reasons about **expected information gain**: which next search or
read best reduces uncertainty about the question. Explore thin/empty tags
vs exploit promising ones. Output: the next action, or `done`.

It's LLM reasoning framed with IDS/BOED — not numerical EIG. Keep it a
prompt, not a math engine.

## Files (barebones)

- `db.py` — sqlite + the `notes` table.
- `tools.py` — `search(query, source)`, `read(doc)`.
- `agent.py` — codex shard that searches / reads / stores.
- `planner.py` — codex shard that picks the next action via IDS/BOED.
- `run.py` — the loop above.

## Avoid re-reading (kept trivial)

Before storing, the agent checks the notes DB for the doc name; if already
there, the planner steers the next search toward documents not yet in the
notes. No ledger, no wrappers — just "is it already in notes?".
```
