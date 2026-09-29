---
name: budget
description: Check the remaining research budget in real USD. paperclip_search / serper_search / fetch calls spend budget; this reports how much has been spent and how much remains. Use it to decide whether to keep searching or to stop and finish.
metadata:
  short-description: Show research-budget usage
---

# budget

Use the **`budget`** tool (MCP server `research`) to report research-budget usage
in **real USD** — your actual token cost so far, read from codex's own usage log.

```
budget()
# [budget: $X | spent: $Y (real) | remaining: $Z | N ops]
```

`paperclip_search`, `serper_search` and `fetch` spend budget; `notes` is cheap.
Once the cap is hit, the search/fetch tools refuse to run. Check this periodically
and **stop when you are confident in the answer, OR when little budget remains** —
leave room to record your final notes.
