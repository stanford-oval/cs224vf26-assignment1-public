# orchestrator.py

This page is a top-to-bottom implementation walkthrough of `orchestrator.py`: the two budget classes, the `Config` dataclass, and every method of the `Orchestrator` — INIT, the round loop, frontier selection, the promotion posterior, the verify pool, checkpoint/convergence, and finalize. Every claim is cited as `orchestrator.py:<line>` relative to `src/`.

Related: [The orchestration loop](../architecture/orchestration-loop.md) · [Frontier selection](../architecture/frontier-selection.md) · [Promotion and verification](../architecture/promotion-and-verification.md) · [Budget, cost, and the FDR brake](../architecture/budget-cost-fdr.md) · [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) · [ledger.py](./ledger.md) · [executors.py](./executors.md) · [Config knobs (reference)](../reference/config-reference.md) · [Formal algorithm spec](../design/algorithm-spec.md)

---

## Role in the system

The orchestrator is the only stateful component. It owns the belief ledger, the budget, the FDR wealth, and the calibrator, and drives everything by dispatching **stateless** codex executor calls (`executors.py`) through a thread pool. Each executor call returns `(data, usd)`; the orchestrator charges the USD to a budget pool and ingests the data. It never calls the model directly except through those executor functions and the `Embedder`.

```
init()                      # INIT: fields + prior (parallel), ground terms, prior probe
  └─ _prior_probe()         #   seed the calibrator with (prior conf → outcome) labels
run() loop  (per round)
  ├─ _select_batch(k)       # frontier scoring (embedding) + niche boost + LLM rerank → top-k dirs
  ├─ executors.explore      # parallel EXPLORE wave, budget-sized fan-out
  ├─ ledger.ingest          # add claims + new directions with provenance
  ├─ _rescore_corroboration # bump backlog claims that fresh independent evidence supports
  ├─ _promote               # beam (top-k) + Thompson sampling → verify_queue
  ├─ _drain_verify_pool     # FDR-gated parallel VERIFY, calibrator refit
  └─ _checkpoint (periodic) # coverage judge → snapshot → steer (patterns) or converge
finalize(converged)         # final verify drain, patterns, LLM report → answer.md
```

---

## `Budget` (orchestrator.py:37-63)

Two hard-capped pools. Constructed with a total and a split `rho` (fraction going to explore); `explore_cap = total*rho`, `verify_cap = total*(1-rho)` (orchestrator.py:41-46). Embedding and judge/instrument cost is charged to the **explore** pool by convention.

| Member | Lines | Behaviour |
|---|---|---|
| `spend(pool, usd)` | 48-53 | Adds to `spent_verify` if `pool=="verify"`, else `spent_explore`. Ignores non-positive `usd`. |
| `explore_remaining()` | 55-56 | `explore_cap - spent_explore`. |
| `verify_remaining()` | 58-59 | `verify_cap - spent_verify`. |
| `spent` (property) | 61-63 | `spent_explore + spent_verify` (total spend across both pools). |

There is no shared/overflow accounting: each pool is independent, so explore cannot borrow from verify or vice versa.

## `AlphaInvesting` (orchestrator.py:120-146)

Online-FDR alpha-investing over the verification stream (Component E). A wealth pool of "error budget"; each verify invests `cost(confidence)`, a confirmation pays back `payout`.

| Member | Lines | Formula / behaviour |
|---|---|---|
| `cost(confidence)` | 133-135 | `alpha_min + alpha*(1-c)` where `c` is clamped to `[0,1]`. Speculative (low-confidence) tests cost more. |
| `can_afford(confidence)` | 137-138 | `wealth >= cost(confidence)`. |
| `settle(confidence, confirmed)` | 140-146 | Subtracts `cost`, adds `payout` if `confirmed`, floors wealth at `0.0`, returns new wealth. |

Defaults (from `Config`): `wealth0=0.5`, `alpha=0.05`, `payout=0.05`, `alpha_min=0.005`. Because payout equals alpha, a run that keeps confirming stays solvent; a run that mostly refutes bleeds wealth and eventually only affords high-confidence tests.

## `Config` (orchestrator.py:66-117)

Frozen-at-construction dataclass of every knob. The full annotated table lives in [Config knobs (reference)](../reference/config-reference.md); the groups that drive orchestrator behaviour are summarised here.

| Group | Key knobs (default) | What the orchestrator does with them |
|---|---|---|
| Budget & pools | `budget=50.0`, `rho=0.7` | Sizes `Budget`. |
| Wave sizing | `K=5`, `eta=3.0`, `explore_work_frac=0.85`, `explore_task_usd=3.5`, `verify_task_usd=1.5`, `ground_task_usd=2.0`, `task_cap_mult=1.8`, `concurrency=4` | Per-wave fan-out and per-task USD caps. |
| Promotion (A) | `promote_explore_frac=0.34`, `promote_kappa=8.0`, `promote_seed=0` | Beam vs Thompson split, fallback Beta concentration, RNG seed. |
| FDR (E) | `fdr_enabled=True`, `fdr_wealth0=0.5`, `fdr_alpha=0.05`, `fdr_payout=0.05`, `fdr_alpha_min=0.005` | Builds `AlphaInvesting`, gates the verify drain. |
| Calibration (B) | `calibrate_enabled=True`, `calibrate_min_labels=12`, `calibrate_refit_every=6` | Builds `Calibrator`; when/how often to refit. |
| Corroboration (B/C) | `corroborate_enabled=True`, `corroborate_thresh=0.88`, `corroborate_per_source=0.04` | Backlog resurfacing on fresh independent evidence. |
| Prior probe (G) | `prior_probe_enabled=True`, `prior_probe_k=5` | Verify top-k priors during INIT. |
| Hierarchy (C) | `niche_boost=0.15` | Promise boost for directions under thin/contested parents. |
| Frontier rerank | `rerank_frontier=True`, `rerank_direct_max=60`, `rerank_pool=50` | LLM rerank of the open-direction frontier. |
| Checkpoint / stop | `checkpoint_every=0.0`, `progress_eps=0.02`, `max_rounds=30` | Checkpoint cadence and convergence test. |
| Correction (D) | `correction_max_attempts=2` | Passed to `ledger.apply_verification` as the peeking guard. |
| Misc | `ground_terms=4`, `task_timeout=1800`, `model="gpt-5.4"`, `env_file`, `reference_set=[]`, `rubric=...` | INIT grounding count, per-call kwargs. |

**Two knobs are effectively dead in this module.** `promote_tau` is annotated `DEPRECATED` and never read here (orchestrator.py:71). `reference_set` (92) and `rubric` (93-94) are stored but never consumed by `orchestrator.py` — `rubric` would be an argument to `executors.evaluate`, which the loop never calls (see [Unwired code](#unwired-code)).

---

## `Orchestrator.__init__` (orchestrator.py:150-176)

Sets up all state. Notable fields:

| Field | Line | Purpose |
|---|---|---|
| `q`, `run_dir`, `cfg` | 151-154 | Question, output dir, config. |
| `ledger` | 155 | `Ledger(q)` — the belief store. |
| `budget` | 156 | `Budget(cfg.budget, cfg.rho)`. |
| `embedder` | 157 | `Embedder` for all cosine/rank operations. |
| `verify_queue` | 158 | Claims promoted and awaiting VERIFY. |
| `fdr` | 159-160 | `AlphaInvesting` from the `fdr_*` knobs. |
| `calibrator`, `calib_pairs`, `_calib_last_fit` | 161-163 | Isotonic calibrator + accumulated `(raw_conf, interval_width, outcome)` labels + last-fit marker. |
| `snapshots` | 164 | `metrics.Snapshot` history. |
| `explored_texts`, `uncovered_fields` | 165, 167 | Frontier de-dup signal + coverage gaps. |
| `explore_costs`, `verify_costs` | 168-169 | Observed per-task USD, used for rolling averages. |
| `_new_claims` | 166 | Claims since last checkpoint (progress numerator). |
| `checkpoint_cost` | 172 | `cfg.checkpoint_every or (cfg.budget/6.0)` — spend interval between checkpoints. |
| `_emb_charged` | 175 | Cumulative embedder USD already charged to the budget. |
| `_log_f` | 176 | Append-mode `orchestrator.log`. |

## Infrastructure helpers (orchestrator.py:179-229)

| Helper | Lines | Behaviour |
|---|---|---|
| `log(msg)` | 179-183 | Timestamped print + append to `orchestrator.log`, both flushed. |
| `_task_dir(label)` | 185-189 | Increments `_task_n`, returns `run_dir/tasks/NNNN_label`. Every executor call gets its own numbered dir. |
| `_charge_embed()` | 191-195 | Charges the embedder's *new* spend (`spent_usd - _emb_charged`) to the **explore** pool and advances the watermark. This is the only place embedding cost enters the budget. |
| `_take(res, pool="explore")` | 197-206 | Unpacks `(data, usd)`, charges `usd` to `pool`, records the cost in `explore_costs`/`verify_costs`, returns `data`. A task killed at its cap returns `(None, usd>0)` — still charged, data is `None`. |
| `_run_parallel(jobs)` | 208-222 | Runs `[(fn, args, kwargs), ...]` on a `ThreadPoolExecutor(max_workers=concurrency)`, preserving input order in the results list. `CodexError` and any other exception are logged and leave a `None` slot; they do not abort the wave. |
| `_kw(usd_cap=None)` | 224-229 | Builds the common executor kwargs (`model`, `env_file`, `timeout`), adding `usd_cap` only when given. |

## `init()` — INIT (orchestrator.py:232-265)

1. Runs `executors.fields` and `executors.prior` **in parallel** (234-237). `fields` → `ledger.required_fields` (238-240); `prior` → `ledger.seed(open_questions, prior_hypothesis, candidate_answers)` (243-246) plus up to `ground_terms` `key_terms` (247).
2. Seeds `uncovered_fields` from the required fields (248).
3. If there are key terms and explore budget remains, GROUNDs each term in parallel with a `ground_task_usd` hint and a `task_cap_mult` cap (252-262), writing definitions into `ledger.glossary`.
4. Calls `_prior_probe()` (263) then `_save()` (265).

INIT charges everything to the explore pool (via `_take`'s default).

## `_prior_probe()` / `_probe_apply()` — Component G (orchestrator.py:268-307)

`_prior_probe` (268-296): if enabled and there are prior candidate answers, it takes the top `prior_probe_k` by confidence (275-276) and VERIFYs each as a synthetic `Claim` in parallel — **but only if `explore_remaining() > cap`** (277-279), otherwise it returns without probing. Results are charged to the **explore** pool (290, comment at line 290) and applied via `_probe_apply`. After the wave, if calibration is enabled and enough labels have accrued, it fits the calibrator once (293-296).

`_probe_apply` (298-307): calls `ledger.apply_verification` (302), then logs a `(raw_conf, interval_width, outcome)` label when the verdict is terminal `CONFIRMED`/`REFUTED` (304-305), and — only if `CONFIRMED` and the claim `graduates()` — inserts it as an early grounded claim (306-307).

## Wave-sizing helpers (orchestrator.py:310-316)

- `_avg(costs, seed)` (310-311): mean of the last 8 recorded costs, or `seed` if none yet. Used for `run.json` reporting.
- `_explore_work_remaining()` (313-316): `explore_cap * explore_work_frac - spent_explore`. This holds back `(1 - explore_work_frac)` of the explore pool as reserve for the *uncapped* judge/evaluate/embedding calls, so EXPLORE waves cannot consume the entire pool.

## `run()` — the round loop (orchestrator.py:319-378)

```
init()
while  not converged
   and round < max_rounds
   and ledger.open_directions()
   and _explore_work_remaining() >= explore_task_usd * 0.5:      # loop guard (322-324)
    round += 1
    target = explore_task_usd;  cap = target * task_cap_mult
    rem = _explore_work_remaining()
    if rem < cap:  k, cap = 1, rem                               # shrink to one task, cap = whatever's left
    else:          k = clamp(rem // cap, 1..K)                   # worst case (all hit cap) still fits (330-333)
    batch = _select_batch(k)                                     # frontier selection
    mark batch EXPLORING
    for each dir: ctx = measure.select_context(...); build explore job
    _charge_embed(); results = _run_parallel(jobs)              # 352-353
    for dir, res:
        ingest claims + new_directions;  mark dir CLOSED/EXPLORED (dead_end?) (356-365)
    _rescore_corroboration(batch_claims)                        # 366
    _promote(batch_claims)                                      # 367
    _drain_verify_pool()                                        # 371
    if spent - last_checkpoint_spend >= checkpoint_cost:        # 373
        converged = _checkpoint();  last_checkpoint_spend = spent
    _save()
finalize(converged)
```

Wave sizing (330-333) is the core budget guarantee: `k` is chosen so that even if every one of the `k` tasks is killed at its `cap`, the total stays within the reserved explore-work budget. A dir whose result is `None` (killed/errored) is marked `CLOSED` (360); a dir whose result carries `dead_end` is also `CLOSED`, otherwise `EXPLORED` (365).

## `_select_batch(k)` — frontier selection (orchestrator.py:380-413)

1. `measure.score_frontier(...)` computes an embedding **promise** score per open direction against explored texts and uncovered fields (384-385); `_charge_embed()` bills it (386).
2. **Niche boost (Component C, hierarchy):** if `niche_boost > 0`, it reads `ledger.direction_scores()` and, for any open direction whose *parent* came back `thin` (nothing confirmed) or `contested` (confirmed≈refuted), adds `niche_boost` to its promise (clamped to 1.0) (390-395).
3. Writes the promise back onto each direction and sorts descending (396-399).
4. **LLM rerank (opt-in):** if `rerank_frontier` and there is more than one open direction and `explore_remaining() > ground cap` (404): rank the whole frontier directly when `len(ranked) <= rerank_direct_max`, else embedding-shortlist the top `rerank_pool` and rerank only those (405). `executors.rerank` returns per-id scores; the USD is charged directly to explore (408); promises are overwritten and re-sorted (409-412).
5. Returns the top `k` (413).

## Promotion posterior — `_score` / `_beta_params` (orchestrator.py:416-443)

`_score(c)` (416-421): the promotion score is the calibrated confidence — `calibrator.apply(c.confidence)` when calibration is enabled **and** the calibrator is `fitted`, else the raw `c.confidence`. This is the single scoring function used for promotion ranking, verify-queue ordering, and the FDR speculativeness input.

`_beta_params(c)` (423-443) returns the `(a, b)` of the Beta posterior for Thompson sampling. Mean `mu = clamp(_score(c), 1e-3, 1-1e-3)` (429). Variance is chosen in priority order:

| Priority | Condition (lines) | Variance |
|---|---|---|
| 1 | calibration on, `calibrator.width_fitted`, valid interval (434-435) | `calibrator.variance(hi-lo)` — verify-calibrated width |
| 2 | valid interval present (436-437) | `((hi-lo)/(2·1.645))²` — LLM's raw ~90% interval moment-matched |
| 3 | otherwise (438-440) | fixed-concentration fallback: returns `(mu·kappa, (1-mu)·kappa)` with `kappa = promote_kappa` |

For paths 1–2 the variance is clamped below `mu(1-mu)` and converted to a concentration `kappa_c = clamp(var_max/var - 1, 1..200)`, returning `(mu·kappa_c, (1-mu)·kappa_c)` (441-443).

## Niche / spread / pool / corroboration (orchestrator.py:446-502)

| Method | Lines | Behaviour |
|---|---|---|
| `_niche(c)` (static) | 446-449 | Niche key = the claim's primary aspect lowercased, or `"(none)"`. |
| `_pick_spread(ordered, n)` | 451-467 | Round-robin one claim per niche (highest-priority first within each) to pick `n`, so one crowded aspect can't monopolise the verify budget (MAP-Elites style). |
| `_promotable_pool()` | 469-475 | The resurfacing archive: every `UNVERIFIED` claim in `ledger.claims` that `graduates()` and is not already in `verify_queue`. This is fresh claims **plus** carried-over backlog. |
| `_rescore_corroboration(new_claims)` | 477-502 | For each fresh graduated claim, `embedder.rank()`s it against the backlog texts; while cosine ≥ `corroborate_thresh` (`rank()` is sorted desc, so it breaks at the first miss), it calls `ledger.corroborate(backlog_claim, [fresh], per_source=corroborate_per_source)`, which applies the independent-source filter and the capped confidence bump. Charges the embedder and logs a count if anything was bumped. |

## `_promote(batch_claims)` — Components A+C (orchestrator.py:504-537)

Beam search + Thompson sampling over `_promotable_pool()`:

1. `keep = ceil(len(batch_claims) / eta)` — the per-wave verify budget / beam width (515).
2. `n_ex = round(keep * promote_explore_frac)` Thompson slots; `n_beam = keep - n_ex` beam slots (516-517).
3. **Beam:** sort the pool by `_score` desc, `_pick_spread` the top `n_beam` (518-521).
4. **Thompson:** sort the non-beam tail by a single Beta draw per claim (`rng.betavariate(*_beta_params(c))`, seeded `promote_seed + len(ledger.claims)`) and `_pick_spread` enough to reach `keep` (522-528).
5. Append all promoted claims to `verify_queue`, and mark each promoted claim's source direction `PROMOTED` (529-532).
6. Logs beam/sampled/resurfaced counts (533-537). "Resurfaced" = promoted claims that are not in this wave's fresh set.

## `_drain_verify_pool()` — VERIFY pool (orchestrator.py:540-603)

Runs after every EXPLORE wave and again at the top of `finalize`.

```
sort verify_queue by _score desc                                 # cheapest FDR test first (543)
while queue and verify_remaining() >= verify_task_usd*0.5:        # 548
    if fdr_enabled and not fdr.can_afford(_score(queue[0])):      # cheapest unaffordable → halt (551-553)
        halted = True; break
    size wave n by remaining verify budget and concurrency (554-560)
    pop up to n claims that are individually FDR-affordable (561-566)
    parallel executors.verify(claim), cap = verify_task_usd*task_cap_mult, hint = target
    for each result:
        raw_conf, raw_w = pre-overwrite self-report + interval width (575-576)
        promo_score = _score(c)                                   # FDR speculativeness (577)
        corrective = ledger.apply_verification(c, v, max_corrections=correction_max_attempts) (578-579)
        if fdr_enabled: fdr.settle(promo_score, verification==CONFIRMED) (580-581)
        if verification in (CONFIRMED, REFUTED): append calib label (584-585)
        if corrective: corrective.promise += 0.1 (capped) (586-587)
```

After draining, if calibration is enabled, enough labels exist, and `calib_pairs - _calib_last_fit >= calibrate_refit_every`, it refits the calibrator and advances `_calib_last_fit` **only when the fit lands** (589-596) — so a below-minimum no-op does not skip the refit window. Logs FDR-halt and drain summaries (597-603). All verify cost is charged to the **verify** pool (`_take(res, pool="verify")`, 572).

## Measurement, checkpoint, convergence (orchestrator.py:606-653)

`_measure(tag)` (606-620): runs `executors.judge_coverage` (charged to explore via `_take`'s default pool), converts the judge output to `(coverage, uncovered)` via `measure.coverage_from_judge`, updates `uncovered_fields`, builds a `metrics.Snapshot` (with `new_claims` and `progress_eps`), appends it, and resets `_new_claims` to 0.

`_checkpoint()` (623-653) is invoked when spend since the last checkpoint reaches `checkpoint_cost` (orchestrator.py:373):

1. Takes a measurement and logs coverage/quality/progress/answeredness (624-630).
2. **Steer (dig deeper):** if `snap.stalled` and explore budget remains, calls `executors.patterns`, adds them to the ledger, and `spawn_from_patterns` new frontier directions with a `+0.1` promise nudge (635-644). Stall is *not* convergence.
3. **Convergence test** (648-650): returns `True` only if `required_fields` is non-empty **and** `coverage >= 0.999` **and** `backlog == 0` **and** `progress <= progress_eps`. All four must hold; progress≈0 alone never converges.

## `finalize(converged)` (orchestrator.py:656-692)

1. Drains the verify pool one last time (657).
2. If the ledger has no patterns yet and explore budget remains, runs `executors.patterns` for the synthesis section (662-666).
3. Runs `executors.finalize_report`; on success writes `outline.json` and uses `report_markdown` (appending `ledger.references_md()` if the body has no sources/references section) (669-681). On failure, falls back to the deterministic `ledger.synthesize(only_confirmed=True)` (682-684).
4. Writes `answer.md`, takes a final measurement, saves, and logs the DONE line including `answeredness/$` (685-692).

## `_save()` — persistence (orchestrator.py:694-707)

Writes `ledger.json` (via `ledger.save`) and `run.json`. `run.json` records the question, round, budget breakdown (total/spent/explore/verify/**embeddings**), pattern count, rolling `avg_explore_cost`/`avg_verify_cost` (last-8 average), all snapshots (as `__dict__`), and the full config dict. Called after INIT, after every round, and inside finalize.

---

## Cost and embedding charging — summary

| Cost source | Pool charged | Where |
|---|---|---|
| EXPLORE waves, GROUND, fields/prior, patterns, judge_coverage, finalize_report | explore | `_take(...)` default (197-206) |
| Prior-probe VERIFYs | explore | `_take(res, pool="explore")` (290) |
| Frontier rerank | explore | direct `budget.spend("explore", usd)` (408) |
| Embedding / `score_frontier` / `rank` calls | explore | `_charge_embed()` (191-195), called at 352, 386, 501 |
| VERIFY waves (main loop + finalize) | verify | `_take(res, pool="verify")` (572) |

Embedding cost is billed incrementally by watermark (`_emb_charged`), so it is counted exactly once even though `_charge_embed` is called from several sites.

## Unwired code

- **`executors.evaluate` and `executors.judge_forward` are never called** by the orchestrator. `orchestrator.py` invokes 9 of the 11 executor functions defined in `executors.py` (`fields`, `prior`, `ground`, `verify`, `explore`, `rerank`, `judge_coverage`, `patterns`, `finalize_report`); `evaluate` (`executors.py:307`) and `judge_forward` (`executors.py:292`) have no caller here. Consequently `Config.rubric` (orchestrator.py:93-94) — which is `evaluate`'s rubric argument — is stored, saved into `run.json`, but never used at runtime.
- **`Config.promote_tau`** (orchestrator.py:71) is explicitly deprecated and unused; kept only for CLI back-compat.
- **`Config.reference_set`** (orchestrator.py:92) is stored and persisted but not read anywhere in `orchestrator.py`.
- **`self.last_draft`** (orchestrator.py:171) is initialised to `""` and never read or reassigned — a vestige of the removed draft/evaluate loop.
