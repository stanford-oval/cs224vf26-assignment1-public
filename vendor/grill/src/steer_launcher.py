#!/usr/bin/env python3
"""Host-side launcher daemon for steerable methodology-v2 runs (DESIGN_interactive.md, Phase 5).

The portal runs in a container where codex can't execute (no codex binary; its sandbox can't nest).
This daemon runs on the HOST — where codex works — and watches a launch queue on the shared
`extracted/` volume. The portal's `POST /api/steer/new` drops a request JSON into the queue; this
daemon spawns `python -m src.cli` into a run-dir with a steer inbox, so the whole run is steerable
from the portal console (and streams its ledger/activity/trajectory back to it).

    python3 -m src.steer_launcher \
        --steer-root /srv/services/sliders-portal/extracted/steer_runs

Queue layout under <steer-root>/_queue/: `*.json` = pending requests; `done/`, `bad/` = archived.
A run-dir gets a `launch.json` ({pid,status,cmd}) so the portal can show launch state.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from . import codex_exec, config

REPO = Path(__file__).resolve().parent.parent      # graph-search-sliders (cwd for `python -m src.cli`)
DEFAULT_PY = config.VENV_PYTHON
_SLUG_RE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")


_ASSIST_SYS = """You are the research assistant for a scientist's own workspace on the Oval portal.

You answer from the FILES IN THIS DIRECTORY ONLY. They are that user's investigations — nothing
else. Do not read anything outside this directory, and never guess at what other users may have.

Layout — every text file here is a REAL file, so grep/rg/find all work normally:

  INDEX.md                     every investigation, its topic, status and key terms — READ FIRST
  runs/<slug>/
    00-QUESTION.txt            the research question this investigation set out to answer
    01-REPORT.md               the written report (absent if it hasn't finished one)
    02-FINDINGS.md             EVERY hypothesis: verdict, confidence, and its evidence.
                               This is the searchable substance — one block per finding.
    03-SOURCES.md              the bibliography
    files/                     charts, CSVs and the researcher's uploaded data (may be a link)
  investigations/<slug>/       older investigations (SQLite + exported reports)

TO FIND WHICH INVESTIGATION MENTIONS SOMETHING — a gene, marker, drug, method, author — search
the whole tree first, then open only what matched:

    grep -rin "FOXG1" runs/ | head -40
    grep -rln "FOXG1" runs/            # just which investigations

Do that before concluding anything is absent. A term can appear in a report, in a finding, or only
in a source title, and each means something different — say which.

How to answer:
  * Ground every claim in a file you actually read. Name the run by its slug, like (run-ed9c3573)
    — slugs are turned into links to that report for the reader, so write them plainly rather than
    as a path or a URL, and name the run whenever you use something from it. For an older
    investigation, put its slug in `backticks` so it links too.
    Say which file a claim came from when that matters.
  * Distinguish supported from contested: a hypothesis is supported, conflicted, refuted, or
    untested, and 02-FINDINGS.md records which, with the evidence each way.
  * If the files genuinely don't answer it, say so and say what is missing. Never invent a
    finding, a number, or a citation.
  * Be concise and concrete. Markdown. No preamble, no restating the question.
"""


_VERDICT_WORD = {"supported": "SUPPORTED", "conflicted": "CONTESTED",
                 "refuted": "REFUTED", "": "UNTESTED", None: "UNTESTED"}


def _findings_md(led: dict, slug: str) -> tuple[str, list[str]]:
    """A greppable digest of the ledger: one block per hypothesis with its verdict and the evidence
    for and against. ledger.json is a 150KB single-line blob that no grep can usefully hit; this is
    the file that makes 'which investigation mentions FOXG1' actually work.

    Returns (markdown, key_terms)."""
    hyps = led.get("hypotheses") or {}
    hyps = list(hyps.values()) if isinstance(hyps, dict) else list(hyps)
    ev = led.get("evidence") or {}
    ev = ev if isinstance(ev, dict) else {str(e.get("id")): e for e in ev if isinstance(e, dict)}
    by_hyp: dict = {}
    for e in ev.values():
        if isinstance(e, dict) and e.get("hypothesis_id"):
            by_hyp.setdefault(e["hypothesis_id"], []).append(e)
    order = {"pooled": 0, "screened": 1, "proposed": 2, "binned": 3}
    hyps.sort(key=lambda h: (order.get(h.get("status"), 9), -(h.get("confidence") or 0)))
    terms: dict = {}
    out = [f"# Findings — {slug}", "",
           f"{len(hyps)} hypotheses. Verdicts: SUPPORTED (evidence supports it), CONTESTED (real "
           f"support and real contradiction), REFUTED (no support / contradicted), UNTESTED "
           f"(proposed but never tested).", ""]
    for h in hyps:
        if not isinstance(h, dict):
            continue
        v = _VERDICT_WORD.get(h.get("verdict") or ("" if h.get("status") in ("proposed", "screened") else h.get("status")), "UNTESTED")
        conf = h.get("confidence")
        out.append(f"## [{v}] {h.get('id', '?')}"
                   + (f"  (confidence {round(conf * 100)}%)" if isinstance(conf, (int, float)) else ""))
        out.append(h.get("text") or "")
        for a in (h.get("aspects") or []):
            terms[str(a)] = terms.get(str(a), 0) + 1
        if h.get("aspects"):
            out.append(f"Aspects: {', '.join(str(a) for a in h['aspects'])}")
        why = h.get("bin_reason") or h.get("screen_note") or ""
        if why:
            out.append(f"Why this verdict: {why}")
        items = []
        for eid in (h.get("evidence_ids") or []):
            if eid in ev:
                items.append(ev[eid])
        seen = {id(x) for x in items}
        items += [e for e in by_hyp.get(h.get("id"), []) if id(e) not in seen]
        for stance, label in (("supports", "FOR"), ("contradicts", "AGAINST"), ("neutral", "CONTEXT")):
            rows = [e for e in items if (e.get("stance") or "neutral") == stance]
            for e in rows[:12]:
                src = e.get("source") or {}
                au = (src.get("authors") or [None])[0] or ""
                cite = " ".join(x for x in [au, f"({src.get('year')})" if src.get("year") else "",
                                            src.get("title") or ""] if x)
                out.append(f"- {label}: {(e.get('text') or '')[:400]}  [{cite.strip()}]")
        out.append("")
    top = [t for t, _ in sorted(terms.items(), key=lambda kv: -kv[1])[:8]]
    return "\n".join(out) + "\n", top


def _build_run(src: Path, dst: Path) -> dict:
    """Materialise one investigation as REAL text files. Symlinked directories are invisible to
    grep -r, rg and find, so anything the assistant must search is copied, not linked; only the
    bulky binary artifacts stay as a link."""
    dst.mkdir(parents=True, exist_ok=True)
    meta = {"question": "", "terms": [], "has_report": False, "n_hyp": 0}
    led = {}
    try:
        led = json.loads((src / "ledger.json").read_text(encoding="utf-8"))
    except Exception:
        led = {}
    q = led.get("question") or ""
    if not q:
        try:
            q = json.loads((src / "launch.json").read_text(encoding="utf-8")).get("question") or ""
        except Exception:
            q = ""
    meta["question"] = q
    (dst / "00-QUESTION.txt").write_text((q or "(unknown)") + "\n", encoding="utf-8")
    rep = src / "answer.md"
    if rep.is_file():
        try:
            shutil.copyfile(rep, dst / "01-REPORT.md")
            meta["has_report"] = True
        except OSError:
            pass
    if led:
        try:
            md, terms = _findings_md(led, src.name)
            (dst / "02-FINDINGS.md").write_text(md, encoding="utf-8")
            meta["terms"] = terms
            h = led.get("hypotheses") or {}
            meta["n_hyp"] = len(h if isinstance(h, dict) else list(h))
        except Exception:
            pass
    # the bibliography already sits at the end of the report; also expose it standalone when present
    for name, out in (("references.md", "03-SOURCES.md"),):
        p = src / name
        if p.is_file():
            try:
                shutil.copyfile(p, dst / out)
            except OSError:
                pass
    # data + artifacts: linked, not copied (charts and CSVs can be large and are not searched)
    for sub, link in (("workspace/artifacts", "files"), ("workspace/inputs", "my-data"),
                      ("uploads", "my-uploads")):
        p = src / sub
        if p.is_dir():
            try:
                (dst / link).symlink_to(p, target_is_directory=True)
            except OSError:
                pass
    return meta


def _ask_view(req: dict, steer_root: Path, work: Path) -> int:
    """Materialise the searchable view: one real directory per investigation the user may see,
    plus an INDEX.md that lets the assistant pick targets without opening everything."""
    runs_dir, inv_dir = work / "runs", work / "investigations"
    runs_dir.mkdir(parents=True, exist_ok=True)
    extracted = steer_root.parent                     # …/extracted
    # `focus` is the run the user happens to be looking at. It is a HINT, never a filter: a
    # workspace question ("how many investigations do I have?") asked from a run page must still
    # see the whole workspace, or the assistant answers truthfully about a view we secretly
    # narrowed.
    focus = str(req.get("focus") or "").strip()
    wanted = [str(s) for s in (req.get("runs") or [])]
    if focus and focus not in wanted:
        wanted.append(focus)
    rows, n = [], 0
    for slug in wanted:
        if not slug or ".." in slug or not _SLUG_RE.match(slug):
            continue
        src = steer_root / slug
        if not src.is_dir():
            continue
        try:
            meta = _build_run(src, runs_dir / slug)
        except Exception:
            continue
        rows.append((slug, meta))
        n += 1
    # investigations arrive as {slug,label} (older senders sent bare slugs — accept both)
    inv_items = []
    for x in (req.get("investigations") or []):
        if isinstance(x, dict):
            sl, lb = str(x.get("slug") or "").strip(), str(x.get("label") or "").strip()
        else:
            sl, lb = str(x).strip(), ""
        if sl:
            inv_items.append((sl, lb))
    n_inv_total = len(inv_items)
    lines = ["# What you can see", "",
             "Every investigation this user has access to — nothing else exists for you.", ""]
    if focus:
        # the focus may be a steerable run or one of the older investigations — name it correctly
        where = f"runs/{focus}" if any(sl == focus for sl, _ in rows) else f"investigations/{focus}"
        lines += [f"The user is reading **`{where}`** right now. If the question says \"this\", "
                  f"\"here\", \"this report\" or \"the run\" — or is plainly about what they are "
                  f"looking at — they mean that one, so answer from it first and say so. Anything "
                  f"broader should still be answered across everything below.", ""]
    lines += [f"**Totals: {len(rows)} steerable investigations** (each with its own research "
              f"question, all listed in the table below) **and {n_inv_total} older investigations.** "
              f"These totals are authoritative — use them for counting questions rather than "
              f"counting directories, since only some older investigations are linked here.", "",
              "To find which one mentions a gene, marker, drug or method:", "",
              "    grep -rin \"<term>\" runs/ | head -40", "",
              "| investigation | topic | findings | report | recurring themes |",
              "|---|---|---|---|---|"]
    for slug, m in rows:
        q = (m["question"] or "(unknown)").replace("|", "/")
        here = " ← currently open" if slug == focus else ""
        lines.append(f"| `runs/{slug}`{here} | {q[:110]} | {m['n_hyp'] or '—'} | "
                     f"{'yes' if m['has_report'] else 'not yet'} | {', '.join(m['terms'][:5]) or '—'} |")
    if True:
        inv_dir.mkdir(parents=True, exist_ok=True)
        shown, cap = 0, 40
        for slug, _lb in inv_items:
            if shown >= cap:
                break
            if ".." in slug or not _SLUG_RE.match(slug):
                continue
            for cand in (extracted / f"{slug}_db", extracted / slug):
                if cand.is_dir():
                    try:
                        (inv_dir / slug).symlink_to(cand, target_is_directory=True)
                    except OSError:
                        break
                    shown += 1
                    n += 1
                    break
        if inv_items:
            linked = {p.name for p in inv_dir.iterdir()} if inv_dir.is_dir() else set()
            lines += ["", f"### Older investigations ({n_inv_total})", "",
                      "Every one is named here, so they can be counted and searched by topic. Their "
                      "directories are SQLite-backed; the ones marked (linked) are under "
                      "`investigations/` and need `grep -R` to search, the rest are listed by name "
                      "only — say so if a question would need their contents.", ""]
            for sl, lb in inv_items:
                mark = " (linked)" if sl in linked else ""
                lines.append(f"- `{sl}`{mark} — {lb or '(untitled)'}")
    (work / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return n


def _ask(aid: str, assist_root: Path, steer_root: Path, log) -> dict:
    """Answer one meta-assistant question with a read-only codex over the user's own files."""
    if not aid or ".." in aid or not _SLUG_RE.match(aid):
        raise ValueError(f"bad id {aid!r}")
    d = assist_root / aid
    req = json.loads((d / "request.json").read_text(encoding="utf-8"))
    work = d / "view"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    n = _ask_view(req, steer_root, work)
    (d / "progress.txt").write_text(f"reading {n} investigation(s)…", encoding="utf-8")
    hist = ""
    for h in (req.get("history") or []):
        role = "You" if (h.get("role") == "user") else "Assistant"
        hist += f"\n{role}: {str(h.get('text') or '')[:1500]}"
    prompt = _ASSIST_SYS
    if hist:
        prompt += f"\n\nEarlier in this conversation:{hist}\n"
    prompt += f"\n\nQUESTION: {req.get('question', '')}\n"
    env = os.environ.copy()
    codex_exec.load_env(str(config.ENV_FILE), env)
    cmd = ["codex", "exec", "--skip-git-repo-check", "--cd", str(work), "--sandbox", "read-only"]
    for c in codex_exec.PROVIDER:                 # Stanford proxy, same provider the agent uses
        cmd += ["-c", c]
    model = getattr(config, "ASSIST_MODEL", "") or getattr(config, "RUN_MODEL", "")
    if model:
        cmd += ["-m", model]
    t0 = time.time()
    status, answer, err = "done", "", ""
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           cwd=str(work), env=env, timeout=600)
        answer = _clean_codex_output(p.stdout or "")
        if not answer.strip():
            status, err = "error", (p.stdout or p.stderr or "codex produced no output")[-600:]
    except subprocess.TimeoutExpired:
        status, err = "error", "timed out after 10 minutes"
    except Exception as e:  # noqa: BLE001
        status, err = "error", f"{type(e).__name__}: {e}"
    usd = 0.0
    try:
        usd = codex_exec.spent_usd(work, since=t0)
    except Exception:  # noqa: BLE001
        pass
    res = {"status": status, "answer": answer, "error": err,
           "seconds": round(time.time() - t0, 1), "usd": round(usd, 4)}
    (d / "answer.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    req["status"] = status
    (d / "request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)       # the view is disposable; the answer is the artifact
    log(f"ask {aid}: {status} in {res['seconds']}s ${res['usd']:.3f} over {n} item(s)")
    return res


_CODEX_NOISE = re.compile(r"^\s*(\[[\d:T\-]+\]|OpenAI Codex|--------|workdir:|model:|provider:|"
                          r"approval:|sandbox:|reasoning |tokens used|user\b|thinking\b)", re.I)


def _clean_codex_output(raw: str) -> str:
    """codex exec prints a session banner and its own trace around the answer; keep the answer."""
    lines = [ln for ln in (raw or "").splitlines() if not _CODEX_NOISE.match(ln)]
    txt = "\n".join(lines).strip()
    # the final assistant turn is what we want; codex separates turns with a rule
    if "\ncodex\n" in txt:
        txt = txt.rsplit("\ncodex\n", 1)[-1].strip()
    return txt


def _launch(req: dict, steer_root: Path, py: str) -> dict:
    slug = str(req.get("slug") or "").strip()
    if not slug or ".." in slug or not _SLUG_RE.match(slug):
        raise ValueError(f"bad slug {slug!r}")
    question = str(req.get("question") or "").strip()
    if not question:
        raise ValueError("empty question")
    run_dir = steer_root / slug
    run_dir.mkdir(parents=True, exist_ok=True)
    inbox = run_dir / "steer_inbox.json"
    if not inbox.exists():
        inbox.write_text("[]", encoding="utf-8")
    cmd = [py, "-m", "src.cli",
           "--question", question,
           "--run-dir", str(run_dir),
           "--steer-inbox", str(inbox),
           "--budget", str(float(req.get("budget", 15.0))),
           "-K", str(int(req.get("K", 5))),
           "--alloc-ceiling-frac", str(float(req.get("alloc_ceiling_frac", 0.40))),
           "--max-rounds", str(int(req.get("max_rounds", 30))),
           "--model", str(req.get("model", config.RUN_MODEL)),
           "--reasoning", str(req.get("reasoning", config.REASONING)),
           "--sources", ",".join(req.get("sources") or [])]
    logf = open(run_dir / "launch.out", "a", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT,
                            start_new_session=True)   # detach: survives the daemon
    meta = {"pid": proc.pid, "slug": slug, "question": question,
            "status": "running", "budget": float(req.get("budget", 15.0)),
            "started_at": time.time(),   # epoch — drives the elapsed timer in the console
            "requested_by": req.get("requested_by"), "cmd": cmd}
    (run_dir / "launch.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def _pid_alive(pid) -> bool:
    try:
        pid = int(pid)
        os.kill(pid, 0)
    except (OSError, ValueError, TypeError):
        return False
    try:   # a finished-but-unreaped child is a ZOMBIE — os.kill(...,0) still succeeds; treat it as dead
        with open(f"/proc/{pid}/stat", encoding="utf-8") as f:
            state = f.read().rsplit(")", 1)[1].split()[0]
        return state != "Z"
    except OSError:
        return True


def _resume(slug: str, steer_root: Path) -> dict:
    """Continue a FINISHED run so it drains a steer the user sent after it converged. Re-runs the run's
    original command with --resume (budget.total is restored from saved state; the steer re-opens the
    loop). Guarded: if a live process for the run already exists, do nothing."""
    if not slug or ".." in slug or not _SLUG_RE.match(slug):
        raise ValueError(f"bad slug {slug!r}")
    run_dir = steer_root / slug
    lj = run_dir / "launch.json"
    if not lj.exists():
        raise ValueError(f"no launch.json for {slug}")
    meta = json.loads(lj.read_text(encoding="utf-8"))
    if _pid_alive(meta.get("pid")):
        return {"slug": slug, "skipped": "already running"}
    cmd = list(meta.get("cmd") or [])
    if not cmd:
        raise ValueError("no original cmd to resume")
    if "--resume" not in cmd:
        cmd = cmd + ["--resume"]
    logf = open(run_dir / "launch.out", "a", encoding="utf-8")
    proc = subprocess.Popen(cmd, cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT,
                            start_new_session=True)
    meta.update({"pid": proc.pid, "status": "running", "started_at": time.time(), "cmd": cmd})
    lj.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {"slug": slug, "pid": proc.pid}


def _scan_asks(assist_root: Path, steer_root: Path, log) -> int:
    """Meta-assistant questions: one read-only codex per question, answered in place."""
    q = assist_root / "_queue"
    if not q.is_dir():
        return 0
    done, bad = q / "done", q / "bad"
    done.mkdir(exist_ok=True)
    bad.mkdir(exist_ok=True)
    n = 0
    for rp in sorted(q.glob("*.json")):
        aid = rp.stem
        try:
            _ask(aid, assist_root, steer_root, log)
            rp.rename(done / rp.name)
            n += 1
        except Exception as e:  # noqa: BLE001 — one bad question must not stop the daemon
            log(f"ask failed for {rp.name}: {type(e).__name__}: {e}")
            try:
                (assist_root / aid).mkdir(parents=True, exist_ok=True)
                (assist_root / aid / "answer.json").write_text(
                    json.dumps({"status": "error", "answer": "",
                                "error": f"{type(e).__name__}: {e}"}), encoding="utf-8")
            except OSError:
                pass
            rp.rename(bad / rp.name)
    return n


def _scan_once(queue: Path, steer_root: Path, py: str, log) -> int:
    done, bad = queue / "done", queue / "bad"
    done.mkdir(exist_ok=True)
    bad.mkdir(exist_ok=True)
    n = 0
    # Resume requests (from the portal when a steer lands on a finished run that still has budget).
    rq = queue / "_resume"
    if rq.is_dir():
        for rp in sorted(rq.glob("*.json")):
            try:
                res = _resume(rp.stem, steer_root)
                log(f"resume {rp.stem}: " + (res["skipped"] if res.get("skipped") else f"pid={res.get('pid')}"))
                rp.rename(done / ("resume-" + rp.name))
                n += 1
            except Exception as e:  # noqa: BLE001
                log(f"resume failed for {rp.name}: {e}")
                rp.rename(bad / ("resume-" + rp.name))
    for req_path in sorted(queue.glob("*.json")):
        try:
            req = json.loads(req_path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            log(f"bad request {req_path.name}: {e}")
            req_path.rename(bad / req_path.name)
            continue
        try:
            meta = _launch(req, steer_root, py)
            log(f"launched {meta['slug']} pid={meta['pid']} budget=${meta['budget']}")
            req_path.rename(done / req_path.name)
            n += 1
        except Exception as e:  # noqa: BLE001
            log(f"launch failed for {req_path.name}: {e}")
            req_path.rename(bad / req_path.name)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Host launcher daemon for steerable methodology-v2 runs")
    ap.add_argument("--steer-root", required=True, help="the steer_runs dir on the shared volume")
    ap.add_argument("--python", default=DEFAULT_PY, help="interpreter to run the agent with")
    ap.add_argument("--interval", type=float, default=3.0, help="poll seconds")
    ap.add_argument("--once", action="store_true", help="scan once and exit (for testing)")
    ap.add_argument("--assistant-root", default="",
                    help="meta-assistant queue dir (default: <steer-root>/../assistant)")
    a = ap.parse_args()

    # Auto-reap finished children so they don't linger as zombies (which would make the resume
    # "already running" guard falsely skip). Detached runs are unaffected.
    try:
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    except (ValueError, OSError):
        pass

    steer_root = Path(a.steer_root)
    queue = steer_root / "_queue"
    queue.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)

    assist_root = Path(a.assistant_root) if a.assistant_root else (steer_root.parent / "assistant")
    log(f"launcher watching {queue} (python={a.python}); assistant queue {assist_root / '_queue'}")
    if a.once:
        _scan_once(queue, steer_root, a.python, log)
        _scan_asks(assist_root, steer_root, log)
        return 0
    while True:
        try:
            _scan_once(queue, steer_root, a.python, log)
        except Exception as e:  # noqa: BLE001 — a bad scan must not kill the daemon
            log(f"scan error: {type(e).__name__}: {e}")
        try:
            _scan_asks(assist_root, steer_root, log)
        except Exception as e:  # noqa: BLE001
            log(f"assistant scan error: {type(e).__name__}: {e}")
        time.sleep(a.interval)


if __name__ == "__main__":
    raise SystemExit(main())
