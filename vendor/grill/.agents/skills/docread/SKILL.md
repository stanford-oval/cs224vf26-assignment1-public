---
name: docread
description: Download a document's full text to disk by id (e.g. a PMC id), then read it with your own shell tools (grep/rg/sed). Use when you have a document id from a search and want to read it.
metadata:
  short-description: Fetch a document to disk, then read it with the shell
---

# docread

Use the **`fetch`** tool (MCP server `research`) to download a document's full
text to disk by id.

```
fetch(doc_id)
```

- `doc_id`: an id from your search results (a `channel:id` prefix is stripped).
- It saves the numbered full text to **`./papers/<id>.txt`** and returns the
  **path + metadata only — NOT the body**.

Then **read the file yourself with your shell** — you're good at this, so use
whatever fits:

```
rg -n "<keyword>|<another-term>" papers/<id>.txt          # find the relevant lines
sed -n '120,170p' papers/<id>.txt                         # read a section
grep -nE "Results|Discussion" papers/<id>.txt             # jump to structure
```

The `Lxx:` prefixes are citation line numbers — cite the `Lxx` ranges in your
notes. Skip documents already recorded in the notes DB — fetch NEW ones. Each
`fetch` costs research budget (reading the saved file with your shell does not, but
the tokens still count toward your real spend).

**After reading, reflect before moving on:** what new candidate answers,
answer-categories, mechanisms, or cited papers did this document surface? Add them
to your θ ledger as `open`, and decide whether each is worth a fresh search now — a
document you read should usually spawn your next search rather than end the loop.
