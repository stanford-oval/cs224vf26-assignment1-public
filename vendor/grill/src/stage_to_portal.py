#!/usr/bin/env python3
"""Stage a Methodology-v2 run into the portal as a report-only investigation.

Converts a v2 run dir (answer.md + run.json + ledger.json + question.txt) into
extracted/<slug>_db/ with report.md, question.txt, and a v2-native activity.json
(summary + cost_curve + timeline + ledger) so the portal home-card stats and the
Activity tab render. No trajectory.json is emitted — the portal hides that tab when
`trajectory_graph` is absent from the server.py entry.

    python3 -m methodology_v2.stage_to_portal <run_dir> <slug> "<clean title>"
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/mnt/data/oval/report_formation")


import re

LOG_TEXT = ""   # set in main() from the run's orchestrator.log


def _timeline_from_log(text: str) -> list[dict]:
    """Parse orchestrator.log into a per-event timeline (INIT/EXPLORE round/ingest/
    VERIFY/checkpoint), with cumulative USD reconstructed from the explore/verify
    pool figures the log prints on each line."""
    rows, seq, cum = [], 0, 0.0
    last_expl, last_ver = 0.0, 0.0

    def add(kind, name, label, summary, cum_now, state=False):
        nonlocal seq
        seq += 1
        rows.append({"seq": seq, "kind": kind, "name": name, "label": label,
                     "summary": summary.strip(), "usd": round(max(0.0, cum_now - cum), 4),
                     "cum_usd": round(cum_now, 4), "state_update": state})

    for line in text.splitlines():
        m = re.search(r"\]\s*(.*)$", line)
        if not m:
            continue
        body = m.group(1)
        me = re.search(r"explore \$([\d.]+)/", body)
        mv = re.search(r"verify \$([\d.]+)/", body)
        if me:
            last_expl = float(me.group(1))
        if mv:
            last_ver = float(mv.group(1))
        cum_now = last_expl + last_ver
        if body.startswith("INIT spent"):
            add("state", "init", "INIT", body, float(re.search(r"\$([\d.]+)", body).group(1)))
        elif body.startswith("ROUND"):
            add("search", "explore", body.split("(")[0].strip(), body, cum_now)
        elif body.lstrip().startswith("+") and "claims" in body:
            add("notes", "ingest", "ingest claims", body, cum_now)
        elif "VERIFY drained" in body:
            add("think", "verify", "VERIFY", body, cum_now)
        elif body.startswith("CHECKPOINT"):
            add("state", "checkpoint", body.split(":")[0], body, cum_now, state=True)
        elif body.startswith("FINALIZE") or body.startswith("DONE"):
            add("state", "finalize", body.split(":")[0].split(" ")[0], body, cum_now, state=True)
        cum = cum_now
    return rows


def _src_key(s: dict) -> str | None:
    for k in ("doi", "pmid", "pmc", "url"):
        if s.get(k):
            return f"{k}:{str(s[k]).strip().lower()}"
    return (s.get("title") or "").strip().lower() or None


def build_activity(run: dict, ledger: dict, generated_at: str, task_dirs: list[str]) -> dict:
    b = run.get("budget", {})
    total = round(float(b.get("spent", 0.0)), 4)
    explore = round(float(b.get("explore", 0.0)), 4)
    verify = round(float(b.get("verify", 0.0)), 4)
    emb = round(float(b.get("embeddings", 0.0)), 4)

    claims = ledger.get("claims", {})
    all_src, conf_src = set(), set()
    for c in claims.values():
        for s in (c.get("evidence") or []):
            k = _src_key(s)
            if not k:
                continue
            all_src.add(k)
            if c.get("verification") == "confirmed":
                conf_src.add(k)

    # task counts by kind (from task dir names)
    def count(pred):
        return sum(1 for d in task_dirs if pred(d))
    n_verify = count(lambda d: "verify_" in d)
    n_explore = count(lambda d: "explore_" in d)
    n_other = len(task_dirs) - n_verify - n_explore

    by_kind = {
        "explore": {"usd": round(explore, 4), "count": n_explore + n_other, "color": "var(--blue)"},
        "verify": {"usd": round(verify, 4), "count": n_verify, "color": "var(--teal)"},
        "embeddings": {"usd": emb, "count": 1, "color": "var(--green)"},
    }
    summary = {
        "total_usd": total, "codex_usd": round(explore + verify, 4), "aux_usd": emb,
        "n_actions": len(task_dirs), "n_tool_calls": len(task_dirs),
        "by_kind": by_kind,
        "papers_read": len(conf_src), "papers_total": len(all_src),
        "generated_at": generated_at,
        "rounds": run.get("round"),
    }

    snaps = run.get("snapshots", [])
    cost_curve = [{"seq": i + 1, "cum_usd": round(float(s.get("cost", 0.0)), 4)}
                  for i, s in enumerate(snaps)]

    timeline = _timeline_from_log(LOG_TEXT) if LOG_TEXT else []
    if not timeline:                       # fallback: checkpoints only
        for i, s in enumerate(snaps, 1):
            timeline.append({
                "seq": i, "kind": "state", "name": "checkpoint", "label": f"checkpoint {i}",
                "summary": (
                    f"coverage={s.get('coverage', 0):.2f} quality={s.get('quality', 0):.2f} "
                    f"answeredness={s.get('answeredness', 0):.2f} claims={s.get('n_claims')}"
                    if "coverage" in s else
                    f"S={s.get('score', 0):.3f} Corr={s.get('corr', 0):.2f} claims={s.get('n_claims')}"),
                "usd": 0.0, "cum_usd": round(float(s.get("cost", 0.0)), 4), "state_update": True})

    # belief ledger view (confirmed findings as the locked beliefs)
    confirmed = [c for c in claims.values() if c.get("verification") == "confirmed"]
    findings = "\n".join(
        f"- {c.get('text','')}" for c in sorted(confirmed, key=lambda c: -c.get("confidence", 0))[:40])
    ledger_view = {
        "question": ledger.get("question", ""),
        "scope": "Methodology v2 — orchestrator-driven belief ledger; only source-verified "
                 "(CONFIRMED) claims are locked beliefs. " + (run.get("config", {}).get("rubric", "")),
        "confirmed_findings": findings,
        "counts": {"claims": len(claims), "confirmed": len(confirmed),
                   "refuted": sum(1 for c in claims.values() if c.get("verification") == "refuted"),
                   "directions": len(ledger.get("directions", {}))},
    }
    return {"summary": summary, "timeline": timeline, "cost_curve": cost_curve,
            "ledger": ledger_view, "ledger_versions": []}


def clean_report(answer_md: str, title: str) -> str:
    """Replace the giant question H1 with a clean title (the portal shows the question
    separately in its own callout)."""
    lines = answer_md.splitlines()
    if lines and lines[0].startswith("# "):
        lines[0] = f"# {title}"
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    run_dir = Path(sys.argv[1])
    slug = sys.argv[2]
    title = sys.argv[3]
    out = ROOT / "extracted" / f"{slug}_db"
    out.mkdir(parents=True, exist_ok=True)

    answer = (run_dir / "answer.md").read_text(encoding="utf-8")
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    ledger = json.loads((run_dir / "ledger.json").read_text(encoding="utf-8"))
    question = (run_dir / "question.txt").read_text(encoding="utf-8") if (run_dir / "question.txt").exists() \
        else run.get("question", "")
    if not question:
        question = ledger.get("question", "")

    (out / "report.md").write_text(clean_report(answer, title), encoding="utf-8")
    (out / "question.txt").write_text(question.strip() + "\n", encoding="utf-8")

    global LOG_TEXT
    log_p = run_dir / "orchestrator.log"
    LOG_TEXT = log_p.read_text(encoding="utf-8", errors="replace") if log_p.exists() else ""

    mtime = (run_dir / "answer.md").stat().st_mtime
    gen_at = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    task_dirs = [p.name for p in (run_dir / "tasks").glob("*")] if (run_dir / "tasks").exists() else []
    activity = build_activity(run, ledger, gen_at, task_dirs)
    (out / "activity.json").write_text(json.dumps(activity, indent=1), encoding="utf-8")

    # empty placeholder db so the _none.sqlite path resolves (report-only never opens it)
    (out / "_none.sqlite").touch()

    s = activity["summary"]
    print(f"staged {slug}: report {len(answer)//1024}KB, ${s['total_usd']} , "
          f"papers {s['papers_read']}/{s['papers_total']}, {len(task_dirs)} actions → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
