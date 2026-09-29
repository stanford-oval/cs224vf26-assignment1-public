# Frontier selection

How the orchestrator chooses which OPEN directions to explore next each round: the embedding-based promise score, the context slice handed to each EXPLORE task, the optional LLM reranker, and the niche/hierarchy promise boost for thin or contested branches.

Related: [The orchestration loop](./orchestration-loop.md) · [The belief ledger](./belief-ledger.md) · [The executor roles](./executor-roles.md) · [Budget, cost, and the FDR brake](./budget-cost-fdr.md) · [measure.py](../modules/measure.md) · [embed.py](../modules/embed.md) · [metrics.py](../modules/metrics.md)

## What this subsystem does

The ledger holds a growing pool of *directions* — candidate sub-questions to investigate. Most are OPEN (unexplored). Each round the loop must pick a small batch of them to spend EXPLORE budget on. Frontier selection is that pick: a best-first ranking of the OPEN directions by a **promise** score, followed by an optional LLM rerank, returning the top `k`.

It is driven by one method, `Orchestrator._select_batch` (`orchestrator.py:380`), which composes three ingredients:

| Stage | Where | What it produces |
| --- | --- | --- |
| Embedding promise | `measure.score_frontier` (`measure.py:31`) | a float per OPEN direction: relevance + EIG + novelty − cost |
| Hierarchy boost | `_select_batch` + `ledger.direction_scores` (`orchestrator.py:390`, `ledger.py:399`) | additive bump for directions whose parent came back thin/contested |
| LLM rerank | `executors.rerank` (`executors.py:64`) | overrides promise with an LLM value score for a shortlist |

A separate, smaller instrument — `measure.select_context` (`measure.py:19`) — decides *which claims* travel with each selected direction into its EXPLORE call.

Both instruments are purely semantic: every similarity term is an embedding cosine (`embed.py`), never token overlap.

## The promise function

`score_frontier` computes, for each OPEN direction `d`:

```
promise(d) = w1·rel  +  w2·EIG  +  w3·nov  −  w4·cost
```

The weights live in `PromiseWeights` (`metrics.py:26`), defined in `metrics.py` only so selection stays tunable — they are unrelated to the checkpoint metrics in the same module.

| Term | Default weight | Definition (`measure.py`) | Intuition |
| --- | --- | --- | --- |
| `rel` | `w1 = 0.35` | cosine(direction, question **biased toward under-covered asks**) (`measure.py:51`) | on-topic, and steered at the gaps |
| `EIG` | `w2 = 0.30` | mean `(1 − confidence)` over the direction's produced claims; if none yet, `min(1, max(0, d.promise))` (`measure.py:54`, `measure.py:56`) | expected information gain — how much uncertainty it can still resolve |
| `nov` | `w3 = 0.25` | `1 − max cosine(direction, any already-explored direction)` (`measure.py:57`) | not a rehash of ground already covered |
| `cost` | `w4 = 0.10` | `1 − exp(−max(0, est_cost)/5)` — a saturating penalty (`measure.py:58`) | cheap directions preferred, but the penalty flattens out |

Two details worth stating explicitly:

- **Relevance is biased, not raw.** The query vector is not the bare question. It is `ledger.question` plus, if any asks are still uncovered, a line `"\nUnder-covered asks: " + "; ".join(under_covered)` (`measure.py:43`). So relevance tilts toward whatever the required-fields checkpoint has *not* yet answered. The caller passes `self.uncovered_fields`, which starts as the full required-fields list at INIT (`orchestrator.py:248`) and is refreshed from the coverage judge after each checkpoint (`orchestrator.py:612`).
- **EIG degrades to self-report for fresh directions.** A direction that has produced claims is scored by how *unconfirmed* those claims are (mean `1 − confidence`). An unexplored direction has no claims, so it falls back to its own declared `promise` field (whatever the executor that spawned it asserted).

```
                        ledger.question
                              │
        under_covered ──►  bias string  ──►  emb.one()  ──►  q_vec
                                                               │
  for each OPEN direction d:                                   │
     d.question_text ──► emb.embed() ──► d_vec ──┬── cos(d_vec, q_vec) ─► rel
                                                 ├── mean(1−conf) / promise ─► EIG
     explored_texts ──► emb.embed() ─► e_vecs ───┴── 1 − max cos(d_vec,·) ─► nov
                                                     1 − exp(−est_cost/5) ─► cost
                                                               │
                          promise[d.id] = w1·rel + w2·EIG + w3·nov − w4·cost
```

Every embedding call made here is billed to the explore budget pool via `_charge_embed` right after scoring (`orchestrator.py:386`, helper at `orchestrator.py:191`).

## The niche / hierarchy boost

After the raw promise map is computed, `_select_batch` optionally nudges directions that follow up on an inconclusive parent (Component C, the two-level direction→claims hierarchy). Gated on `cfg.niche_boost > 0` (default `0.15`, `orchestrator.py:113`).

It reads `ledger.direction_scores` (`ledger.py:399`), which scores each direction by *its own* produced claims:

| Field | Definition (`ledger.py:412`) |
| --- | --- |
| `strength` | `confirmed / (confirmed + refuted)`, or `0` if nothing checked |
| `thin` | has claims **and** `confirmed == 0` — explored but nothing held up |
| `contested` | `checked >= 2` **and** `0.34 <= strength <= 0.66` — confirmed ≈ refuted |

For each OPEN direction `d`, the code looks up **its parent's** score. If the parent is `thin` or `contested`, `d` gets `promise[d.id] = min(1.0, promise + niche_boost)` (`orchestrator.py:395`). The effect: when a branch of the investigation came back inconclusive, its follow-up directions are prioritised so the loop digs deeper exactly where the evidence is weak or split, rather than moving on.

Note this is the *primary* hierarchy (direction → claims). It is distinct from the aspect-based promotion diversity tie-breaker, which is `Orchestrator._niche` + `_pick_spread` — see [Promotion and verification](./promotion-and-verification.md). (`ledger.niche_scores()` exists but is currently unused; it is not the tie-breaker.)

## The LLM reranker

Embedding cosine is a cheap ranker but a coarse one. When affordable, `_select_batch` replaces the promise ordering with a direct LLM value judgement over a shortlist (`orchestrator.py:404`).

Config knobs (`orchestrator.py:115-117`):

| Knob | Default | Meaning |
| --- | --- | --- |
| `rerank_frontier` | `True` | opt in to the LLM rerank at all |
| `rerank_direct_max` | `60` | if OPEN count `<= this`, rerank the whole frontier directly |
| `rerank_pool` | `50` | otherwise, embedding-promise pre-filters to this top-N, then rerank those |

Gate: it runs only when `rerank_frontier` is on, there is more than one OPEN direction, and `budget.explore_remaining() > cap`, where `cap = ground_task_usd * task_cap_mult` (`orchestrator.py:403`). So a nearly-exhausted budget skips the extra reason call.

```
ranked (by embedding promise, desc)
        │
        ├─ len(ranked) <= rerank_direct_max (60)? ──► pool = ranked   (rank all)
        └─ else                                   ──► pool = ranked[:rerank_pool]  (top 50)
                                                       │
                     executors.rerank(question, [(id, question_text) …])   ← one "reason" call, no tools
                                                       │
                     scores{id: [0,1]}  ──►  d.promise = score  (for d in pool)
                                                       │
                              re-sort OPEN directions by promise, return top k
```

`executors.rerank` (`executors.py:64`) sends the shortlist as an `id=…: text` listing and asks the model to score each candidate in `[0,1]` — rewarding relevance, non-redundancy, and likely payoff — under the `RERANK` schema (`schemas.py:135`, `{rankings: [{id, score}]}`). It runs `mode="reason"` (no web tools) and returns `({id: score}, usd)`; the cost is charged to the explore pool. Only directions in the pool are rescored, so a large frontier's tail keeps its embedding-derived promise.

The final return is `ranked[:k]` (`orchestrator.py:413`). The batch size `k` itself is decided upstream by the round loop from remaining explore budget and per-task cap (`orchestrator.py:330-333`), not here — see [The orchestration loop](./orchestration-loop.md).

## Context selection for EXPLORE

Choosing a direction is only half the job; each selected direction is dispatched with a *slice* of the ledger's claims so the executor has relevant prior findings without being flooded. That is `measure.select_context` (`measure.py:19`), called per direction in the round loop (`orchestrator.py:345`):

- Takes the direction and the full claim list (`ledger.all_claims()`).
- If there are `<= limit` claims (default `limit = 12`), returns them all — no ranking needed.
- Otherwise ranks all claims by embedding cosine to `direction.question_text` (via `emb.rank`) and returns the top `limit`.

This is the only place claim→direction relevance is computed for dispatch, and again it is pure cosine.

## The embedder

All cosines above run through one `Embedder` (`embed.py:32`), constructed once per run (`orchestrator.py:157`).

| Property | Value | Source |
| --- | --- | --- |
| Model | `text-embedding-3-large` | `embed.py:14` |
| Price | `0.13 / 1e6` USD per token | `embed.py:15` |
| Cache | in-memory `dict[text → vector]`; repeated comparisons are free | `embed.py:36`, `embed.py:62` |
| Batching | up to 256 texts per API call | `embed.py:63` |
| Empty text | maps to a zero/`None` vector (cosine → 0) | `embed.py:74` |

Endpoint resolution (`embed.py:41`): if `OPENAI_BASE_URL` + `OPENAI_API_KEY` are set it uses that OpenAI-compatible proxy verbatim; otherwise it falls back to the Azure docuset endpoint with an `/openai/v1` suffix. Config comes from a `.env` file whose values **override** ambient environment variables (`embed.py:29`), so a stale exported key can't shadow it.

`Embedder.spent_usd` accumulates as vectors are created; the orchestrator reconciles that running total into the explore pool through `_charge_embed` (`orchestrator.py:191`), which charges only the delta since the last reconciliation.

The methods actually used by frontier selection are `embed`, `one`, and `rank` (the last backing `select_context`). `Embedder.cos` and `Embedder.max_sim` (`embed.py:80`, `embed.py:84`) exist but are not called from the selection path.

## Honest notes on wiring

- **`ledger.top_k_open` is not the frontier path.** `Ledger.top_k_open(k, score)` (`ledger.py:422`) is a generic best-first helper, but `_select_batch` does its own scoring, boosting, reranking, and sorting inline and never calls it. Treat `top_k_open` as an unused convenience method, not the live selection code.
- **The reranker overrides, it does not blend.** For directions in the rerank pool, the LLM score fully *replaces* `d.promise`; the embedding promise for those directions survives only as the shortlisting order, not as a component of the final score.
- **EIG for unexplored directions is self-reported.** Because a fresh direction has no claims, its EIG term is just the `promise` value the spawning executor emitted. That number is an unverified model assertion until the direction is explored and produces claims.
- **`select_context`'s `limit` is fixed in code.** The `limit = 12` default (`measure.py:20`) is not exposed as a `Config` knob; the caller uses the default.
