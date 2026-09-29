#!/usr/bin/env python3
"""Ask a question about a run — including one that has already finished.

    python3 -m src.qa --run-dir OUT --ask "what did you actually find on early-stage sensitivity?"
    python3 -m src.qa --run-dir OUT            # interactive, one question per line

The live steering console (`steer_server.py`) answers questions at round seams, but only while the
run is still going: after FINALIZE nothing drains the inbox, and most questions about a *report*
are asked once it exists. This is the same answer path, runnable against a finished run-dir.

It reads the ledger and reports on it. It never explores, tests, or writes to the ledger — the only
thing it appends to is `qa_log.jsonl`, the same file the console polls, so answers from either route
land in one thread.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config
from .codex_exec import DEFAULT_ENV
from .orchestrator import Config, Orchestrator


def _print(rec: dict) -> None:
    print()
    print(rec.get("answer", "") or "(no answer)")
    if not rec.get("confident"):
        print("\n[the run doesn't fully settle this]")
    if rec.get("basis"):
        print(f"\nbased on: {rec['basis']}")
    if rec.get("suggested_steer"):
        print(f"\nWant me to follow up on this? {rec.get('suggest_reason') or ''}")
        print(f"  steer: {rec['suggested_steer']}")
        print("  → to run it:  python3 -m src.cli --resume --run-dir <dir>  (with this in the inbox)")
    if rec.get("usd"):
        print(f"\n(${rec['usd']:.2f})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ask a question about a run (live or finished)")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--ask", help="the question (omit for an interactive prompt)")
    ap.add_argument("--qa-usd", type=float, default=0.50, help="cap per answer")
    ap.add_argument("--model", default=config.RUN_MODEL)
    ap.add_argument("--env", default=DEFAULT_ENV)
    a = ap.parse_args()

    run_dir = Path(a.run_dir)
    if not (run_dir / "ledger.json").exists():
        print(f"no ledger at {run_dir} — nothing to ask about", file=sys.stderr)
        return 2

    cfg = Config(model=a.model, env_file=a.env, qa_task_usd=a.qa_usd, workspace=False)
    orch = Orchestrator.resume(run_dir, cfg)
    # A finished run has spent its budget; asking a question must not be blocked by that. The
    # per-answer cap is the real bound here, so give the Q&A session its own small allowance.
    orch.budget.total = orch.budget.spent + max(a.qa_usd * 8, 1.0)

    if a.ask:
        _print(orch._answer_question(a.ask, phase="qa-cli"))
        return 0

    print(f"asking about: {orch.q[:100]}")
    print("type a question (blank line to quit)\n")
    while True:
        try:
            q = input("? ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not q:
            return 0
        _print(orch._answer_question(q, phase="qa-cli"))
        print()


if __name__ == "__main__":
    raise SystemExit(main())
