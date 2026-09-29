#!/usr/bin/env python3
"""CLI for the v2 orchestrator agent (mirrors baseline.py's interface).

    python3 -m methodology_v2.cli --question-file Q.txt --run-dir OUT --budget 50
    python3 -m methodology_v2.cli --question "What ..." --run-dir OUT --budget 50 -K 5

Run dirs may live anywhere (no .agents/skills auto-load concern: each codex task runs
with --cd <its own task dir>, an empty leaf, and the repo root has no AGENTS.md).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config
from .codex_exec import DEFAULT_ENV
from .orchestrator import Config, Orchestrator


def main() -> int:
    ap = argparse.ArgumentParser(description="Methodology v2 orchestrator agent")
    g = ap.add_mutually_exclusive_group(required=False)   # required unless --resume (checked below)
    g.add_argument("--question")
    g.add_argument("--question-file")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--budget", type=float, default=50.0, help="total USD cap (one pool)")
    ap.add_argument("-K", "--batch", type=int, default=5,
                    help="max directions the agent's planner may fund per round")
    ap.add_argument("--alloc-ceiling-frac", type=float, default=0.40,
                    help="max share of a round's pot any single direction may be allocated")
    ap.add_argument("--explore-round-frac", type=float, default=0.50,
                    help="share of the remaining budget the planner may hand out each round; the "
                         "rest stays free so every hypothesis it produces can still be tested")
    ap.add_argument("--screen-task-usd", type=float, default=0.40, help="cap per stage-1 screen")
    ap.add_argument("--deep-task-usd", type=float, default=2.00, help="cap per stage-2 deep test")
    ap.add_argument("--checkpoint-every", type=float, default=0.0, help="USD between checkpoints (0→budget/6)")
    ap.add_argument("--max-rounds", type=int, default=30)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--task-timeout", type=int, default=1800)
    ap.add_argument("--model", default=config.RUN_MODEL)
    ap.add_argument("--reasoning", default=config.REASONING, choices=["minimal", "low", "medium", "high"],
                    help="codex reasoning effort (default from config.py)")
    ap.add_argument("--env", default=DEFAULT_ENV)
    ap.add_argument("--sources", default="",
                    help="comma-separated paperclip corpora to ground on (e.g. arxiv,pmc). Empty = web only.")
    ap.add_argument("--reference-set", help="path to JSON list of grounded findings (§7c recall)")
    # Interactive steering (DESIGN_interactive.md)
    ap.add_argument("--steer-inbox", default="",
                    help="path to a JSON steer inbox drained each round (async live steering)")
    ap.add_argument("--interactive", action="store_true",
                    help="block for console steer input at every checkpoint")
    ap.add_argument("--resume", action="store_true",
                    help="resume a paused run from --run-dir (rehydrate ledger + runtime state)")
    # Artifacts (DESIGN_workspace.md)
    ap.add_argument("--no-workspace", action="store_true",
                    help="don't create <run-dir>/workspace (disables artifacts entirely)")
    ap.add_argument("--no-auto-artifacts", action="store_true",
                    help="only build deliverables the user explicitly asks for (skip the finalize pass)")
    ap.add_argument("--artifact-usd", type=float, default=1.50, help="cap per artifact build")
    # The data plane (DESIGN_data_plane.md) — the researcher's own files as a queryable source.
    ap.add_argument("--data", default="",
                    help="comma-separated data files (CSV/TSV) the question is about. They are "
                         "copied read-only into <run-dir>/workspace/inputs/ and the agent queries "
                         "them with scripts it writes. Empty = literature only (unchanged).")
    ap.add_argument("--data-query-usd", type=float, default=1.50, help="cap per data-query task")
    ap.add_argument("--ablate", default="",
                    choices=["", "no-verifier", "no-alloc", "no-directions",
                             "search-only", "directions-only"],
                    help="methodology ablation. no-verifier: drop STAGE 2 (deep test) — whatever "
                         "passes the cheap screen is pooled untested, so nothing is ever checked "
                         "for counter-evidence. no-alloc: the frontier is still ranked but the "
                         "round's pot is split equally instead of priced by the agent. "
                         "no-directions: no frontier — hypotheses are generated straight from the "
                         "question every round. search-only: no hypotheses/evidence/verifier at "
                         "all, just ask and search. directions-only: decompose, then answer each "
                         "part by search, with no beliefs. In every case the rest is unchanged.")
    a = ap.parse_args()

    ref: list[str] = []
    if a.reference_set:
        ref = json.loads(Path(a.reference_set).read_text(encoding="utf-8"))
        if isinstance(ref, dict):
            ref = ref.get("findings") or ref.get("items") or []

    cfg = Config(
        budget=a.budget, K=a.batch, alloc_ceiling_frac=a.alloc_ceiling_frac,
        explore_round_frac=a.explore_round_frac, screen_task_usd=a.screen_task_usd,
        deep_task_usd=a.deep_task_usd,
        checkpoint_every=a.checkpoint_every, max_rounds=a.max_rounds,
        concurrency=a.concurrency, task_timeout=a.task_timeout, model=a.model,
        reasoning=a.reasoning, env_file=a.env, reference_set=ref, ablate=a.ablate,
        sources=[s.strip() for s in a.sources.split(",") if s.strip()],
        steer_inbox=a.steer_inbox, interactive=a.interactive,
        workspace=not a.no_workspace, auto_artifacts=not a.no_auto_artifacts,
        artifact_task_usd=a.artifact_usd,
        data=[s.strip() for s in a.data.split(",") if s.strip()],
        data_query_usd=a.data_query_usd,
    )
    if a.resume:
        orch = Orchestrator.resume(Path(a.run_dir), cfg)
        orch.resume_run()
    else:
        if not (a.question or a.question_file):
            ap.error("one of --question / --question-file is required (unless --resume)")
        question = Path(a.question_file).read_text(encoding="utf-8") if a.question_file else a.question
        orch = Orchestrator(question, Path(a.run_dir), cfg)
        orch.run()
    print(f"\nanswer  → {Path(a.run_dir) / 'answer.md'}")
    print(f"ledger  → {Path(a.run_dir) / 'ledger.json'}")
    print(f"run     → {Path(a.run_dir) / 'run.json'}")
    if not a.no_workspace:
        print(f"work    → {Path(a.run_dir) / 'workspace'}   (git repo: data/, artifacts/, scripts/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
