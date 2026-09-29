---
name: notesdb
description: Query, store, and consolidate research findings in the notes.sqlite database via SQL. Use to record evidence, check what is already stored (to avoid re-reading documents), and merge duplicate notes.
metadata:
  short-description: Notes database (SQL) for findings
---

# notesdb

Use the **`notes`** tool (MCP server `research`) to run one SQL statement against
the notes DB. It's cheap (does not spend research budget), so query it often.

Schema: `notes(id, doc_name, authors, doc_time, source, url, note, tags, created_at)`
- `tags` is a JSON array string e.g. `'["tag-a","tag-b"]'`; `created_at` auto-fills.
- `SELECT` returns rows as TSV; `INSERT`/`UPDATE`/`DELETE` commit.
- **A SELECT returns at most 10 rows.** Don't expect the whole table back — add
  `WHERE` / `LIMIT` / `ORDER BY` to target the rows you actually need. The
  `[notes.sqlite: …]` footer (note / doc / tag counts) on every response, plus
  `SELECT COUNT(*)` and `GROUP BY` aggregates, give you the big picture without
  dumping rows.

Values in `<…>` are placeholders — substitute your own.

### Read what's already known (do this before searching)

```
notes("SELECT id, doc_name, note FROM notes ORDER BY id DESC LIMIT 10")   # recent notes (≤10)
notes("SELECT DISTINCT doc_name FROM notes")                              # docs stored (skip when reading)
notes("SELECT tags, COUNT(*) AS n FROM notes GROUP BY tags ORDER BY n DESC")  # coverage per tag
notes("SELECT id, doc_name, note FROM notes WHERE note LIKE '%<keyword>%'")   # free-text search
```

### Store a finding (one row per distinct finding)

```
notes("INSERT INTO notes (doc_name, authors, doc_time, source, url, note, tags) VALUES ('<Title>','<Author et al.>','<YYYY>','<source>','<DOC_ID>','<one-sentence finding (L42-L58)>','[\"<tag-a>\",\"<tag-b>\"]')")
notes("INSERT INTO notes (doc_name, note, tags) VALUES ('<Title>','<finding>','[\"<tag>\"]')")
```

### Update / consolidate

```
notes("UPDATE notes SET tags='[\"<tag-a>\",\"verified\"]' WHERE id=<N>")
notes("UPDATE notes SET note='<merged: finding A + finding B (L42-L58)>' WHERE id=<N>")
notes("DELETE FROM notes WHERE id=<N>")   # drop the now-redundant note
```

Rules: escape single quotes inside SQL strings by doubling them (`''`); keep
`tags` a JSON array string; reuse consistent short tags so similar notes cluster;
never delete a *distinct* finding.
