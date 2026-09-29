"""The control shell (Methodology §4) — the orchestrator owns the loop and the state.

INIT  → PRIOR's parametric candidate answers become HYPOTHESES and go straight through the
        two-stage test; whatever they turn up also seeds the frontier. GROUND the key terms.
LOOP  → PLAN (§5): the agent ranks the open directions AND allocates the round's money across
        them → parallel EXPLORE, each direction capped at its own allocation → the hypotheses
        it proposes are SCREENED (stage 1, cheap) → every hypothesis that passes is DEEP-TESTED
        (stage 2: hunt evidence *and* counter-examples) → survivors enter the POOL, the rest go
        to the BIN with a reason → periodic EVALUATE checkpoint (§7) → steer / stop (§8).
FINAL → outline-then-fill report over the pool, with the bin reported alongside.

BUDGET. One pool. The *agent* decides how it is split across topics: executors.plan returns a
dollar figure per direction and the harness enforces it with the per-task USD watchdog. The
harness imposes exactly two limits of its own — a per-direction ceiling (a share of what's
left, so one round can't eat the run) and a per-round explore cap, which is what makes
"verification always happens" true: testing draws from the same pool but is never rationed
against it. Killed tasks are still CHARGED.

TESTING IS NEVER RATIONED. Every hypothesis is screened, and every hypothesis that passes the
screen is deep-tested. There is no promotion gate, no beam width, and no error budget deciding
what gets checked. Nothing is discarded either: a hypothesis that fails is BINNED with its
reason, stays in the ledger and the report, and can be resurfaced by later corroborating
evidence.

Every semantic judgment goes through an embedding (`measure.py`) or an LLM judge
(`executors.judge_*`) — there are no lexical proxies.

ARTIFACTS. Each run-dir also carries a git-controlled `workspace/` (`workspace.py`) where the agent
BUILDS things: charts, CSVs, comparison tables. The harness exports the ledger there as JSON + CSV so
a build computes over real data instead of re-typing numbers out of a prompt, and it commits whatever
appears on disk. Every run gets the export for free; only bespoke deliverables (asked for via an
`artifacts_request` steer, or the one bounded pass at finalize) cost money.
"""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from . import config, executors, measure, metrics, workspace
from .codex_exec import CodexError, DEFAULT_ENV
from .embed import Embedder
from .ledger import (Ledger, Direction, Hypothesis, EXPLORING, EXPLORED, CLOSED,
                     PROPOSED, SCREENED, POOLED, BINNED, SUPPORTS)
from .steer import SteerSource, NullSteer, FileInbox, ConsolePrompt
from .workspace import Workspace


# ── budget (one pool; the agent allocates it across topics) ──────────────────

class Budget:
    """A single pool. There is no explore/verify split — testing is not rationed against
    discovery, it just spends from the same money. `by_phase` is bookkeeping for the run
    report, not an allocation mechanism: nothing reads it to decide what may run."""

    PHASES = ("init", "plan", "explore", "screen", "deep", "measure", "finalize", "artifact")

    def __init__(self, total: float):
        self.total = float(total)
        self.spent = 0.0
        self.by_phase: dict[str, float] = {p: 0.0 for p in self.PHASES}

    def add_budget(self, delta: float) -> None:
        """Human steer: grow (or shrink) the total budget mid-run. Never drops below what's
        already spent, so a shrink can't go negative."""
        self.total = max(self.spent, self.total + delta)

    def spend(self, phase: str, usd: float) -> None:
        if usd and usd > 0:
            self.spent += usd
            self.by_phase[phase] = self.by_phase.get(phase, 0.0) + usd

    def remaining(self) -> float:
        return max(0.0, self.total - self.spent)


@dataclass
class Config:
    budget: float = 50.0
    K: int = 5                         # max directions the planner may fund in one round
    # ── budget allocation (the agent decides; these are the harness's only limits) ──
    alloc_ceiling_frac: float = 0.40   # no single direction may get more than this share of the round's pot
    explore_round_frac: float = 0.50   # share of the remaining budget the planner may hand out per round;
                                       # the rest stays available so this round's hypotheses can all be
                                       # tested (testing is never rationed — see _round_explore_pot)
    explore_default_usd: float = 3.5   # allocation for a direction the planner didn't price
    explore_min_usd: float = 1.0       # below this a direction isn't worth launching
    plan_task_usd: float = 1.0         # cap for the rank-and-allocate call itself
    # ── the two-stage test (caps; the hint sent to the model is 0.8x these) ──
    screen_task_usd: float = 0.40      # stage 1: quick search — does this hold up at all?
    deep_task_usd: float = 2.00        # stage 2: extensive hunt for evidence AND counter-examples
    ground_task_usd: float = 2.0       # cap per GROUND
    ground_terms: int = 4              # how many key terms to GROUND in INIT (0 = skip)
    checkpoint_every: float = 0.0
    progress_eps: float = 0.02         # new (covered asks + pooled) per $ below this = stalled
    max_rounds: int = 30
    concurrency: int = 4
    task_timeout: int = 1800
    sources: list[str] = field(default_factory=list)   # paperclip corpora to ground on (empty = web only)
    model: str = config.RUN_MODEL      # single source of truth: config.py (env-overridable)
    reasoning: str = config.REASONING  # codex model_reasoning_effort (minimal|low|medium|high)
    env_file: str = DEFAULT_ENV
    reference_set: list[str] = field(default_factory=list)
    rubric: str = "Correctness (no hallucination), Completeness (diverse coverage), " \
                  "Forward-looking (good next directions), Faithfulness (answers the ask)."
    retest_max_attempts: int = 2       # bound the refute/conflict → re-investigate → re-test loop
    # Corroboration re-scoring — the driver that pulls hypotheses back OUT of the bin.
    corroborate_enabled: bool = True
    corroborate_thresh: float = 0.88   # text-embedding cosine to count fresh evidence as bearing on a hypothesis
    corroborate_per_source: float = 0.04  # confidence bump per independent corroborating source (diminishing)
    unbin_thresh: float = 0.60         # corroborated past this, a binned hypothesis returns for another test
    # INIT probe — the parametric candidate answers are tested first, and what they turn up
    # becomes some of the research directions to take.
    prior_probe_enabled: bool = True
    prior_probe_k: int = 5             # how many top-confidence candidate answers to test
    niche_boost: float = 0.15          # promise boost for directions under a thin/contested parent
    # Frontier shortlisting — the embedding pre-rank narrows what the planner has to read.
    rerank_direct_max: int = 60        # if <= this many open directions, hand them all to the planner
    rerank_pool: int = 50              # else embedding pre-filters to this top-N first
    # Interactive steering (see DESIGN_interactive.md). Default off → behavior unchanged.
    steer_inbox: str = ""              # path to a JSON inbox drained each round (async live steering)
    interactive: bool = False          # block for console steer input at every checkpoint
    # Artifacts (see DESIGN_workspace.md) — a git repo per question the agent builds deliverables in.
    workspace: bool = True             # create <run-dir>/workspace and export the ledger to data/
    auto_artifacts: bool = True        # at finalize, let the agent build report-supporting deliverables
    artifact_task_usd: float = 1.50    # cap per artifact build
    artifact_min_usd: float = 0.50     # below this a build isn't worth launching; the request stays queued
    # The data plane (see DESIGN_data_plane.md) — the researcher's own files as a queryable source.
    data: list[str] = field(default_factory=list)   # paths copied into workspace/inputs/ (empty = off)
    qa_task_usd: float = 0.50          # cap per answer to a researcher's question (reason-mode)
    data_query_usd: float = 1.50       # cap per data-query task (writes + runs a script)
    judge_query_usd: float = 0.40      # cap per script review — reason-mode, no web search
    # Ablation switch for methodology experiments. "" = the full pipeline. "no-verifier" removes
    # STAGE 2 (deep test): whatever passes the cheap screen is accepted as-is, so nothing is ever
    # tested for counter-evidence. Everything else — directions, planning, budget allocation,
    # screening, checkpoints, finalize — is untouched, so the arms stay comparable.
    ablate: str = ""


class Orchestrator:
    def __init__(self, question: str, run_dir: Path, cfg: Config,
                 steer: SteerSource | None = None):
        self.q = question.strip()
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.cfg = cfg
        self.ledger = Ledger(self.q)
        self.ledger.sources = list(cfg.sources or [])   # paperclip corpora to ground explore/verify on
        self.budget = Budget(cfg.budget)
        self.embedder = Embedder(env_file=cfg.env_file)
        self.snapshots: list[metrics.Snapshot] = []
        self.explored_texts: list[str] = []
        self._new_hypotheses = 0       # hypotheses added since the last checkpoint (for progress)
        self.uncovered_fields: list[str] = []
        self.explore_costs: list[float] = []
        self.test_costs: list[float] = []
        self.round = 0
        self.last_draft = ""
        self.checkpoint_cost = cfg.checkpoint_every or (cfg.budget / 6.0)
        self.last_checkpoint_spend = 0.0
        self._task_n = 0
        self._emb_charged = 0.0
        self._log_f = open(self.run_dir / "orchestrator.log", "a", encoding="utf-8")
        # Interactive steering: an async source (default off) + a blocking console for --interactive.
        self.steer: SteerSource = steer or (FileInbox(cfg.steer_inbox) if cfg.steer_inbox else NullSteer())
        self._console = ConsolePrompt() if cfg.interactive else None
        self._steer_log = open(self.run_dir / "steer.log", "a", encoding="utf-8")
        self._stop_requested = False   # set by a 'stop_after_round'/'finalize_now' steer control
        # The per-question git workspace + its artifact index (see workspace.py).
        self.ws: Workspace | None = Workspace(self.run_dir / "workspace") if cfg.workspace else None
        self.artifacts: list[dict] = []          # index records, oldest first
        self._artifact_requests: list[dict] = []  # queued {spec, kind}, drained at the loop seams
        # The data plane: the researcher's files, and how this request was routed (§3.2).
        self.datasets: list[dict] = []           # {dataset_id, name, path, sha256, columns, rows}
        self.route: dict = {}                    # the classify_request result, persisted in run.json

    # ── infra ────────────────────────────────────────────────────────────────
    def log(self, msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self._log_f.write(line + "\n")
        self._log_f.flush()

    def _task_dir(self, label: str, subject: str = "") -> Path:
        self._task_n += 1
        d = self.run_dir / "tasks" / f"{self._task_n:04d}_{label}"
        d.mkdir(parents=True, exist_ok=True)
        if subject:   # what this step is about (term / direction / hypothesis) — shown live in the console
            try:
                (d / "subject.txt").write_text(subject.strip()[:300], encoding="utf-8")
            except OSError:
                pass
        return d

    def _charge_embed(self) -> None:
        delta = self.embedder.spent_usd - self._emb_charged
        if delta > 0:
            self.budget.spend("measure", delta)
            self._emb_charged = self.embedder.spent_usd

    def _take(self, res, phase: str = "explore"):
        """Charge a (data, usd) result and return data (or None). A task killed at its cap
        returns (None, usd>0) — we still charge it. `phase` is bookkeeping only: no phase has
        its own pool, so charging one never starves another."""
        if not res:
            return None
        data, usd = res
        self.budget.spend(phase, usd or 0.0)
        if isinstance(usd, (int, float)) and usd > 0:
            if phase == "explore":
                self.explore_costs.append(usd)
            elif phase in ("screen", "deep"):
                self.test_costs.append(usd)
        return data

    def _run_parallel(self, jobs: list[tuple]) -> list:
        results: list = [None] * len(jobs)
        if not jobs:
            return results
        with ThreadPoolExecutor(max_workers=self.cfg.concurrency) as ex:
            futs = {ex.submit(fn, *a, **k): i for i, (fn, a, k) in enumerate(jobs)}
            for fut in as_completed(futs):
                i = futs[fut]
                try:
                    results[i] = fut.result()
                except CodexError as e:
                    self.log(f"  task {i} config-failed: {e}")
                except Exception as e:  # noqa: BLE001
                    self.log(f"  task {i} errored: {type(e).__name__}: {e}")
        return results

    def _kw(self, usd_cap: float | None = None) -> dict:
        kw = {"model": self.cfg.model, "env_file": self.cfg.env_file,
              "reasoning": self.cfg.reasoning, "timeout": self.cfg.task_timeout}
        if usd_cap:
            kw["usd_cap"] = usd_cap
        return kw

    # ── INIT (§4 steps 1-3) ───────────────────────────────────────────────────
    def init(self) -> None:
        self.log("INIT: parse fields + PRIOR (parallel)")
        out = self._run_parallel([
            (executors.fields, (self.q, self._task_dir("fields")), self._kw()),
            (executors.prior, (self.q, self._task_dir("prior")), self._kw()),
        ])
        req = self._take(out[0], phase="init")
        if req is not None:
            self.ledger.required_fields = req
        pr = self._take(out[1], phase="init")
        key_terms: list[str] = []
        if pr is not None:
            self.ledger.seed(open_questions=pr.get("open_questions") or [],
                             prior_hypothesis=pr.get("prior_hypothesis", ""),
                             candidate_answers=pr.get("candidate_answers") or [])
            key_terms = (pr.get("key_terms") or [])[:self.cfg.ground_terms]
        self.uncovered_fields = list(self.ledger.required_fields)
        self.log(f"  required_fields={len(self.ledger.required_fields)} "
                 f"seed_directions={len(self.ledger.directions)} "
                 f"prior_hypotheses={len(self.ledger.hypotheses)} terms={len(key_terms)}")

        if key_terms and self.budget.remaining() > 0:
            self.log(f"INIT: GROUND {len(key_terms)} terms (parallel, ~${self.cfg.ground_task_usd}/term)")
            jobs = [(executors.ground, (t, self.q, self._task_dir(f"ground_{i}", t)),
                     {**self._kw(self.cfg.ground_task_usd),
                      "budget_hint": self.cfg.ground_task_usd * 0.8,
                      "guardrails": self._guardrails()})
                    for i, t in enumerate(key_terms)]
            for t, res in zip(key_terms, self._run_parallel(jobs)):
                g = self._take(res, phase="init")
                if g is not None:
                    self.ledger.glossary[t] = {"definition": g.get("definition", ""),
                                               "source": g.get("source", {})}
        self._prior_probe()
        self.log(f"  INIT spent ${self.budget.spent:.2f}")
        self._save()

    # ── INIT probe: test what the model thinks it already knows ───────────────
    def _prior_probe(self) -> None:
        """PRIOR's candidate answers came out of parametric memory, so they are the highest
        hallucination risk in the run — they go through the full two-stage test before anything
        is built on them. Whatever survives (and whatever is refuted interestingly) then seeds
        research directions: what the model already believes is a legitimate place to start."""
        cands = [h for h in self.ledger.hypotheses.values() if h.origin == "prior"]
        if not self.cfg.prior_probe_enabled or not cands:
            return
        cands.sort(key=lambda h: -h.confidence)
        cands = cands[:self.cfg.prior_probe_k]
        for h in self.ledger.hypotheses.values():          # the rest wait for a normal round
            if h.origin == "prior" and h not in cands:
                h.status = PROPOSED
        verify = self.cfg.ablate != "no-verifier"
        self.log(f"INIT: probing {len(cands)} prior candidate answer(s) — "
                 + ("screen then deep test" if verify else "screen only (ablate=no-verifier)"))
        self._screen(cands)
        if verify:
            self._deep_test([h for h in cands if h.status == SCREENED])
        else:
            self.ledger.accept_screened([h for h in cands if h.status == SCREENED])
        for h in cands:
            if h.status == POOLED:
                self.ledger.add_direction(
                    f"Build on the confirmed prior: {h.text}", rationale=
                    "INIT probe: this candidate answer survived the deep test — extend it",
                    promise=min(1.0, 0.55 + 0.4 * h.confidence))
        self.log(f"  INIT probe: {sum(h.status == POOLED for h in cands)} pooled, "
                 f"{sum(h.status == BINNED for h in cands)} binned "
                 f"(+{sum(1 for h in cands if h.status == POOLED)} directions seeded)")

    # ── cost bookkeeping ──────────────────────────────────────────────────────
    def _avg(self, costs: list[float], seed: float) -> float:
        return (sum(costs[-8:]) / len(costs[-8:])) if costs else seed

    def _round_explore_pot(self) -> float:
        """What the planner may hand out this round. Capped at a share of the remaining budget so
        the hypotheses this exploration produces can all be screened and deep-tested from the same
        pool — this is the mechanism behind 'testing is never rationed'. Whatever testing doesn't
        use simply rolls into next round's remaining, so nothing is wasted."""
        return self.budget.remaining() * self.cfg.explore_round_frac

    # ── MAIN LOOP (§4) ────────────────────────────────────────────────────────
    def run(self) -> None:
        self._ws_init()
        self._data_init()
        # Route by claim kind BEFORE spending anything on research (DESIGN_data_plane.md §3.2).
        self.route = self._classify()
        kind = self.route.get("kind", "research_only")
        made: list[Hypothesis] = []
        if kind in ("data_only", "both"):
            made = self._run_data_phase(self.route.get("data_ask") or self.q)
        if kind == "both" and (ask := (self.route.get("research_ask") or "").strip()):
            # The bridge (§3.2): the literature half is scoped BY the data result, so it targets
            # the researcher's actual rows instead of a guess about what they contain.
            found = "; ".join(h.text for h in self.ledger.pool() if self.ledger.is_data_claim(h))
            self.ledger.add_direction(
                ask + (f"\n(computed from the researcher's data: {found[:600]})" if found else ""),
                rationale="bridge: establish this from the literature FOR the computed data result",
                promise=0.99, origin="data")
        if kind == "data_only":
            # No open question to chase: the research loop's rounds, frontier, two-stage test and
            # coverage convergence all exist for a question the literature must settle (§3.3).
            self.log("DATA-ONLY: skipping the research loop (nothing here needs the literature)")
            self._drain_steer("post-data")
            self._service_artifacts("post-data")
            self.finalize(converged=True)
            return
        if self.cfg.ablate in ("search-only", "directions-only"):
            self._search_loop()
            return
        self.init()
        self._drain_steer("post-init")     # let a human set scope/assumptions before round 1
        self._service_artifacts("post-init")
        self._loop()

    def _search_loop(self) -> None:
        """ABLATION baselines with no belief ledger.

        search-only      — ask the question and search for the answer, repeatedly, until the budget
                           is gone. No decomposition, no hypotheses, no evidence adjudication.
        directions-only  — the same, but the question is first DECOMPOSED into directions and each
                           is answered separately, so the pair isolates what decomposition alone buys.
        """
        decompose = self.cfg.ablate == "directions-only"
        self.log(f"ABLATION {self.cfg.ablate}: no hypotheses, no evidence ledger, no verifier")
        if decompose:
            self.init()                      # seeds required_fields + the initial directions
        notes: list[str] = []
        cap = max(0.60, self.cfg.deep_task_usd)
        while (self.budget.remaining() >= cap and self.round < self.cfg.max_rounds
               and not self._stop_requested):
            self._drain_steer(f"round{self.round + 1}")
            self.round += 1
            if decompose:
                opens = [d for d in self.ledger.open_directions()][: self.cfg.K]
                if not opens:
                    break
                asks = [(d, d.question_text) for d in opens]
            else:
                asks = [(None, self.q) for _ in range(min(self.cfg.K, 3))]
            self.log(f"ROUND {self.round}: ANSWER {len(asks)} question(s) "
                     f"(spent ${self.budget.spent:.2f}/{self.budget.total:.2f})")
            jobs = [(executors.answer_search,
                     (q, "\n\n".join(notes)[-6000:], self._task_dir(f"answer_r{self.round}_{i}", q)),
                     {**self._kw(cap), "budget_hint": cap * 0.8, "guardrails": self._guardrails()})
                    for i, (_d, q) in enumerate(asks)]
            got = 0
            for (d, _q), res in zip(asks, self._run_parallel(jobs)):
                r = self._take(res, phase="explore")
                if d is not None:
                    d.status = CLOSED
                if r is None:
                    continue
                md = (r.get("answer_markdown") or "").strip()
                if md:
                    notes.append(md)
                    got += 1
                # keep the sources so the report can carry a real bibliography
                for src in (r.get("sources") or []):
                    try:
                        self.ledger.note_source(src)
                    except Exception:      # noqa: BLE001 — bibliography is best-effort here
                        pass
            self.log(f"  +{got} answer section(s); {len(notes)} total")
        self._ablation_notes = notes
        self.finalize(converged=True)

    def _loop(self) -> None:
        converged = False
        while (not converged and not self._stop_requested
               and self.round < self.cfg.max_rounds
               and self.ledger.open_directions()
               and self.budget.remaining() >= self.cfg.explore_min_usd):
            self._write_digest()
            control = self._drain_steer(f"round{self.round + 1}")
            # Deliverables are built BEFORE the round's research spend, so a request that arrives
            # mid-run is answered at the next seam instead of waiting for the run to finish.
            self._service_artifacts(f"round{self.round + 1}")
            if control == "finalize_now":
                break
            self.round += 1

            # 1. PLAN — the agent ranks the frontier and allocates this round's money across it.
            if self.cfg.ablate == "no-directions":
                self._reset_root_direction()
            plan = self._plan_batch()
            if not plan:
                break
            for d, _ in plan:
                d.status = EXPLORING
            self.log(f"ROUND {self.round}: EXPLORE {len(plan)} dirs "
                     f"({'  '.join(f'{d.id}=${u:.2f}' for d, u in plan)}; "
                     f"spent ${self.budget.spent:.2f}/{self.budget.total:.2f})")

            # 2. EXPLORE — each direction capped at exactly what the agent gave it.
            jobs = []
            for i, (d, usd) in enumerate(plan):
                ctx = measure.select_context(self.embedder, d, self.ledger.all_hypotheses())
                kw = {**self._kw(usd), "budget_hint": usd, "guardrails": self._guardrails()}
                jobs.append((executors.explore,
                             (d, ctx, self.ledger, self._task_dir(f"explore_r{self.round}_{i}", d.question_text)), kw))
            self._charge_embed()
            results = self._run_parallel(jobs)

            fresh: list[Hypothesis] = []
            for (d, usd), res in zip(plan, results):
                self.explored_texts.append(d.question_text)
                before = self.budget.spent
                r = self._take(res, phase="explore")
                d.spent_usd += self.budget.spent - before
                if r is None:
                    d.status = CLOSED
                    continue
                fresh += self.ledger.ingest_hypotheses(r.get("hypotheses"), direction_id=d.id)
                if self.cfg.ablate == "no-directions":
                    # ABLATION: no frontier. Proposed directions are discarded and the single root
                    # direction stays OPEN, so every round generates hypotheses straight from the
                    # question rather than from a decomposition of it.
                    d.status = EXPLORING
                else:
                    self.ledger.add_directions(r.get("new_directions"), parent_id=d.id)
                    d.status = CLOSED if r.get("dead_end") else EXPLORED
            self._new_hypotheses += len(fresh)
            self.log(f"  +{len(fresh)} hypotheses from {len(plan)} directions")

            # 3-4. TEST — every hypothesis is screened, and everything that passes is deep-tested.
            #      Neither stage is rationed; both simply draw from the pool.
            self._screen(self.ledger.pending_screen())
            if self.cfg.ablate == "no-verifier":
                # STAGE 2 removed: accept the screen's output untested. _rescore_corroboration is
                # skipped too — it re-adjudicates verdicts, which is verifier machinery.
                kept = self.ledger.accept_screened(self.ledger.pending_deep())
                self.log(f"  DEEP: SKIPPED (ablate=no-verifier) — {kept} screened hypotheses "
                         f"pooled untested, none checked for counter-evidence")
            else:
                self._deep_test(self.ledger.pending_deep())
            # fresh evidence can pull hypotheses back out of the bin. This is a refinement, not a
            # correctness requirement — and it is embedding-heavy, so a proxy blip here must not
            # discard a whole round of completed (and paid-for) DEEP work.
            try:
                if self.cfg.ablate != "no-verifier":
                    self._rescore_corroboration()
            except Exception as e:                       # noqa: BLE001
                self.log(f"  rescore skipped ({type(e).__name__}: {str(e)[:120]})")

            if self.budget.spent - self.last_checkpoint_spend >= self.checkpoint_cost:
                converged = self._checkpoint()
                self.last_checkpoint_spend = self.budget.spent
                # Post-checkpoint steer: the digest is fresh, so this is the natural review point.
                # In --interactive mode _drain_steer blocks here on the console.
                ctl = self._drain_steer(f"checkpoint{len(self.snapshots)}")
                self._service_artifacts(f"checkpoint{len(self.snapshots)}")
                if ctl == "finalize_now":
                    self._save()
                    break
            self._save()

        self.finalize(converged)

    # ── steering (human-in-the-loop; DESIGN_interactive.md) ───────────────────
    @staticmethod
    def _stronger(a: str, b: str) -> str:
        rank = {"continue": 0, "stop_after_round": 1, "finalize_now": 2}
        return a if rank.get(a, 0) >= rank.get(b, 0) else b

    def _drain_steer(self, phase: str) -> str:
        """Poll the steer source (plus the console at checkpoints in --interactive), apply each event,
        and return the strongest control seen. Non-blocking unless --interactive. A bad inbox must never
        crash the run."""
        control = "continue"
        try:
            events = list(self.steer.poll())
        except Exception as e:  # noqa: BLE001
            self.log(f"  steer: poll failed ({type(e).__name__}: {e})")
            events = []
        if self._console is not None and phase.startswith("checkpoint"):
            self.log("  --interactive: paused (blank=continue, 'stop'=finalize, or paste steer JSON)")
            try:
                events += list(self._console.poll())
            except Exception:  # noqa: BLE001
                pass
        for e in events:
            control = self._stronger(control, self._apply_steer(e, phase))
        if control == "stop_after_round":
            self._stop_requested = True
        return control

    def _apply_steer(self, event, phase: str) -> str:
        # Natural-language steer: classify the free text into structured fields (agent-side LLM call,
        # working proxy creds) before applying. The portal only forwards the raw text.
        orig_nl = getattr(event, "nl", "") or ""   # keep the user's ORIGINAL message for the record
        if orig_nl:
            # Is this an instruction or a QUESTION? Before this split, "did you find anything on X?"
            # was classified as a steer and became a research direction — the run went and spent
            # budget investigating a question the user only wanted answered from what it already had.
            from . import classify
            intent = classify.classify_intent(orig_nl, self.cfg.env_file, self.cfg.model)
            if intent.get("intent") == "qa":
                self._answer_question(orig_nl, phase, intent.get("rationale", ""))
                return "continue"          # a question changes nothing about the run
            event = self._classify_nl(event.nl) or event
            # Guard against classifier misfires: a message that ADDS work (directions/scope/assumptions)
            # cannot also be a "stop" — that's contradictory intent. Drop the stop so the agent actually
            # explores what the user asked for instead of finalizing immediately.
            if getattr(event, "control", "") in ("stop_after_round", "finalize_now") and (
                    getattr(event, "directions_add", None) or getattr(event, "constraints", None)
                    or getattr(event, "assumptions", None) or getattr(event, "budget_delta", 0)
                    or getattr(event, "artifacts_request", None)
                    or getattr(event, "data_add", None)):
                self.log(f"  (ignoring '{event.control}' — the message also adds work)")
                event.control = "continue"
        applied = event.apply_to(self.ledger)
        if applied.artifacts:
            if self.ws is None:
                applied.changes.append("skip artifacts: the workspace is disabled (--no-workspace)")
            else:
                self._artifact_requests += applied.artifacts
        # New data files handed over mid-run. Staged exactly like launch-time inputs so the data
        # plane treats them identically; paths are resolved against the run dir, because the portal
        # writes uploads there and its own filesystem layout differs from ours.
        data_add = list(getattr(event, "data_add", None) or [])
        if data_add:
            applied.changes.append(self._stage_steered_data(data_add))
        if applied.budget_delta:
            self.budget.add_budget(applied.budget_delta)
            applied.changes.append(f"budget {applied.budget_delta:+.2f} → total ${self.budget.total:.2f}")
        for v in applied.verdicts:
            self._apply_human_verdict(v)
        rec = {"phase": phase, "round": self.round, "control": applied.control,
               "message": orig_nl, "changes": applied.changes, "event": event.to_dict()}
        self._steer_log.write(json.dumps(rec) + "\n")
        self._steer_log.flush()
        if applied.changes:
            head = "; ".join(applied.changes[:8])
            more = f" (+{len(applied.changes) - 8} more)" if len(applied.changes) > 8 else ""
            self.log(f"  STEER[{phase}]: {head}{more}")
        return applied.control

    def _state_note(self) -> str:
        """One line on where the run stands — so an answer can say "not yet, still testing" rather
        than implying the run is finished when it isn't."""
        return (f"round {self.round}, ${self.budget.spent:.2f} of ${self.budget.total:.2f} spent; "
                f"{len(self.ledger.pool())} findings established, {len(self.ledger.binned())} set "
                f"aside, {len(self.ledger.pending_screen()) + len(self.ledger.pending_deep())} still "
                f"being tested, {len(self.ledger.open_directions())} directions still open")

    def qa_log_path(self) -> Path:
        return self.run_dir / "qa_log.jsonl"

    def _answer_question(self, question: str, phase: str, why: str = "") -> dict:
        """Answer a question about the run WITHOUT changing it, and offer a steer the answer implies.

        The ledger is never touched here — that is the whole point of the intent split. The answer
        is appended to qa_log.jsonl, which the steering console polls (`GET /qa`)."""
        self.log(f"  QUESTION[{phase}]: {question[:110]}" + (f"  ({why[:60]})" if why else ""))
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "phase": phase, "round": self.round,
               "question": question, "answer": "", "basis": "", "confident": False,
               "suggested_steer": None, "suggest_reason": None, "usd": 0.0}
        cap = self.cfg.qa_task_usd
        if self.budget.remaining() < cap:
            rec["answer"] = (f"I can't answer that right now — ${self.budget.remaining():.2f} left, "
                             f"under the ${cap:.2f} this needs. Add budget and ask again.")
            self._append_qa(rec)
            self.log("  QUESTION: not enough budget to answer")
            return rec
        report = ""
        ap = self.run_dir / "answer.md"
        if ap.exists():
            try:
                report = ap.read_text(encoding="utf-8")
            except OSError:
                report = ""
        before = self.budget.spent
        r = self._take(self._run_parallel([(executors.answer_question,
                       (question, self.ledger, report, self._state_note(),
                        self._task_dir("qa", question)), self._kw(cap))])[0], phase="qa")
        rec["usd"] = round(self.budget.spent - before, 4)
        if r is None:
            rec["answer"] = "I couldn't answer that one — the attempt failed. Try asking again."
            self._append_qa(rec)
            self.log("  QUESTION: answer failed")
            return rec
        rec.update({"answer": r.get("answer", ""), "basis": r.get("basis", ""),
                    "confident": bool(r.get("confident")),
                    "suggested_steer": r.get("suggested_steer") or None,
                    "suggest_reason": r.get("suggest_reason") or None})
        self._append_qa(rec)
        self.log(f"  ANSWER ({'confident' if rec['confident'] else 'uncertain'}, "
                 f"${rec['usd']:.2f}): {rec['answer'][:150]}")
        if rec["suggested_steer"]:
            self.log(f"  → offered steer: {rec['suggested_steer'][:120]}")
        return rec

    def _append_qa(self, rec: dict) -> None:
        try:
            with self.qa_log_path().open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError as e:
            self.log(f"  (could not write qa_log: {type(e).__name__}: {e})")

    def _classify_nl(self, text: str):
        """Turn a free-text steer message into a SteerEvent via a single mini chat call (classify.py).
        Falls back to a single new direction if the LLM is unavailable."""
        from . import classify
        from .steer import SteerEvent
        dirs = [(d.id, d.question_text) for d in self.ledger.open_directions()][:40]
        hyps = sorted(self.ledger.hypotheses.values(),
                      key=lambda h: -(int(h.id[1:]) if h.id[1:].isdigit() else 0))[:25]
        obj = classify.nl_to_steer(text, dirs, [(h.id, h.text) for h in hyps],
                                   self.cfg.env_file, self.cfg.model)
        if not obj:
            obj = {"directions_add": [{"question_text": text, "promise": 0.85}]}
        self.log(f"  NL steer '{text[:60]}' → {[k for k in obj if not k.startswith('_')]}")
        return SteerEvent.from_dict(obj)

    def _apply_human_verdict(self, v: dict) -> None:
        """A human ruling on a hypothesis is the highest-quality judgment in the system: it settles
        the hypothesis at $0, pins it so no test ever re-opens it, and — because nothing is
        discarded — a rejection goes to the bin with the human's note as the reason."""
        h = self.ledger.hypotheses.get(v["hypothesis_id"])
        if h is None:
            return
        note = v.get("note", "")
        h.origin, h.pinned = "human", True
        h.confidence = float(v.get("confidence", h.confidence))
        if v["verdict"] == "supported":
            h.status, h.verdict, h.bin_reason = POOLED, "supported", ""
        else:
            h.verdict = v["verdict"]
            self.ledger.bin(h, reason=f"human ruling: {note or v['verdict']}")
        self.log(f"  human verdict on {h.id}: {h.status}/{h.verdict} (pinned, $0)")

    # ── the workspace: a git repo per question, where deliverables get built ───
    def _ws_init(self) -> None:
        """Create <run-dir>/workspace and make it a git repo. Idempotent (resume calls it too),
        costs nothing, and never fails the run — a missing git just means no history."""
        if self.ws is None:
            return
        try:
            is_repo = self.ws.init(self.q)
        except OSError as e:
            self.log(f"  workspace unavailable ({type(e).__name__}: {e}) — artifacts disabled")
            self.ws = None
            return
        self.log(f"WORKSPACE: {self.ws.root}" + ("" if is_repo else "  (no git — artifacts uncommitted)"))

    def _ws_export(self, report: str = "") -> None:
        """Refresh data/ from the ledger so any artifact build computes over the CURRENT beliefs."""
        if self.ws is None:
            return
        try:
            self.ws.export(self.ledger, run_meta=self._run_meta(), report=report)
        except OSError as e:
            self.log(f"  workspace export failed ({type(e).__name__}: {e})")

    # ── the data plane (DESIGN_data_plane.md) ────────────────────────────────
    def _data_init(self) -> None:
        """Copy the researcher's files into workspace/inputs/ and describe them. Read-only for the
        agent and never regenerated, so they live beside data/ (the ledger export) rather than in
        it — data/ is overwritten on every export and would destroy them."""
        if not self.cfg.data or self.ws is None:
            return
        try:
            self.datasets = self.ws.add_inputs(list(self.cfg.data))
        except OSError as e:
            self.log(f"  data: could not stage inputs ({type(e).__name__}: {e})")
            return
        if not self.datasets:
            self.log(f"  data: none of {self.cfg.data} could be read — data plane off")
            return
        self.ledger.datasets = list(self.datasets)
        for d in self.datasets:
            self.log(f"DATA: {d['path']}  {d.get('rows')} rows x "
                     f"{len(d.get('columns') or [])} cols  [{d['dataset_id']}]")
        self.ws.commit("data: stage researcher inputs")

    def _stage_steered_data(self, paths: list[str]) -> str:
        """Adopt data files supplied mid-run by a steer. Same staging as _data_init, so the files
        land read-only in workspace/inputs/ and appear in the manifest every later task sees.
        Returns one human-readable line for the steer log."""
        if self.ws is None:
            return "skip data: the workspace is disabled (--no-workspace)"
        resolved = []
        for p in paths:
            q = Path(p).expanduser()
            if not q.is_absolute():
                q = self.run_dir / p           # portal-relative, e.g. "uploads/results.csv"
            # never let a steer read outside the run directory
            try:
                rq = q.resolve()
                if self.run_dir.resolve() not in rq.parents:
                    continue
            except OSError:
                continue
            if rq.is_file():
                resolved.append(str(rq))
        if not resolved:
            return f"skip data: none of {paths} could be read"
        try:
            added = self.ws.add_inputs(resolved)
        except OSError as e:
            return f"skip data: could not stage ({type(e).__name__}: {e})"
        if not added:
            return f"skip data: none of {paths} could be staged"
        known = {d.get("dataset_id") for d in self.datasets}
        fresh = [d for d in added if d.get("dataset_id") not in known]
        self.datasets += fresh
        self.ledger.datasets = list(self.datasets)
        for d in fresh:
            self.log(f"DATA (steered): {d['path']}  {d.get('rows')} rows x "
                     f"{len(d.get('columns') or [])} cols  [{d['dataset_id']}]")
        try:
            self.ws.commit("data: stage researcher inputs (steered)")
        except Exception:  # noqa: BLE001 — a commit failure must not lose the staged files
            pass
        names = ", ".join(d["name"] for d in fresh) or "(already staged)"
        return f"+data: {names}"

    def _inputs_manifest(self) -> str:
        if self.ws is None or not self.datasets:
            return "(no input data)"
        return self.ws.inputs_manifest(self.datasets)

    def _classify(self) -> dict:
        """Route by which KINDS of claim the request needs (§3.2). Only meaningful once there is
        data to compute over — with no inputs every claim is necessarily about the world."""
        if not self.datasets:
            return {"kind": "research_only", "data_ask": "", "research_ask": self.q,
                    "rationale": "no input data supplied", "ambiguities": []}
        r = self._take(self._run_parallel([(executors.classify_request,
                       (self.q, self._inputs_manifest(), self._task_dir("classify")),
                       self._kw(0.30))])[0], phase="init")
        if not r:
            # Fail toward doing MORE, not less: a misrouted run that also searches the literature
            # wastes budget; one that silently skips half the question answers the wrong thing.
            return {"kind": "both", "data_ask": self.q, "research_ask": self.q,
                    "rationale": "classification failed — running both paths", "ambiguities": []}
        self.log(f"ROUTE: {r.get('kind')} — {str(r.get('rationale',''))[:120]}")
        if r.get("data_ask"):
            self.log(f"  data ask:     {str(r['data_ask'])[:120]}")
        if r.get("research_ask"):
            self.log(f"  research ask: {str(r['research_ask'])[:120]}")
        for a in (r.get("ambiguities") or [])[:5]:
            self.log(f"  ambiguity: {a[:130]}")
        return r

    def _run_data_phase(self, ask: str) -> list[Hypothesis]:
        """Answer the data half by writing and running a script in the workspace, then verify it by
        READING that script (§4.3). Produces hypotheses whose evidence is a dataset SourceRef, so
        they never enter the literature test path."""
        if self.ws is None or not self.datasets or not ask.strip():
            return []
        cap = self.cfg.data_query_usd
        if self.budget.remaining() < cap:
            self.log(f"  DATA: ${self.budget.remaining():.2f} left, under the ${cap:.2f} query cap")
            return []
        self.log(f"DATA QUERY: {ask[:120]}")
        before = self.ws.snapshot()
        res = None
        try:
            res = executors.data_query(
                ask, self.q, self._inputs_manifest(), self._prior_data_work(),
                self._task_dir("data_query", ask), budget_hint=cap * 0.8,
                guardrails=self._guardrails(), python_bin=config.analysis_python(),
                cwd=self.ws.root, **self._kw(cap))
        except CodexError as e:
            self.log(f"  DATA QUERY config-failed: {e}")
        except Exception as e:  # noqa: BLE001 — a failed query must never end the run
            self.log(f"  DATA QUERY errored: {type(e).__name__}: {e}")
        r = self._take(res, phase="data")

        # Files are the source of truth here exactly as for artifacts: index and commit whatever
        # actually appeared, even if the task died before emitting JSON.
        produced = self.ws.artifact_paths(self.ws.changed(before))
        if produced:
            self._index_artifacts(workspace.build_records(
                self.ws, produced, request=f"data query: {ask}",
                declared=None, commit=None, auto=True))
            self.ws.write_index(self.artifacts)
        sha = self.ws.commit(f"data query: {ask[:70]}")
        if r is None:
            self.log("  DATA QUERY: no result" + (f" (files kept: {len(produced)})" if produced else ""))
            return []

        made = self._ingest_data_claims(r, ask)
        self.log(f"  DATA QUERY: {len(made)} claim(s), {r.get('rows_out')} rows out"
                 + (f", script {r.get('script')}" if r.get("script") else "")
                 + (f"  [{sha[:8]}]" if sha else ""))
        for a in (r.get("assumptions") or [])[:6]:
            self.log(f"    assumed: {a[:130]}")
        for c in (r.get("caveats") or [])[:4]:
            self.log(f"    caveat: {c[:130]}")
        for h in made:
            self._verify_data_claim(h)
        return made

    def _prior_data_work(self) -> str:
        rows = []
        for h in self.ledger.hypotheses.values():
            for ev in self.ledger.evidence_for(h):
                if ev.source.is_dataset() and ev.source.query:
                    rows.append(f"- {ev.source.query} → {h.text[:100]}")
                    break
        return "\n".join(rows[-10:])

    def _ingest_data_claims(self, r: dict, ask: str) -> list[Hypothesis]:
        """Turn a data-query result into hypotheses carrying dataset provenance. The script and its
        declared assumptions ARE the source record — that is what a reviewer reads (§4.1)."""
        ds_id = str(r.get("dataset_id") or "").strip()
        known = {d["dataset_id"] for d in self.datasets}
        if ds_id not in known:                    # model paraphrased it — pin to the real one
            ds_id = self.datasets[0]["dataset_id"] if self.datasets else ds_id
        src = {"kind": "dataset", "dataset_id": ds_id, "query": (r.get("query") or ask)[:400],
               "script": str(r.get("script") or ""),
               "assumptions": [str(a) for a in (r.get("assumptions") or [])],
               "rows": r.get("rows_out"), "title": "", "authors": []}
        made: list[Hypothesis] = []
        for c in (r.get("claims") or []):
            text = (c.get("text") or "").strip()
            if not text:
                continue
            h = self.ledger.add_hypothesis(text, rationale=f"computed from {ds_id}: {ask}"[:300],
                                           aspects=c.get("aspects"), confidence=0.75,
                                           origin="data")
            self.ledger.attach_evidence(h, [{
                "text": f"{src['query']}"
                        + (f" → {r.get('rows_out')} rows" if r.get("rows_out") is not None else ""),
                "stance": SUPPORTS, "source": src, "numbers": c.get("numbers") or [],
            }], phase="data")
            made.append(h)
        return made

    def _verify_data_claim(self, h: Hypothesis) -> None:
        """Verification for a data claim: READ the script (§4.3). Never the literature — searching
        published work for a fact about a private file is a category error, and a biased one: no
        paper mentions this dataset either way, so an adversarial search can only fail to find
        support and would bin correct findings."""
        ev = next((e for e in self.ledger.evidence_for(h) if e.source.is_dataset()), None)
        if ev is None or self.ws is None:
            return
        cap = self.cfg.judge_query_usd
        if self.budget.remaining() < cap:
            self.log(f"  REVIEW: no budget to review {h.id} — left unverified (reported as such)")
            return
        src_text = ""
        if ev.source.script:
            try:
                src_text = (self.ws.root / ev.source.script).read_text(
                    encoding="utf-8", errors="replace")
            except OSError:
                src_text = ""
        if not src_text.strip():
            self.ledger.bin(h, reason="no script was saved, so the result cannot be checked")
            self.log(f"  REVIEW {h.id}: no script on disk → binned (unverifiable)")
            return
        r = self._take(self._run_parallel([(executors.judge_query,
                       (h.text, ev.source.query, list(ev.source.assumptions), src_text,
                        self._inputs_manifest(), self._task_dir("judge_query", h.text)),
                       self._kw(cap))])[0], phase="data")
        if r is None:
            self.log(f"  REVIEW {h.id}: review failed — left untested")
            return
        # Any assumption the reviewer found undeclared is real provenance: it belongs on the record
        # even when the verdict is "correct", because it is a choice nobody stated.
        if r.get("unstated_assumptions"):
            ev.source.assumptions = list(ev.source.assumptions) + [
                f"(undeclared, found in review) {a}" for a in r["unstated_assumptions"][:5]]
        verdict = str(r.get("verdict") or "")
        h.confidence = max(0.0, min(1.0, float(r.get("confidence", h.confidence))))
        if verdict == "correct" and r.get("correct"):
            h.status, h.verdict = POOLED, "supported"
            self.log(f"  REVIEW {h.id}: script correct (conf {h.confidence:.2f})")
        elif verdict == "questionable_assumptions":
            # NOT a defect: the code is right for the choices it made, but a reasonable person
            # could have chosen otherwise. Pool it and surface the question — this is exactly the
            # correction a human should get the chance to make (§4.3).
            h.status, h.verdict = POOLED, "supported"
            note = "; ".join(r.get("issues") or []) or r.get("note", "")
            h.screen_note = f"assumptions worth confirming: {note}"[:400]
            self.log(f"  REVIEW {h.id}: computed correctly, but its assumptions need a human: {note[:110]}")
        else:
            reason = "; ".join(r.get("issues") or []) or r.get("note") or "the script does not compute the claim"
            h.verdict = "refuted"
            self.ledger.bin(h, reason=f"script review: {reason}"[:400])
            self.log(f"  REVIEW {h.id}: WRONG SCRIPT → binned: {reason[:110]}")

    def _service_artifacts(self, phase: str) -> None:
        """Build every queued deliverable, one at a time (they share one cwd and one git index).
        A request the budget can't cover stays queued — never silently dropped — and a run with less
        than the full cap left still builds, capped at what remains: the user asked for this one
        explicitly, and a truncated build still leaves its files behind."""
        if self.ws is None:
            return
        while self._artifact_requests:
            if self.budget.remaining() < self.cfg.artifact_min_usd:
                self.log(f"  ARTIFACT: only ${self.budget.remaining():.2f} left (min "
                         f"${self.cfg.artifact_min_usd:.2f}) — {len(self._artifact_requests)} "
                         f"request(s) stay queued; add budget and resume to build them")
                return
            self._build_artifact(self._artifact_requests.pop(0), phase)

    def _build_manifest(self) -> str:
        """What files an artifact build has to work with: the ledger export, plus the researcher's
        own data when the run was given any."""
        parts = [self.ws.data_manifest()]
        try:
            inputs = self.ws.inputs_manifest()
        except Exception:  # noqa: BLE001 — the data plane is optional
            inputs = ""
        if inputs and "no input data" not in inputs:
            parts.append("The researcher's OWN data (read-only — query it, never overwrite it):\n"
                         + inputs)
        return "\n\n".join(parts)

    def _index_artifacts(self, records: list[dict]) -> None:
        """Add index records, replacing any earlier entry for the SAME path. A later task that
        legitimately rewrites a file (the finalize chart pass re-running the analysis, say) must
        update its entry, not add a second one — otherwise the index reports more deliverables
        than exist on disk."""
        by_path = {a["path"]: a for a in self.artifacts}
        for rec in records:
            by_path[rec["path"]] = rec
        self.artifacts = list(by_path.values())

    def _existing_artifacts_md(self) -> str:
        return "\n".join(f"- {a['path']} — {a.get('title', '')}"
                         + (f" ({a['description'][:100]})" if a.get("description") else "")
                         for a in self.artifacts[-15:])

    def _build_artifact(self, req: dict, phase: str) -> list[dict]:
        """One ARTIFACT task: export the data, let codex build in the workspace, then index and
        commit whatever actually appeared on disk. The files are the source of truth — a task that
        dies without emitting JSON still gets its work captured."""
        spec = (req.get("spec") or "").strip()
        if not spec or self.ws is None:
            return []
        auto = bool(req.get("auto"))
        self.log(f"ARTIFACT[{phase}]: {spec[:110]}")
        self._ws_export()      # data/ tracks the live ledger; report.md is written by finalize
        before = self.ws.snapshot()
        cap = min(self.cfg.artifact_task_usd, self.budget.remaining())
        res = None
        try:
            res = executors.artifact(
                spec, req.get("kind", ""), self.q, self.ledger, self._build_manifest(),
                self._existing_artifacts_md(), self._task_dir("artifact", spec),
                budget_hint=cap * 0.8, guardrails=self._guardrails(),
                python_bin=config.analysis_python(), cwd=self.ws.root, **self._kw(cap))
        except CodexError as e:
            self.log(f"  ARTIFACT config-failed: {e}")
        except Exception as e:  # noqa: BLE001 — a failed build must never end the run
            self.log(f"  ARTIFACT errored: {type(e).__name__}: {e}")
        r = self._take(res, phase="artifact")

        produced = self.ws.artifact_paths(self.ws.changed(before))
        records = workspace.build_records(self.ws, produced, request=spec,
                                          declared=(r or {}).get("artifacts"),
                                          commit=None, auto=auto)
        self._index_artifacts(records)
        self.ws.write_index(self.artifacts)
        sha = self.ws.commit(f"artifact: {spec[:70]}")
        for rec in records:                 # the commit only exists once the index is written
            rec["commit"] = sha or ""
        for c in ((r or {}).get("caveats") or [])[:4]:
            self.log(f"    caveat: {c[:140]}")
        if records:
            self.log(f"  ARTIFACT: {len(records)} file(s) — "
                     + ", ".join(a["path"] for a in records[:6])
                     + (f"  [{sha[:8]}]" if sha else "  (uncommitted: no git)"))
        else:
            self.log("  ARTIFACT: the build produced no files"
                     + (f" — {(r or {}).get('summary', '')[:120]}" if r else ""))
        self._save()
        return records

    def _write_digest(self) -> None:
        """The snapshot a watching human reads before steering → steer_request.md."""
        L = self.ledger
        opens = sorted(L.open_directions(), key=lambda d: -d.promise)
        recent = sorted(L.hypotheses.values(), key=lambda h: h.id, reverse=True)[:12]
        binned = sorted(L.binned(), key=lambda h: -h.confidence)
        phases = "  ".join(f"{k} ${v:.2f}" for k, v in self.budget.by_phase.items() if v > 0)
        lines = [f"# Steering digest — round {self.round}", "",
                 f"**Question:** {self.q}", "",
                 f"- spent: ${self.budget.spent:.2f} / ${self.budget.total:.2f}  ({phases})",
                 f"- hypotheses: {len(L.hypotheses)} — {len(L.pool())} pooled, {len(binned)} binned, "
                 f"{len(L.pending_screen()) + len(L.pending_deep())} awaiting a test",
                 f"- evidence items: {len(L.evidence)}",
                 f"- open directions: {len(opens)}",
                 f"- uncovered asks: {self.uncovered_fields or '(none measured yet)'}", ""]
        if L.constraints:
            lines += ["**Scope:**", *[f"- {c}" for c in L.constraints], ""]
        if L.assumptions:
            lines += ["**Assumptions:**", *[f"- {a}" for a in L.assumptions], ""]
        lines += ["## Top open directions (id — promise — question)"]
        for d in opens[:15]:
            tag = " [human]" if d.origin == "human" else ""
            alloc = f" — last got ${d.allocated_usd:.2f}" if d.allocated_usd else ""
            lines.append(f"- `{d.id}` — {d.promise:.2f}{tag}{alloc} — {d.question_text}")
        lines += ["", "## Recent hypotheses (id — status — text)"]
        for h in recent:
            lines.append(f"- `{h.id}` — {h.status}/{h.verdict} — {h.text[:120]}")
        if binned:
            lines += ["", "## Deprioritised — still here, can be brought back (`hypotheses_unbin`)"]
            for h in binned[:10]:
                lines.append(f"- `{h.id}` — {h.bin_reason[:100]} — {h.text[:90]}")
        if self.ws is not None:
            lines += ["", f"## Artifacts — built in `{self.ws.root}` (a git repo)"]
            if self.artifacts:
                lines += [f"- `{a['path']}` ({a.get('kind', 'other')}) — {a.get('title', '')}"
                          for a in self.artifacts[-10:]]
            else:
                lines.append("- _(none yet)_")
            if self._artifact_requests:
                lines += [f"- queued: {r['spec'][:90]}" for r in self._artifact_requests]
            lines.append("Ask for one with `artifacts_request` — e.g. a CSV of every benchmark "
                         "number, or a chart comparing the leading candidates.")
        lines += ["", "---",
                  "Drop a steer event into the inbox. Keys: `directions_add` "
                  "[{question_text,rationale,promise}], `directions_drop` [id], `directions_boost` "
                  "{id:promise}, `constraints` [str], `assumptions` [str], `fields_add`/`fields_remove` "
                  "[str], `hypotheses_pin` [id], `hypotheses_unbin` [id], `hypotheses_verdict` "
                  "[{hypothesis_id,verdict,note}], `artifacts_request` [{spec,kind}], "
                  "`budget_delta` num, `control` continue|stop_after_round|finalize_now."]
        (self.run_dir / "steer_request.md").write_text("\n".join(lines), encoding="utf-8")

    def _guardrails(self) -> str:
        """Scope + assumptions as a prompt guardrail block, injected into research/judge executors."""
        return self.ledger.guardrails_md()

    # ── PLAN: the agent ranks the frontier AND allocates the round's money ─────
    def _reset_root_direction(self) -> None:
        """ABLATION (no-directions): keep exactly one OPEN direction — the user's own question — so
        the loop always regenerates hypotheses from it instead of from a growing frontier."""
        from .ledger import OPEN as _OPEN, CLOSED as _CLOSED
        root = None
        for d in self.ledger.directions.values():
            if d.rationale == "ABLATION root (the question itself)":
                root = d
            else:
                d.status = _CLOSED
        if root is None:
            root = self.ledger.add_directions(
                [{"question_text": self.q, "rationale": "ABLATION root (the question itself)",
                  "promise": 1.0}])[0]
            root.rationale = "ABLATION root (the question itself)"
        root.status = _OPEN
        root.promise = 1.0

    def _plan_batch(self) -> list[tuple[Direction, float]]:
        """Return [(direction, usd)] for this round. The embedding pre-rank only narrows the
        frontier to a readable shortlist; the *agent* then decides both the order and the money.
        The harness clamps each allocation to a ceiling — a share of the round's pot, so one
        direction can never eat the run — and enforces it with the per-task USD watchdog."""
        opens = self.ledger.open_directions()
        if not opens:
            return []
        pot = self._round_explore_pot()
        if pot < self.cfg.explore_min_usd:
            return []

        promise = measure.score_frontier(self.embedder, self.ledger, opens,
                                         self.explored_texts, self.uncovered_fields)
        self._charge_embed()
        # Hierarchy boost (direction→hypotheses): prioritise an open direction that digs deeper into
        # a PARENT direction whose own hypotheses came back thin (nothing pooled) or contested.
        if self.cfg.niche_boost > 0:
            ds = self.ledger.direction_scores()
            for d in opens:
                parent = ds.get(d.parent_id)
                if parent and (parent["thin"] or parent["contested"]):
                    promise[d.id] = min(1.0, promise.get(d.id, d.promise) + self.cfg.niche_boost)
        for d in opens:
            if d.id in promise:
                d.promise = promise[d.id]
        # Human-steered directions are funded first: pin their promise high so they lead the ranking
        # (and thus get an allocation this round) — the user asked for them explicitly.
        for d in opens:
            if getattr(d, "origin", "") == "human":
                d.promise = max(d.promise, 0.99)
        ranked = sorted(opens, key=lambda d: d.promise, reverse=True)
        shortlist = (ranked if len(ranked) <= self.cfg.rerank_direct_max
                     else ranked[:self.cfg.rerank_pool])
        ceiling = pot * self.cfg.alloc_ceiling_frac

        alloc: dict[str, dict] = {}
        if self.cfg.ablate == "no-alloc":
            # ABLATION: the frontier is still ranked, but the agent no longer decides the money —
            # the round's pot is split equally across the top-K, with no ceiling reasoning.
            take = shortlist[:max(1, self.cfg.K)]
            share = pot / len(take)
            self.log(f"  PLAN: SKIPPED pricing (ablate=no-alloc) — ${pot:.2f} split equally, "
                     f"${share:.2f} x {len(take)}")
            return [(d, share) for d in take]
        if len(shortlist) > 1 and self.budget.remaining() > self.cfg.plan_task_usd:
            alloc, usd = executors.plan(
                self.q, [(d.id, d.question_text, d.rationale) for d in shortlist],
                pot, ceiling, self.cfg.K, self._task_dir(f"plan_r{self.round}"),
                uncovered=self.uncovered_fields, **self._kw(self.cfg.plan_task_usd))
            self.budget.spend("plan", usd or 0.0)
            for d in shortlist:
                if d.id in alloc:
                    d.promise = alloc[d.id]["score"]
            ranked = sorted(opens, key=lambda d: d.promise, reverse=True)

        # Clamp and pay out. Ceiling only — the agent may fund a direction as thinly as it likes,
        # and a direction it priced below explore_min_usd is simply left open for a later round.
        out: list[tuple[Direction, float]] = []
        left = pot
        for d in ranked:
            if len(out) >= self.cfg.K or left < self.cfg.explore_min_usd:
                break
            a = alloc.get(d.id)
            want = a["usd"] if a else self.cfg.explore_default_usd
            usd = min(want, ceiling, left)
            if usd < self.cfg.explore_min_usd:
                continue
            d.allocated_usd = usd
            d.alloc_rationale = (a or {}).get("rationale", "harness default (planner did not price it)")
            out.append((d, usd))
            left -= usd
        if out:
            self.log(f"  PLAN: ${pot:.2f} pot, ${ceiling:.2f} ceiling → "
                     + "; ".join(f"{d.id} ${u:.2f} ({d.alloc_rationale[:48]})" for d, u in out))
        else:
            # Say WHY nothing was funded. An empty plan ends the loop, so a run that stopped here
            # because the ceiling fell below the launch minimum otherwise looks like convergence —
            # it reports "0 rounds" with open directions and no explanation.
            need = self.cfg.explore_min_usd / max(1e-9, self.cfg.explore_round_frac
                                                  * self.cfg.alloc_ceiling_frac)
            self.log(f"  PLAN: nothing fundable — ${pot:.2f} pot gives a ${ceiling:.2f} per-direction "
                     f"ceiling, under the ${self.cfg.explore_min_usd:.2f} launch minimum. "
                     f"{len(opens)} direction(s) stay OPEN and UNEXPLORED; exploring needs "
                     f"~${need:.2f} remaining.")
        return out

    # ── niche spreading (aspect diversity when ordering the test queue) ───────
    @staticmethod
    def _niche(h: Hypothesis) -> str:
        """A hypothesis's niche descriptor = its primary aspect (the QD behaviour space)."""
        return h.aspects[0].strip().lower() if h.aspects else "(none)"

    def _spread(self, ordered: list[Hypothesis]) -> list[Hypothesis]:
        """Reorder a priority-sorted list to round-robin across niches. Everything is still tested —
        this only decides WHO GOES FIRST, so if the budget dies mid-queue the tests that did run
        span the aspects instead of piling into one crowded topic."""
        by_niche: dict[str, list[Hypothesis]] = {}
        for h in ordered:
            by_niche.setdefault(self._niche(h), []).append(h)
        out: list[Hypothesis] = []
        while any(by_niche.values()):
            for lst in by_niche.values():
                if lst:
                    out.append(lst.pop(0))
        return out

    # ── STAGE 1: screen ───────────────────────────────────────────────────────
    def _screen(self, hyps: list[Hypothesis]) -> None:
        """Every proposed hypothesis gets a cheap web search: does this make sense at all? There is
        no gate deciding which ones are worth screening — screening IS the gate, and it is cheap
        enough to run on everything."""
        queue = self._spread(sorted(hyps, key=lambda h: -h.confidence))
        if not queue:
            return
        cap = self.cfg.screen_task_usd
        passed = 0
        while queue and self.budget.remaining() >= cap:
            wave = [queue.pop(0) for _ in range(min(self.cfg.concurrency, len(queue)))]
            jobs = [(executors.screen, (h, self.q, self._task_dir(f"screen_{h.id}", h.text)),
                     {**self._kw(cap), "budget_hint": cap * 0.8, "guardrails": self._guardrails()})
                    for h in wave]
            for h, res in zip(wave, self._run_parallel(jobs)):
                r = self._take(res, phase="screen")
                if r is None:
                    continue                    # task died: leave it PROPOSED, retry next round
                passed += bool(self.ledger.apply_screen(h, r))
        if queue:
            self.log(f"  SCREEN: budget ran out with {len(queue)} hypotheses unscreened "
                     f"(they stay PROPOSED and are reported as untested)")
        self.log(f"  SCREEN: {passed} passed / {len(hyps) - len(queue)} screened "
                 f"(${self.budget.by_phase['screen']:.2f} total)")

    # ── STAGE 2: the in-depth test ────────────────────────────────────────────
    def _deep_test(self, hyps: list[Hypothesis]) -> None:
        """Every hypothesis that passed the screen gets the deep test — an extensive hunt for both
        evidence and counter-examples. Nothing rations this: no beam width, no error budget, no
        promotion score. Supported and uncontradicted → the pool; anything else → the bin, with its
        reason, plus a bounded re-investigation direction so the loop can try to resolve it."""
        queue = self._spread(sorted(hyps, key=lambda h: -h.confidence))
        if not queue:
            return
        cap = self.cfg.deep_task_usd
        pooled = binned = 0
        while queue and self.budget.remaining() >= cap:
            wave = [queue.pop(0) for _ in range(min(self.cfg.concurrency, len(queue)))]
            jobs = []
            for h in wave:
                prior = "\n".join(
                    f"- [{e.stance}] {e.text}  (src: {e.source.doi or e.source.pmid or e.source.url})"
                    for e in self.ledger.evidence_for(h)) or "(none yet — find your own)"
                jobs.append((executors.deep_test, (h, self.q, prior, self._task_dir(f"deep_{h.id}", h.text)),
                             {**self._kw(cap), "budget_hint": cap * 0.8,
                              "guardrails": self._guardrails()}))
            for h, res in zip(wave, self._run_parallel(jobs)):
                r = self._take(res, phase="deep")
                if r is None:
                    continue                    # task died: stays SCREENED, retried next round
                followup = self.ledger.apply_deep(h, r, max_attempts=self.cfg.retest_max_attempts)
                self.ledger.add_directions(r.get("new_directions"), parent_id=h.direction_id)
                if followup is not None:
                    followup.promise = min(1.0, followup.promise + 0.1)
                pooled += h.status == POOLED
                binned += h.status == BINNED
        if queue:
            self.log(f"  DEEP: budget ran out with {len(queue)} screened hypotheses untested "
                     f"(they stay SCREENED and are reported as untested)")
        self.log(f"  DEEP: {pooled} → pool, {binned} → bin "
                 f"(${self.budget.by_phase['deep']:.2f} total)")

    # ── resurfacing: fresh evidence pulls hypotheses back out of the bin ──────
    def _rescore_corroboration(self) -> None:
        """The bin is not a grave. When evidence gathered for one hypothesis independently supports
        a BINNED one, that hypothesis's confidence rises; past unbin_thresh it returns to the test
        queue for another deep test. Discovery uses the embedder (cosine); the independent-source
        filter and the capped bump live in ledger.corroborate."""
        if not self.cfg.corroborate_enabled:
            return
        binned = [h for h in self.ledger.binned() if not h.pinned]
        if not binned:
            return
        # only evidence not already attached to a binned hypothesis can corroborate it
        pool_ev = [e for e in self.ledger.evidence.values()
                   if e.stance == SUPPORTS and e.resolvable()]
        if not pool_ev:
            return
        texts = [h.text for h in binned]
        bumped, unbinned = 0, 0
        for ev in pool_ev:
            for i, cos in self.embedder.rank(ev.text, texts):
                if cos < self.cfg.corroborate_thresh:
                    break                      # rank() is sorted desc — nothing else clears the bar
                h = binned[i]
                if ev.hypothesis_id == h.id:
                    continue
                if self.ledger.corroborate(h, [ev], per_source=self.cfg.corroborate_per_source) > 0:
                    bumped += 1
                    if h.confidence >= self.cfg.unbin_thresh and h.test_attempts <= self.cfg.retest_max_attempts:
                        self.ledger.unbin(h, reason=f"independent corroboration (conf {h.confidence:.2f})")
                        unbinned += 1
        if bumped:
            self._charge_embed()
            self.log(f"  corroboration: raised {bumped} binned hypothesis/es on independent "
                     f"evidence; {unbinned} resurfaced for another test")

    # ── measurement (§7 revised: ONE coverage judge + counts → a Snapshot) ────
    def _measure(self, tag: str) -> metrics.Snapshot:
        cj = self._take(self._run_parallel([(executors.judge_coverage,
                        (self.ledger, self._task_dir(f"judge_cov_{tag}")), self._kw())])[0],
                        phase="measure")
        cov, uncovered = 0.0, list(self.ledger.required_fields)
        if cj is not None:
            cov, uncovered = measure.coverage_from_judge(cj.get("fields"), self.ledger.required_fields)
        self.uncovered_fields = uncovered
        prev = self.snapshots[-1] if self.snapshots else None
        backlog = len(self.ledger.pending_screen()) + len(self.ledger.pending_deep())
        snap = metrics.build_snapshot(
            self.ledger, self.budget.spent, coverage=cov, uncovered=uncovered,
            backlog=backlog, prev=prev, new_hypotheses=self._new_hypotheses,
            progress_eps=self.cfg.progress_eps)
        self.snapshots.append(snap)
        self._new_hypotheses = 0
        return snap

    # ── CHECKPOINT (§7 revised) ───────────────────────────────────────────────
    def _checkpoint(self) -> bool:
        snap = self._measure(tag=f"cp{len(self.snapshots) + 1}")
        self.log(f"CHECKPOINT {len(self.snapshots)}: coverage={snap.coverage:.2f} "
                 f"({snap.n_covered}/{snap.n_asks})  quality={snap.quality:.2f} "
                 f"({snap.n_pooled} pooled / {snap.n_binned} binned "
                 f"[{snap.n_conflicted} contested, {snap.n_refuted} refuted], untested {snap.backlog})  "
                 f"progress={snap.progress:.4f}/$  answeredness={snap.answeredness:.2f}  ${snap.cost:.2f}")
        if snap.uncovered:
            self.log(f"  uncovered asks: {snap.uncovered}")

        # Steer: when progress stalls with the question still incomplete, that's shallow
        # saturation — DIG DEEPER (don't stop). Distil cross-cutting abstract patterns; their
        # `direction`/`hypothesis` fields seed genuinely new, non-obvious frontier directions.
        if snap.stalled and self.budget.remaining() > self.cfg.explore_min_usd:
            self.log("  STALLED (progress~0, coverage<1): distilling abstract patterns to dig deeper")
            pr = self._take(self._run_parallel([(executors.patterns,
                            (self.ledger, self._task_dir(f"patterns_{len(self.snapshots)}")), self._kw())])[0],
                            phase="measure")
            if pr is not None:
                rows = self.ledger.add_patterns(pr.get("patterns"))
                spawned = self.ledger.spawn_from_patterns(rows)
                for d in spawned:
                    d.promise = min(1.0, d.promise + 0.1)
                self.log(f"  +{len(spawned)} deeper directions from {len(rows)} cross-cutting patterns")

        # Honor human steer: never converge while a human-added direction is still unexplored — the
        # user explicitly asked for it, and the (backward-looking) progress metric can't know it would
        # yield new findings. Agent-generated frontier directions are still subject to the progress/
        # coverage stop (that's the intended budget-efficiency behavior).
        open_human = [d for d in self.ledger.open_directions()
                      if getattr(d, "origin", "") == "human"]
        # Converge ONLY when the question is fully answered, everything's tested, and
        # nothing new is coming. Progress~0 alone is NOT done (see stall handling above).
        converged = (self.ledger.required_fields                # never "converge" with 0 asks (fields failed)
                     and snap.coverage >= 0.999 and snap.backlog == 0
                     and snap.progress <= self.cfg.progress_eps
                     and not open_human)
        if converged:
            self.log("CONVERGED: all asks answered + every hypothesis tested + no new progress.")
        elif open_human and snap.coverage >= 0.999 and snap.backlog == 0:
            self.log(f"  not converging: {len(open_human)} human-steered direction(s) still to explore.")
        return converged

    # ── FINALIZE (§4) ─────────────────────────────────────────────────────────
    def finalize(self, converged: bool) -> None:
        # The search-baseline ablations hold no beliefs: their report is the answers they collected,
        # stitched together, with the bibliography the harness builds from the sources they cited.
        notes = getattr(self, "_ablation_notes", None)
        if notes is not None:
            body = (f"# {self.q}\n\n"
                    f"*Produced by the `{self.cfg.ablate}` ablation: literature search only — no "
                    f"hypotheses, no evidence adjudication, nothing verified against "
                    f"counter-evidence.*\n\n" + "\n\n---\n\n".join(notes))
            try:
                from . import refs as _refs
                if _refs.available():
                    _refs.enrich_all(self.ledger.reference_objs())
                body, _ = _refs.scrub_unknown_citations(body)
            except Exception as e:                       # noqa: BLE001
                self.log(f"  reference hygiene skipped ({type(e).__name__})")
            rm = self.ledger.references_md()
            if rm:
                body += "\n\n" + rm
            (self.run_dir / "answer.md").write_text(body, encoding="utf-8")
            self.log(f"FINALIZE ({self.cfg.ablate}): {len(notes)} section(s), "
                     f"{len(self.ledger.reference_objs())} sources, spent ${self.budget.spent:.2f}")
            self._save()
            return
        # Last chance to test anything still outstanding — testing is never skipped by design,
        # so it only ends up here if the budget genuinely ran out mid-round.
        self._screen(self.ledger.pending_screen())
        if self.cfg.ablate != "no-verifier":
            self._deep_test(self.ledger.pending_deep())
        else:
            self.ledger.accept_screened(self.ledger.pending_deep())
        phases = "  ".join(f"{k} ${v:.2f}" for k, v in self.budget.by_phase.items() if v > 0)
        self.log(f"FINALIZE: converged={converged} spent=${self.budget.spent:.2f}  ({phases})")

        # Cross-cutting patterns for the synthesis section (if the loop never stalled into them).
        if not self.ledger.patterns and self.budget.remaining() > 0:
            pr = self._take(self._run_parallel([(executors.patterns,
                            (self.ledger, self._task_dir("patterns_final")), self._kw())])[0],
                            phase="finalize")
            if pr is not None:
                self.ledger.add_patterns(pr.get("patterns"))

        # Outline-then-fill report (LLM); deterministic synthesis is the fallback.
        answer = None
        fr = self._take(self._run_parallel([(executors.finalize_report,
                        (self.q, self.ledger, self.ledger.patterns,
                         self._task_dir("finalize_report")), self._kw())])[0], phase="finalize")
        if fr is not None and fr.get("report_markdown"):
            (self.run_dir / "outline.json").write_text(
                json.dumps(fr.get("outline"), indent=2), encoding="utf-8")
            body = fr["report_markdown"].rstrip()
            # Always use the harness's deduped, guaranteed-accurate bibliography. If the LLM wrote its own
            # References/Sources section it will contain the same paper under multiple locators (arXiv vs
            # published vs PDF), so strip it and append the deterministic one instead.
            body = re.sub(r"\n#{1,6}\s*(references|sources|bibliography)\b.*$", "",
                          body, flags=re.IGNORECASE | re.DOTALL).rstrip()
            # Fill in missing author/year/venue on the bibliography via clibib, so there are no
            # "Unknown / n.d." entries. Best-effort + network-bounded; skips already-complete refs.
            try:
                from . import refs as _refs
                if _refs.available():
                    objs = self.ledger.reference_objs()
                    changed = _refs.enrich_all(objs)
                    if changed:
                        self.log(f"  enriched {changed} reference(s) via clibib")
            except Exception as e:  # noqa: BLE001 — enrichment must never break finalize
                self.log(f"  reference enrichment skipped ({type(e).__name__})")
            refs = self.ledger.references_md()
            if refs:
                body += "\n\n" + refs
            # Data findings get their own provenance section: not citations, but the operations
            # that produced them plus the assumptions those made (DESIGN_data_plane.md §6).
            data_md = self.ledger.data_sources_md()
            if data_md:
                body += "\n\n" + data_md
            answer = body
            self.log(f"  outline: {len(fr.get('outline') or [])} sections; report {len(body)//1024}KB")
        if not answer:
            self.log("  finalize LLM failed → deterministic synthesis fallback")
            answer = self.ledger.synthesize()
        # Final reference hygiene, applied to whichever report we ended up with: strip placeholder
        # citations the writer may have copied into the prose, then assert none survived. The
        # bibliography itself is already clean (clibib enrichment + publisher fallback for
        # author-less database/web records).
        try:
            from . import refs as _refs
            answer, n_scrubbed = _refs.scrub_unknown_citations(answer)
            if n_scrubbed:
                self.log(f"  scrubbed {n_scrubbed} placeholder citation(s) from the report")
            left = _refs.count_unknowns(answer)
            if left:
                self.log(f"  WARNING: {left} unresolved 'Unknown' reference(s) remain in the report")
        except Exception as e:  # noqa: BLE001 — hygiene must never break finalize
            self.log(f"  citation scrub skipped ({type(e).__name__})")
        (self.run_dir / "answer.md").write_text(answer, encoding="utf-8")
        # Keep a versioned history: each finalize (initial run + every resume) is a report version.
        try:
            vdir = self.run_dir / "reports"
            vdir.mkdir(exist_ok=True)
            ip = vdir / "index.json"
            idx = json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else []
            v = len(idx) + 1
            (vdir / f"v{v}.md").write_text(answer, encoding="utf-8")
            idx.append({"v": v, "round": self.round, "spent": round(self.budget.spent, 2),
                        "converged": bool(converged), "created": time.strftime("%Y-%m-%dT%H:%M:%S")})
            ip.write_text(json.dumps(idx, indent=2), encoding="utf-8")
        except Exception:
            pass
        snap = self._measure(tag="final")
        self._save()
        self._finalize_workspace(answer)
        ans_per_dollar = snap.answeredness / self.budget.spent if self.budget.spent > 0 else 0.0
        self.log(f"DONE: coverage {snap.n_covered}/{snap.n_asks}  "
                 f"quality {snap.quality:.2f} ({snap.n_pooled} pooled / {snap.n_binned} binned, "
                 f"untested {snap.backlog})  answeredness={snap.answeredness:.2f}  "
                 f"unsourced={snap.unsourced:.2f}  answeredness/$={ans_per_dollar:.4f}")

    def _finalize_workspace(self, answer: str) -> None:
        """Close the workspace out. Every run — steered or not — ends with a committed snapshot of
        the report plus machine-readable findings/evidence/metrics CSVs, which costs $0. Only the
        bespoke deliverables (queued requests, and the auto pass) spend money."""
        if self.ws is None:
            return
        self._ws_export(report=answer)
        sha = self.ws.commit(f"run: finalize (round {self.round}, ${self.budget.spent:.2f})")
        self.log(f"  workspace: data export committed{f' [{sha[:8]}]' if sha else ''}"
                 f" → {self.ws.root}")
        self._service_artifacts("finalize")          # user requests first — they were asked for
        if (self.cfg.auto_artifacts and not self._artifact_requests
                and self.budget.remaining() >= self.cfg.artifact_task_usd):
            self._build_artifact({"spec": executors.AUTO_ARTIFACT_SPEC, "kind": "", "auto": True},
                                 "finalize")
        self.ws.write_index(self.artifacts)
        self.ws.commit("workspace: refresh artifact index")
        self._save_artifacts()
        if self.artifacts:
            self.log(f"ARTIFACTS: {len(self.artifacts)} in {self.ws.root}/ — "
                     + ", ".join(a["path"] for a in self.artifacts[-6:]))

    def _run_meta(self) -> dict:
        return {
            "question": self.q, "round": self.round,
            "budget": {"total": self.budget.total, "spent": self.budget.spent,
                       "by_phase": dict(self.budget.by_phase),
                       "embeddings": self.embedder.spent_usd},
            "allocations": [{"direction": d.id, "question": d.question_text,
                             "allocated": d.allocated_usd, "spent": d.spent_usd,
                             "rationale": d.alloc_rationale}
                            for d in self.ledger.directions.values() if d.allocated_usd],
            "patterns": len(self.ledger.patterns),
            "artifacts": len(self.artifacts),
            "avg_explore_cost": self._avg(self.explore_costs, self.cfg.explore_default_usd),
            "avg_test_cost": self._avg(self.test_costs, self.cfg.deep_task_usd),
            "snapshots": [s.__dict__ for s in self.snapshots],
            "config": {k: v for k, v in self.cfg.__dict__.items()},
            "state": self._state(),
        }

    def _save(self) -> None:
        self.ledger.save(self.run_dir / "ledger.json")
        (self.run_dir / "run.json").write_text(json.dumps(self._run_meta(), indent=2), encoding="utf-8")
        self._save_artifacts()

    def _save_artifacts(self) -> None:
        """The artifact index, next to ledger.json so a UI can list deliverables without git."""
        if self.ws is None:
            return
        try:
            (self.run_dir / "artifacts.json").write_text(json.dumps({
                "workspace": str(self.ws.root),
                "artifacts": self.artifacts,
                "pending": self._artifact_requests,
                "commits": self.ws.log(40),
            }, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _state(self) -> dict:
        """Full runtime state beyond the ledger — everything resume() needs to continue mid-flight.
        The test queues are NOT stored: they are derived from hypothesis status, so a resumed run
        rediscovers exactly what is still untested."""
        return {
            "round": self.round,
            "uncovered_fields": self.uncovered_fields,
            "explored_texts": self.explored_texts,
            "explore_costs": self.explore_costs,
            "test_costs": self.test_costs,
            "task_n": self._task_n,
            "new_hypotheses": self._new_hypotheses,
            "artifact_requests": self._artifact_requests,   # unbuilt deliverables survive a resume
            "datasets": self.datasets,       # the staged inputs + their content digests
            "route": self.route,             # how this request was routed (§3.2)
            "last_checkpoint_spend": self.last_checkpoint_spend,
            "budget_total": self.budget.total,
            "budget_spent": self.budget.spent,
            "budget_by_phase": dict(self.budget.by_phase),
        }

    # ── resume a paused run (DESIGN_interactive.md §4.3) ──────────────────────
    @classmethod
    def resume(cls, run_dir, cfg: Config, steer: SteerSource | None = None) -> "Orchestrator":
        """Rehydrate a paused run from its run-dir and continue. The ledger round-trips via from_json;
        this restores the runtime state that lives outside it. Call resume_run() to continue the loop."""
        run_dir = Path(run_dir)
        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        ledger = Ledger.from_json(json.loads((run_dir / "ledger.json").read_text(encoding="utf-8")))
        st = meta.get("state") or {}
        orch = cls(ledger.question, run_dir, cfg, steer=steer)
        orch.ledger = ledger          # from_json already restored the id sequences
        orch.round = int(st.get("round", 0))
        orch.uncovered_fields = list(st.get("uncovered_fields") or list(ledger.required_fields))
        orch.explored_texts = list(st.get("explored_texts") or [])
        orch.explore_costs = list(st.get("explore_costs") or [])
        orch.test_costs = list(st.get("test_costs") or [])
        orch._task_n = int(st.get("task_n", 0))
        orch._new_hypotheses = int(st.get("new_hypotheses", 0))
        orch.last_checkpoint_spend = float(st.get("last_checkpoint_spend", 0.0))
        orch.budget.total = float(st.get("budget_total", cfg.budget))
        orch.budget.spent = float(st.get("budget_spent", 0.0))
        orch.budget.by_phase.update(st.get("budget_by_phase") or {})
        orch._emb_charged = 0.0    # fresh embedder starts at 0; past embed spend is already in spent
        orch.snapshots = [metrics.Snapshot(**s) for s in (meta.get("snapshots") or [])]
        orch._artifact_requests = list(st.get("artifact_requests") or [])
        orch.datasets = list(st.get("datasets") or [])       # inputs are already staged on disk
        orch.route = dict(st.get("route") or {})
        orch.ledger.datasets = list(orch.datasets)
        try:      # the artifact index lives beside the ledger; the workspace itself is on disk
            ai = json.loads((run_dir / "artifacts.json").read_text(encoding="utf-8"))
            orch.artifacts = list(ai.get("artifacts") or [])
        except (OSError, json.JSONDecodeError):
            orch.artifacts = []
        untested = len(ledger.pending_screen()) + len(ledger.pending_deep())
        orch.log(f"RESUME: round={orch.round} spent=${orch.budget.spent:.2f} "
                 f"hypotheses={len(ledger.hypotheses)} ({len(ledger.pool())} pooled, "
                 f"{len(ledger.binned())} binned, {untested} untested)")
        return orch

    def resume_run(self) -> None:
        """Continue a resumed run: drain any queued steer, loop, finalize."""
        self._ws_init()                    # idempotent; rebuilds the workspace if it was removed
        self._drain_steer("resume")
        self._service_artifacts("resume")
        self._loop()
