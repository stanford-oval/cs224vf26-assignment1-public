"""The per-question WORKSPACE — a git repository the agent builds artifacts in.

Every run-dir gets a ``workspace/`` subdirectory that is a real git repo. It is the one place in
the run where files persist across tasks and where the agent is allowed to *build* things rather
than just report them:

    <run-dir>/workspace/
        data/         ← written by the HARNESS from the ledger (read-only for the agent)
        inputs/       ← the USER's own data files (read-only; see DESIGN_data_plane.md)
        artifacts/    ← what the agent produces: charts, CSVs, tables, docs
        scripts/      ← the code that produced them (committed alongside, so it's reproducible)
        ARTIFACTS.md  ← the human-readable index
        .git/         ← full history: every artifact task is a commit

Two design points:

1. **The data comes from the ledger, deterministically.** Before any artifact task the harness
   exports the belief state to ``data/`` as JSON + CSV (findings, evidence, and one long-format
   ``metrics.csv`` holding every number any source reported). The agent computes over real files
   with pandas instead of transcribing numbers out of a prompt — which is also what stops it
   inventing them.

2. **Artifacts are detected from the filesystem, not from the model's word.** A task's declared
   output is metadata only; what actually counts as produced is whatever changed on disk
   (``snapshot`` → ``changed``). So a task that emits no JSON, or one whose sandbox blocked
   ``git commit``, still gets its work indexed and committed by the harness.

Pure Python + the ``git`` CLI — no codex, no spend, no network. Fully exercised by the offline
self-test, and degrades to a plain (uncommitted) folder when git is unavailable.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

DATA = "data"
INPUTS = "inputs"
ARTIFACTS = "artifacts"
SCRIPTS = "scripts"
INDEX_MD = "ARTIFACTS.md"

# Paths the harness owns — changes under these are committed but never indexed as artifacts.
# `inputs/` is the USER's data: harness-placed and read-only like data/, but never regenerated,
# so it must not be mistaken for something the agent produced.
_NOT_ARTIFACTS = (DATA + "/", INPUTS + "/", INDEX_MD, "README.md", ".gitignore",
                  ".codex")   # codex drops a marker file in its cwd — not a deliverable

# Machine droppings: never a deliverable. Tool caches especially — matplotlib writes a ~90KB font
# list on first import, which would otherwise read as "the agent produced a data file" purely
# because it appeared while the task was running.
_SKIP_DIRS = {".git", "__pycache__", ".mplcache", ".matplotlib", ".ipynb_checkpoints",
              ".pytest_cache", ".cache", "node_modules", ".venv"}

_KIND_BY_EXT = {
    ".png": "chart", ".svg": "chart", ".jpg": "chart", ".jpeg": "chart", ".pdf": "chart",
    ".csv": "data", ".tsv": "data", ".xlsx": "data", ".json": "data", ".parquet": "data",
    ".md": "doc", ".txt": "doc", ".html": "doc",
    ".py": "code", ".sh": "code", ".r": "code", ".ipynb": "code",
}

_README = """# Workspace — {question}

A git-controlled scratch space for ONE research question. The agent works here.

- `data/` — exported from the belief ledger by the harness before every artifact task.
  **Read-only**: it is overwritten on each export, so never edit it by hand.
  - `findings.json`  — every tested hypothesis with its evidence and sources
  - `findings.csv`   — one row per hypothesis (status, verdict, confidence, support balance)
  - `evidence.csv`   — one row per sourced evidence item
  - `metrics.csv`    — long format: every number any source reported, with its source
  - `report.md`      — the current report (once the run has finalized)
  - `run.json`       — budget, rounds, and checkpoint snapshots
- `inputs/` — the researcher's OWN data files, placed here by the harness. **Read-only —
  never modify or overwrite them.** Query them from a script; write results to `artifacts/`.
- `artifacts/` — the deliverables: charts, tables, spreadsheets, documents.
- `scripts/` — the code that generated them, committed alongside so every artifact is reproducible.

Every artifact task is a commit; `git log` is the audit trail.
"""

_GITIGNORE = """__pycache__/
*.py[cod]
.ipynb_checkpoints/
.mplcache/
*.tmp
"""


def kind_for(rel_path: str) -> str:
    """Best-guess artifact kind from the file extension."""
    return _KIND_BY_EXT.get(Path(rel_path).suffix.lower(), "other")


def _title_for(rel_path: str) -> str:
    return Path(rel_path).stem.replace("_", " ").replace("-", " ").strip() or rel_path


# ── user-data helpers (DESIGN_data_plane.md) — stdlib only, so the harness never needs pandas ──

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def _delimiter(path: Path) -> str:
    return "\t" if path.suffix.lower() in (".tsv", ".tab") else ","


def _tabular_shape(path: Path) -> tuple[list[str], int | None]:
    """(columns, data_row_count) for a delimited text file; ([], None) for anything else."""
    if path.suffix.lower() not in (".csv", ".tsv", ".tab", ".txt"):
        return [], None
    try:
        with open(path, encoding="utf-8", newline="", errors="replace") as f:
            r = csv.reader(f, delimiter=_delimiter(path))
            header = next(r, []) or []
            return [c.strip() for c in header], sum(1 for _ in r)
    except OSError:
        return [], None


def _head_rows(path: Path, n: int) -> list[str]:
    """The first n data rows, rendered compactly for a prompt. Truncated hard — the manifest is a
    shape description, not a data dump."""
    if n <= 0 or not Path(path).is_file() or Path(path).suffix.lower() not in (
            ".csv", ".tsv", ".tab", ".txt"):
        return []
    out: list[str] = []
    try:
        with open(path, encoding="utf-8", newline="", errors="replace") as f:
            r = csv.reader(f, delimiter=_delimiter(Path(path)))
            next(r, None)                                    # header already shown
            for row in r:
                out.append(" | ".join(str(c)[:40] for c in row[:12])[:300])
                if len(out) >= n:
                    break
    except OSError:
        return []
    return out


class Workspace:
    """A git repo at ``root``. Every method is best-effort: a missing/broken git must never take
    down a research run, so failures degrade to "no history" rather than raising."""

    def __init__(self, root):
        self.root = Path(root)

    # ── git plumbing ────────────────────────────────────────────────────────
    @staticmethod
    def git_available() -> bool:
        return shutil.which("git") is not None

    def _git(self, *args, timeout: int = 30, stdin: str | None = None
             ) -> subprocess.CompletedProcess | None:
        if not self.git_available() or not self.root.is_dir():
            return None
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"          # never block on a credential prompt
        try:
            return subprocess.run(["git", *args], cwd=str(self.root), env=env, input=stdin,
                                  capture_output=True, text=True, timeout=timeout)
        except (OSError, subprocess.SubprocessError):
            return None

    def is_repo(self) -> bool:
        r = self._git("rev-parse", "--git-dir")
        return bool(r and r.returncode == 0)

    def head(self) -> str | None:
        r = self._git("rev-parse", "HEAD")
        return r.stdout.strip() if r and r.returncode == 0 else None

    # ── lifecycle ───────────────────────────────────────────────────────────
    def init(self, question: str = "") -> bool:
        """Create the workspace and (if git is present) make it a repo with a first commit.
        Idempotent — safe to call again on every resume. Returns True if it is a git repo."""
        for sub in ("", DATA, INPUTS, ARTIFACTS, SCRIPTS):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        readme = self.root / "README.md"
        if not readme.exists():
            readme.write_text(_README.format(question=(question or "").strip()[:300]), encoding="utf-8")
        gi = self.root / ".gitignore"
        if not gi.exists():
            gi.write_text(_GITIGNORE, encoding="utf-8")
        for sub in (INPUTS, ARTIFACTS, SCRIPTS):  # keep empty dirs in the tree
            keep = self.root / sub / ".gitkeep"
            if not keep.exists():
                keep.write_text("", encoding="utf-8")
        if self.is_repo():
            return True
        if not self.git_available():
            return False
        r = self._git("init", "-b", "main")
        if not r or r.returncode != 0:
            r = self._git("init")                 # older git: no -b
        if not r or r.returncode != 0:
            return False
        # Local identity so commits work regardless of the host's global git config, and no
        # signing so a configured gpg key can never hang the run waiting for a passphrase.
        self._git("config", "--local", "user.name", "methodology-v2 agent")
        self._git("config", "--local", "user.email", "agent@methodology-v2.local")
        self._git("config", "--local", "commit.gpgsign", "false")
        self.commit("workspace: initialise")
        return self.is_repo()

    def commit(self, message: str) -> str | None:
        """Stage everything and commit. Returns the new sha, or None if git is unavailable or
        there was nothing to commit."""
        if not self.is_repo():
            return None
        self._git("add", "-A")
        r = self._git("diff", "--cached", "--quiet")
        if r is not None and r.returncode == 0:
            return None                            # nothing staged → nothing to commit
        c = self._git("commit", "-m", message[:400] or "workspace: update")
        if not c or c.returncode != 0:
            return None
        return self.head()

    def log(self, n: int = 40) -> list[dict]:
        """Recent commits, newest first: {sha, short, ts, subject}."""
        r = self._git("log", f"-{max(1, int(n))}", "--pretty=format:%H%x1f%h%x1f%ct%x1f%s")
        if not r or r.returncode != 0:
            return []
        out = []
        for line in r.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 4:
                out.append({"sha": parts[0], "short": parts[1],
                            "ts": int(parts[2]) if parts[2].isdigit() else 0, "subject": parts[3]})
        return out

    # ── change detection (works with or without git) ─────────────────────────
    def snapshot(self) -> dict:
        """{relpath: (mtime_ns, size)} for every tracked-able file. Used to find what a task
        produced — the filesystem is the source of truth, not the model's declaration."""
        snap: dict[str, tuple] = {}
        if not self.root.is_dir():
            return snap
        for p in self.root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(self.root)
            if set(rel.parts[:-1]) & _SKIP_DIRS:      # a cache DIRECTORY, not a file named like one
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            snap[rel.as_posix()] = (st.st_mtime_ns, st.st_size)
        return snap

    def changed(self, before: dict) -> list[str]:
        """Files added or modified since `before` (a snapshot), newest-first-ish by path order."""
        now = self.snapshot()
        return sorted(rel for rel, meta in now.items() if before.get(rel) != meta)

    def ignored(self, paths: list[str]) -> set[str]:
        """The subset of `paths` git would ignore — including anything the AGENT added to
        .gitignore during its build. Empty when git is unavailable."""
        if not paths or not self.is_repo():
            return set()
        r = self._git("check-ignore", "--stdin", stdin="\n".join(paths) + "\n")
        if not r or r.returncode > 1:      # 0 = some ignored, 1 = none, >1 = error
            return set()
        return {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}

    def artifact_paths(self, changed: list[str]) -> list[str]:
        """The subset of changed files that count as deliverables. Excludes the harness-owned
        directories, placeholders, and anything gitignored — a build that imports matplotlib drops
        a font cache in the workspace, and that is not something the agent produced."""
        out = []
        for rel in changed:
            if rel.endswith("/.gitkeep") or rel == ".gitkeep":
                continue
            if any(rel == p or rel.startswith(p) for p in _NOT_ARTIFACTS):
                continue
            out.append(rel)
        skip = self.ignored(out)
        return [rel for rel in out if rel not in skip]

    def stat(self, rel: str) -> dict:
        p = self.root / rel
        try:
            st = p.stat()
            return {"bytes": st.st_size, "mtime": int(st.st_mtime)}
        except OSError:
            return {"bytes": 0, "mtime": 0}

    # ── the data export: the ledger, as files the agent can compute over ─────
    def export(self, ledger, *, run_meta: dict | None = None, report: str = "") -> list[str]:
        """Write the belief state into ``data/`` as JSON + CSV. Overwritten on every call so the
        agent always computes over the CURRENT ledger. Returns the relative paths written."""
        d = self.root / DATA
        d.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        def _w(name: str, text: str) -> None:
            (d / name).write_text(text, encoding="utf-8")
            written.append(f"{DATA}/{name}")

        pool = sorted(ledger.pool(), key=lambda h: -h.confidence)
        binned = sorted(ledger.binned(), key=lambda h: -h.confidence)
        untested = ledger.pending_screen() + ledger.pending_deep()
        ordered = pool + binned + untested

        findings, frows, erows, mrows = [], [], [], []
        for h in ordered:
            sup, con = ledger.support_balance(h)
            dirn = ledger.directions.get(h.direction_id or "")
            evs = ledger.evidence_for(h)
            nums: dict[str, object] = {}
            for ev in evs:
                nums.update(ev.numbers)
            findings.append({
                "id": h.id, "status": h.status, "verdict": h.verdict,
                "confidence": round(float(h.confidence), 4), "aspects": list(h.aspects),
                "text": h.text, "rationale": h.rationale, "bin_reason": h.bin_reason,
                "conflicts": list(h.conflicts), "origin": h.origin, "pinned": bool(h.pinned),
                "direction": {"id": h.direction_id or "",
                              "question": dirn.question_text if dirn else ""},
                "support": {"for": sup, "against": con},
                "numbers": nums,
                "evidence": [{
                    "id": ev.id, "stance": ev.stance, "phase": ev.phase, "text": ev.text,
                    "numbers": ev.numbers,
                    "source": {"title": ev.source.title, "authors": list(ev.source.authors),
                               "year": ev.source.year, "journal": ev.source.journal,
                               "doi": ev.source.doi, "pmid": ev.source.pmid,
                               "pmc": ev.source.pmc, "url": ev.source.url,
                               "verified": bool(ev.source.verified)},
                } for ev in evs],
            })
            frows.append([h.id, h.status, h.verdict, round(float(h.confidence), 4),
                          "; ".join(h.aspects), h.text, h.rationale, h.bin_reason,
                          sup, con, len(evs), h.direction_id or "",
                          dirn.question_text if dirn else "",
                          json.dumps(nums, ensure_ascii=False) if nums else ""])
            for ev in evs:
                s = ev.source
                loc = s.doi or (f"PMID:{s.pmid}" if s.pmid else "") or s.pmc or s.url or ""
                erows.append([ev.id, h.id, h.text, ev.stance, ev.phase, ev.text, s.title,
                              "; ".join(s.authors), s.year or "", s.journal or "", s.doi or "",
                              s.pmid or "", s.pmc or "", s.url or "",
                              json.dumps(ev.numbers, ensure_ascii=False) if ev.numbers else ""])
                for metric, value in (ev.numbers or {}).items():
                    mrows.append([metric, value, h.id, h.text, h.status, h.verdict,
                                  "; ".join(h.aspects), ev.id, ev.stance, s.title,
                                  (s.authors[0] if s.authors else ""), s.year or "", loc])

        _w("findings.json", json.dumps({
            "question": ledger.question,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "required_fields": list(ledger.required_fields),
            "constraints": list(ledger.constraints),
            "assumptions": list(ledger.assumptions),
            "glossary": dict(ledger.glossary or {}),
            "counts": {"pooled": len(pool), "binned": len(binned), "untested": len(untested),
                       "evidence": len(ledger.evidence), "directions": len(ledger.directions)},
            "findings": findings,
            "patterns": list(ledger.patterns or []),
        }, indent=2, ensure_ascii=False))

        _csv(d / "findings.csv", written,
             ["hypothesis_id", "status", "verdict", "confidence", "aspects", "hypothesis",
              "rationale", "bin_reason", "sources_for", "sources_against", "n_evidence",
              "direction_id", "direction", "numbers_json"], frows)
        _csv(d / "evidence.csv", written,
             ["evidence_id", "hypothesis_id", "hypothesis", "stance", "phase", "quote",
              "source_title", "authors", "year", "journal", "doi", "pmid", "pmc", "url",
              "numbers_json"], erows)
        # Long format — one row per reported number. This is the "all the benchmarks" table.
        _csv(d / "metrics.csv", written,
             ["metric", "value", "hypothesis_id", "hypothesis", "status", "verdict", "aspects",
              "evidence_id", "stance", "source_title", "first_author", "year", "locator"], mrows)

        _w("question.txt", (ledger.question or "").strip() + "\n")
        if run_meta:
            _w("run.json", json.dumps(run_meta, indent=2))
        if report:
            _w("report.md", report)
        return written

    # ── the user's own data (DESIGN_data_plane.md §4.2) ──────────────────────
    def add_inputs(self, paths: list[str]) -> list[dict]:
        """Copy the researcher's data files into ``inputs/`` and describe each one.

        Returns one record per file: {dataset_id, name, path, bytes, sha256, columns, rows}.
        ``dataset_id`` is ``name@<12-hex digest>`` — content-addressed, so a claim's provenance
        pins the exact bytes it was computed from and a changed file is a different dataset
        rather than a silent redefinition of the old one."""
        dst = self.root / INPUTS
        dst.mkdir(parents=True, exist_ok=True)
        out: list[dict] = []
        for src in paths or []:
            p = Path(src).expanduser()
            if not p.is_file():
                continue
            target = dst / p.name
            if target.resolve() != p.resolve():
                shutil.copy2(p, target)
            digest = _sha256(target)
            cols, rows = _tabular_shape(target)
            out.append({"dataset_id": f"{p.name}@{digest[:12]}", "name": p.name,
                        "path": f"{INPUTS}/{p.name}", "bytes": target.stat().st_size,
                        "sha256": digest, "columns": cols, "rows": rows})
        return out

    def inputs_manifest(self, datasets: list[dict] | None = None, head: int = 3) -> str:
        """What the agent is told about the user's data: shape and a few sample rows — never the
        whole file. Enough to write a correct query without paying to read a large file into
        context on every call (DESIGN_data_plane.md §4.2)."""
        recs = datasets if datasets is not None else []
        if not recs:
            d = self.root / INPUTS
            if not d.is_dir():
                return "(no input data)"
            recs = [{"name": p.name, "path": f"{INPUTS}/{p.name}", "dataset_id": p.name,
                     "columns": _tabular_shape(p)[0], "rows": _tabular_shape(p)[1]}
                    for p in sorted(d.iterdir()) if p.is_file()]
        if not recs:
            return "(no input data)"
        lines = []
        for r in recs:
            shape = ""
            if r.get("rows") is not None:
                shape = f" — {r['rows']} rows x {len(r.get('columns') or [])} columns"
            lines.append(f"  {r['path']}{shape}   [dataset_id: {r.get('dataset_id', '')}]")
            if r.get("columns"):
                lines.append(f"      columns: {', '.join(r['columns'])}")
            for row in _head_rows(self.root / r["path"], head):
                lines.append(f"      | {row}")
        return "\n".join(lines)

    def data_manifest(self) -> str:
        """A one-line-per-file description of ``data/`` with row counts, for the artifact prompt."""
        d = self.root / DATA
        if not d.is_dir():
            return "(no data exported yet)"
        rows = []
        for p in sorted(d.iterdir()):
            if not p.is_file():
                continue
            note = ""
            if p.suffix == ".csv":
                try:
                    with open(p, encoding="utf-8", newline="") as f:
                        n = sum(1 for _ in f) - 1
                    hdr = ""
                    with open(p, encoding="utf-8", newline="") as f:
                        hdr = (f.readline() or "").strip()
                    note = f" — {max(0, n)} rows; columns: {hdr}"
                except OSError:
                    pass
            else:
                note = f" — {p.stat().st_size // 1024}KB" if p.stat().st_size > 2048 else ""
            rows.append(f"  {DATA}/{p.name}{note}")
        return "\n".join(rows) or "(no data exported yet)"

    # ── the artifact index ──────────────────────────────────────────────────
    def write_index(self, artifacts: list[dict]) -> None:
        """Human-readable index, committed with the artifacts themselves."""
        lines = ["# Artifacts", ""]
        if not artifacts:
            lines.append("_None yet. Ask the agent for one — e.g. \"give me a CSV of every "
                         "benchmark number\" or \"plot the AUCs by marker\"._")
        for a in artifacts:
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(a.get("created") or 0))
            lines.append(f"- **{a.get('title') or a['path']}** — `{a['path']}` "
                         f"({a.get('kind', 'other')}, {when})")
            if a.get("description"):
                lines.append(f"  - {a['description']}")
            if a.get("request"):
                lines.append(f"  - requested: {a['request']}")
        (self.root / INDEX_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _csv(path: Path, written: list[str], header: list[str], rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(["" if v is None else v for v in r])
    written.append(f"{DATA}/{path.name}")


def build_records(ws: Workspace, paths: list[str], *, request: str, declared: list[dict] | None,
                  commit: str | None, auto: bool = False) -> list[dict]:
    """Turn the files a task produced into artifact index records. The FILES decide what exists;
    the model's `declared` metadata only supplies nicer titles/descriptions where the paths match."""
    meta = {}
    for d in (declared or []):
        p = str(d.get("path", "")).strip().lstrip("./")
        if p:
            meta[p] = d
    out = []
    for rel in paths:
        m = meta.get(rel, {})
        st = ws.stat(rel)
        out.append({
            "path": rel,
            "title": str(m.get("title") or "").strip() or _title_for(rel),
            "kind": str(m.get("kind") or "").strip() or kind_for(rel),
            "description": str(m.get("description") or "").strip(),
            "request": request,
            "auto": bool(auto),
            "commit": commit or "",
            "created": st["mtime"] or int(time.time()),
            "bytes": st["bytes"],
        })
    return out
