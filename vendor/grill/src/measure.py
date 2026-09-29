"""Semantic instruments — the embedding/judge layer that replaces every lexical proxy.

Embeddings (``embed.Embedder``) supply the methodology's `cos(emb(·), emb(·))` terms:
context selection, frontier relevance/novelty, reference recall, the discovery/novelty
curve. LLM judges (``executors.judge_*``) supply the discrete `covered(f)` and `q(d)`
terms; their reducers live here. Nothing in this module does token matching.
"""
from __future__ import annotations

import math

from .embed import Embedder
from .ledger import Direction, Hypothesis, Ledger
from .metrics import PromiseWeights


# ── context selection (§3: a *slice* of the ledger for EXPLORE) ──────────────

def select_context(emb: Embedder, direction: Direction, hypotheses: list[Hypothesis],
                   limit: int = 12) -> list[Hypothesis]:
    """Top-`limit` hypotheses by embedding cosine to the direction. If few exist,
    return them all (no judgment needed)."""
    if len(hypotheses) <= limit:
        return hypotheses
    ranked = emb.rank(direction.question_text, [h.text for h in hypotheses])
    return [hypotheses[i] for i, _ in ranked[:limit]]


# ── frontier promise (§5: rel + EIG + novelty − cost, all non-lexical) ───────

def score_frontier(emb: Embedder, ledger: Ledger, open_dirs: list[Direction],
                   explored_texts: list[str], under_covered: list[str],
                   pw: PromiseWeights = PromiseWeights()) -> dict[str, float]:
    """promise(d) = w1·rel + w2·EIG + w3·nov − w4·cost.

    rel = cosine(direction, question biased to under-covered asks);
    EIG = mean(1−conf) over the direction's hypotheses, else its self-reported promise;
    nov = 1 − max cosine(direction, any explored direction);
    cost = saturating function of est_cost.

    This is the embedding PRE-RANK. The agent's planner (executors.plan) has the final say on
    both order and money; this narrows the frontier to a shortlist the planner can afford to read.
    """
    if not open_dirs:
        return {}
    bias = ledger.question + (("\nUnder-covered asks: " + "; ".join(under_covered))
                              if under_covered else "")
    q_vec = emb.one(bias)
    expl_vecs = emb.embed(explored_texts) if explored_texts else []
    d_vecs = emb.embed([d.question_text for d in open_dirs])

    out: dict[str, float] = {}
    for d, dv in zip(open_dirs, d_vecs):
        rel = _cos(dv, q_vec)
        hyps = [ledger.hypotheses[hid] for hid in d.produced_hypotheses if hid in ledger.hypotheses]
        if hyps:
            eig = sum(1.0 - h.confidence for h in hyps) / len(hyps)
        else:
            eig = min(1.0, max(0.0, d.promise))      # unexplored: trust self-report
        nov = 1.0 - max((_cos(dv, ev) for ev in expl_vecs if ev), default=0.0)
        cost = 1.0 - math.exp(-max(0.0, d.est_cost) / 5.0)
        out[d.id] = pw.w1 * rel + pw.w2 * eig + pw.w3 * nov - pw.w4 * cost
    return out


# ── judge reducer (consume executors.judge_coverage JSON) ────────────────────

def coverage_from_judge(judge_fields: list[dict], required_fields: list[str]) -> tuple[float, list[str]]:
    """Coverage = (asks marked covered) / (total asks).  Returns (coverage, uncovered_asks)."""
    F = required_fields
    if not F:
        return 1.0, []
    covered = [f for f in (judge_fields or []) if f.get("covered")]
    uncovered = [f.get("field", "") for f in (judge_fields or []) if not f.get("covered")]
    return len(covered) / len(F), uncovered


def _cos(a, b) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
