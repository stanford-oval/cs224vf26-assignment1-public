# Prototype: skills-based agent (`src/skills_agent/`)

A parallel implementation of the same research loop, to compare **inline
functions + fat prompt** (the `graph_search` package) against **codex skills**.

## What's the same

The harness is nearly identical to `graph_search`:
- snapshot `notes.sqlite` into the sandbox,
- run **one** codex session,
- copy the DB back out.

It reuses `graph_search.db` (same notes schema) and
`graph_search.codex_runner` (provider / auth / sandbox setup). The notes DB,
IDS/BOED reasoning, and search→read→store flow are unchanged.

## What's different — delivery of the three capabilities

| | `graph_search` (inline) | `skills_agent` (skills) |
|---|---|---|
| Tools | `functions.py` writes `search.py`/`read.py`/`notesdb.py` into the cwd each run | three skills installed once under `$CODEX_HOME/skills/` |
| Docs | one fat `research.md` documents every tool inline | each skill carries its own `SKILL.md`; the run prompt is slim and just names them |
| Discovery | everything in the prompt, always | codex surfaces skills by name/description; full instructions load on demand |
| Reuse | bespoke to this harness | any codex session/project can use the installed skills |

## Layout

```
src/skills_agent/
  harness.py         install_skills() + run_session() (snapshot DB, run, copy back)
  cli.py             skills-agent {install-skills, run, notes}
  prompt.md          slim prompt: names the skills + IDS/BOED method
  skills/
    litsearch/SKILL.md + scripts/search.py      # paperclip + serper fan-out
    docread/SKILL.md   + scripts/read.py        # fetch full text by id
    notesdb/SKILL.md   + scripts/notesdb.py     # SQL query/store/consolidate
```

Skills follow codex's format (YAML frontmatter `name`/`description`, bundled
`scripts/`), and reference their scripts by the absolute
`${CODEX_HOME:-$HOME/.codex}/skills/<name>/scripts/...` path — the same
convention the built-in `.system` skills use.

## Run

```
uv run skills-agent run "which human genes/proteins are synthetically lethal with SMC3" --db smc3_skills.sqlite
```

`run` auto-installs the skills into `$CODEX_HOME/skills/` first (idempotent).
`skills-agent install-skills` does just the install. Artifacts (transcript,
prompt, DB snapshot) land in `artifacts/skills_agent/<timestamp>/`.

## Open question to validate on a live run

Does `codex exec` auto-surface installed skills to the model? The built-in
`.system` skills suggest yes (loaded from `$CODEX_HOME/skills` at startup). As a
hedge, `prompt.md` explicitly names the three skills and their location and
tells the session to read each `SKILL.md` — so it works whether or not codex
auto-injects the skill descriptions. The live run will show which path the model
actually takes (does it read the SKILL.md files, then call the scripts?).

## Note

`install_skills` writes into the real `~/.codex/skills/` by default (override
with `CODEX_HOME`). The three skill names are namespaced and removable:
`rm -rf ~/.codex/skills/{litsearch,docread,notesdb}`.
