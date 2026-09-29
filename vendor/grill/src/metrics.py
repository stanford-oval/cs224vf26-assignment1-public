"""In-loop checkpoint metrics — deliberately SIMPLE (Methodology §7, revised).

Two scored dimensions + one progress signal, all plain counts (one LLM judge total):

  Coverage  = asks_answered / total_asks            (judge over the explicit asks)
  Quality   = pooled / (pooled + binned)             (test survival rate; untested = backlog)
  Progress  = (Δ asks_answered + Δ pooled) / Δ$      (still buying answers per dollar?)

  Answeredness = Coverage × Quality                  (optional single number that MEANS something:
                                                       share of the question answered AND tested)

Key rule: Progress ≈ 0 is "done" ONLY when Coverage is already complete. Progress ≈ 0 with
Coverage < 1 is the *stall / shallow-saturation* failure — the loop should dig deeper, not stop.

Note on Quality: the denominator counts every hypothesis that finished the two-stage test,
including the ones the screen killed. A low quality score means the agent is proposing
hypotheses that don't survive contact with the literature — which is information, not failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .ledger import Ledger, POOLED, BINNED, CONFLICTED, REFUTED


@dataclass
class PromiseWeights:
    """Weights for the embedding pre-rank of directions (measure.score_frontier) — unrelated to
    checkpoint scoring; kept here so selection stays tunable."""
    w1: float = 0.35   # relevance to under-covered question (embedding cosine)
    w2: float = 0.30   # ÊIG (uncertainty it resolves)
    w3: float = 0.25   # novelty vs explored (embedding distance)
    w4: float = 0.10   # cost penalty


def unsourced_rate(ledger: Ledger) -> float:
    """Diagnostic: fraction of TESTED hypotheses that finished with no resolvable source at all.
    Not scored — just shown. The old confabulation proxy."""
    tested = [h for h in ledger.hypotheses.values() if h.status in (POOLED, BINNED)]
    if not tested:
        return 0.0
    return sum(1 for h in tested if not h.grounded()) / len(tested)


def quality(ledger: Ledger) -> float:
    """Test survival rate: of the hypotheses that finished testing, what fraction reached the pool.
    0.0 when nothing has been tested yet (quality still unknown — see backlog)."""
    pooled = sum(1 for h in ledger.hypotheses.values() if h.status == POOLED)
    binned = sum(1 for h in ledger.hypotheses.values() if h.status == BINNED)
    return pooled / (pooled + binned) if (pooled + binned) else 0.0


@dataclass
class Snapshot:
    cost: float
    coverage: float          # asks answered / total asks
    quality: float           # pooled / (pooled + binned)
    answeredness: float      # coverage * quality
    progress: float          # (Δ covered + Δ pooled) / Δ cost  (None-safe: 0 at first cp)
    backlog: int             # hypotheses awaiting a screen or a deep test
    new_hypotheses: int      # hypotheses added since the previous checkpoint
    n_hypotheses: int
    n_pooled: int
    n_binned: int
    n_conflicted: int        # binned specifically because the literature is contested
    n_refuted: int
    n_evidence: int
    n_covered: int           # asks answered (count)
    n_asks: int
    n_open: int
    unsourced: float
    stalled: bool = False    # progress ~0 AND coverage < 1  →  shallow saturation, go deeper
    uncovered: list = field(default_factory=list)   # the asks still unanswered


def build_snapshot(ledger: Ledger, cost: float, *, coverage: float, uncovered: list,
                   backlog: int, prev: "Snapshot | None", new_hypotheses: int,
                   progress_eps: float) -> Snapshot:
    n_pooled = len(ledger.pool())
    binned = ledger.binned()
    q = quality(ledger)
    n_asks = len(ledger.required_fields)
    n_cov = round(coverage * n_asks)
    if prev is not None and cost > prev.cost:
        progress = ((n_cov - prev.n_covered) + (n_pooled - prev.n_pooled)) / (cost - prev.cost)
    else:
        progress = float("inf") if prev is None else 0.0   # first cp: unknown → treat as progressing
    stalled = (progress <= progress_eps) and (coverage < 0.999)
    return Snapshot(
        cost=cost, coverage=coverage, quality=q, answeredness=coverage * q,
        progress=(0.0 if progress == float("inf") else progress),
        backlog=backlog, new_hypotheses=new_hypotheses, n_hypotheses=len(ledger.hypotheses),
        n_pooled=n_pooled, n_binned=len(binned),
        n_conflicted=sum(1 for h in binned if h.verdict == CONFLICTED),
        n_refuted=sum(1 for h in binned if h.verdict == REFUTED),
        n_evidence=len(ledger.evidence),
        n_covered=n_cov, n_asks=n_asks,
        n_open=len(ledger.open_directions()),
        unsourced=unsourced_rate(ledger), stalled=stalled, uncovered=list(uncovered),
    )
