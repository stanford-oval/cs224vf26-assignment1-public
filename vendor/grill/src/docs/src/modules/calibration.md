# calibration.py

Low-level reference for `calibration.py`, the Component B posterior calibrator. This is pure Python — no numpy, no sklearn, no model calls — that fits two isotonic step functions from VERIFY's confirm/refute labels: one maps raw self-reported confidence to an empirical probability, the other maps the LLM's stated interval width to an outcome variance.

Related: [Calibration and uncertainty](../architecture/calibration-and-uncertainty.md) · [orchestrator.py](./orchestrator.md) · [ledger.py](./ledger.md) · [Config knobs (reference)](../reference/config-reference.md)

## What this module is for

The module docstring (`calibration.py:1-18`) states the intent: LLM verbalized confidence is overconfident, so the **point map** corrects raw confidence to `P(true)`; the LLM also emits a ~90% credible interval whose **width** is its stated uncertainty, so the **width map** learns `stated_width -> actual outcome variance`. Both are fit by isotonic regression (Pool-Adjacent-Violators). The width map is what drives Thompson exploration, so for a beam+Thompson policy it matters more than the point map. Both maps are a no-op until `min_labels` labels accrue (`calibration.py:17`).

The file has exactly three top-level definitions:

| Name | Kind | Lines | Role |
|------|------|-------|------|
| `_pav` | function | `calibration.py:24-35` | Pool-Adjacent-Violators isotonic fit |
| `_lookup` | function | `calibration.py:38-49` | Evaluate an ascending step function at `x` |
| `Calibrator` | dataclass | `calibration.py:52-111` | Holds both step functions; `fit` / `apply` / `variance` / `ece` |

## `_pav` — Pool-Adjacent-Violators isotonic fit (`calibration.py:24-35`)

Input is a list of `(x, target)` pairs **already sorted by `x` ascending** (the caller sorts; `_pav` does not). `target` is any real: a `{0,1}` outcome for the point map, a squared error for the width map. Output is an ascending list of `(x_min, fitted_mean)` blocks representing a non-decreasing step function.

Each `blocks` entry is a 3-element list `[sum_target, count, x_min]` (`calibration.py:28`). The algorithm streams the pre-sorted points:

```
for each (x, t) in pairs:
    push a new block [t, 1.0, x]
    while >= 2 blocks AND mean(second-to-last) >= mean(last):   # violation
        pop last block  (st2, c2, _)
        pop prev block  (st1, c1, x1)
        push merged     [st1+st2, c1+c2, x1]                    # keep LEFT x_min
```

The merge condition is `blocks[-2].mean >= blocks[-1].mean` (`calibration.py:31`), where `mean = sum_target / count`. Because equality triggers a merge, adjacent equal-mean blocks are pooled. The merged block keeps the **left** block's `x_min` (`calibration.py:34`), so `x_min` is the smallest `x` in the pooled region. The final comprehension (`calibration.py:35`) drops the running sum/count and returns `(x_min, mean)` per block.

The result is guaranteed non-decreasing in `x`: any adjacent pair whose left mean is `>=` the right mean is pooled away before the loop advances. Cost is O(n) amortized (each block is pushed and popped at most once) on top of the caller's O(n log n) sort.

## `_lookup` — step-function evaluation (`calibration.py:38-49`)

Evaluates an ascending step function `steps` (the `(x_min, value)` blocks from `_pav`) at a query `x`.

| Case | Return |
|------|--------|
| `steps` empty (unfitted) | `None` (`calibration.py:40-41`) |
| `x` below the first `x_min` | first block's value, `steps[0][1]` (`calibration.py:43`) |
| otherwise | value of the last block whose `x_min <= x` |

It walks blocks in order, updating `val` while `x >= x_min`, and `break`s at the first block whose `x_min` exceeds `x` (`calibration.py:44-48`). Because the list is ascending, this yields a right-continuous, last-matching-block lookup. There is no interpolation — it is a pure step function. Note the pre-first-block behavior: `val` is seeded to the first block's value, so an `x` smaller than every `x_min` returns the lowest block's value rather than `None`.

## `Calibrator` dataclass (`calibration.py:52-111`)

### Fields (`calibration.py:55-58`)

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `min_labels` | `int` | `12` | Both maps stay unfitted until this many usable labels accrue |
| `steps` | `list[tuple[float,float]]` | `[]` | Point map: raw confidence -> `P(true)` |
| `width_steps` | `list[tuple[float,float]]` | `[]` | Width map: stated width -> outcome variance |
| `n` | `int` | `0` | Count of cleaned labels from the last `fit` |

The orchestrator constructs it as `Calibrator(min_labels=cfg.calibrate_min_labels)` (`orchestrator.py:161`), where `calibrate_min_labels` defaults to `12` (`orchestrator.py:104`) — matching the dataclass default.

### Properties (`calibration.py:60-66`)

- `fitted` -> `bool(self.steps)`: the point map has been fit.
- `width_fitted` -> `bool(self.width_steps)`: the width map has been fit.

Both are read by the orchestrator to decide whether to apply calibration: `fitted` gates the promotion score (`orchestrator.py:419`) and `width_fitted` gates the Thompson variance (`orchestrator.py:434`).

### `fit(labels)` (`calibration.py:68-84`)

`labels` is a list of `(raw_confidence, stated_width, outcome)` triples; `stated_width < 0` or `None` means no interval was emitted (`calibration.py:69`).

Data flow:

```
labels = [(r, w, y), ...]
  |
  |  clean: keep rows with r is not None; coerce r->float,
  |         w->float (None -> -1.0), y-> 1.0/0.0            (calibration.py:70-71)
  v
n = len(clean)                                              (calibration.py:72)
  |
  |  if n < min_labels: steps = [], width_steps = [], return  (no-op)  (calibration.py:73-76)
  v
POINT map:  _pav( sort clean by r of (r, y) )              (calibration.py:78)
WIDTH map:  wpts = sort by w of (w, (apply(r) - y)^2)
                   for rows with 0.0 <= w <= 1.0            (calibration.py:81-82)
            width_steps = _pav(wpts) if len(wpts) >= min_labels else []  (calibration.py:83)
```

Key details:

- The **no-op guard** (`calibration.py:73-76`): if fewer than `min_labels` cleaned rows, both maps are reset to empty and the calibrator returns itself unfit. This is the "identity until labels accrue" behavior — `apply` then returns raw and `variance` returns `None`.
- The **point map** is fit first (`calibration.py:78`) over all cleaned rows, keyed on raw confidence.
- The **width map** target is `(self.apply(r) - y) ** 2` (`calibration.py:81`) — the squared error of the *already point-calibrated* belief, used as a variance proxy. Because `apply` is called mid-`fit`, it uses the point map that was just assigned on the line above. Only rows with a real interval in `[0.0, 1.0]` contribute; rows with `w = -1.0` (no interval) or `w > 1.0` are excluded.
- The width map has its **own** count gate: it is fit only if the number of interval-bearing points `>= min_labels` (`calibration.py:83`); otherwise `width_steps` stays empty even when the point map fits. So `fitted` can be true while `width_fitted` is false.
- Isotonicity direction: for the width map, wider stated interval -> more error, i.e. non-decreasing width -> variance (`calibration.py:79-80`).

`fit` returns `self` for chaining. The orchestrator calls it during the prior probe (`orchestrator.py:294`) and periodically during the main loop, refitting every `calibrate_refit_every` (default `6`) new labels (`orchestrator.py:589-592`).

### `apply(raw)` (`calibration.py:86-89`)

Looks up `raw` in `steps`; returns `float(raw)` unchanged if the map is unfit (`_lookup` returned `None`), else the calibrated value. This is the identity-until-fitted point map. Called for the promotion score in `orchestrator.py:420` and internally by `fit` (`calibration.py:81`).

### `variance(width)` (`calibration.py:91-95`)

Looks up `width` in `width_steps`. Returns `None` if the width map is unfit, else the fitted variance **clamped to `[1e-4, 0.2499]`** (`calibration.py:95`). The upper clamp `0.2499` is just under `0.25`, the maximum variance of a Bernoulli (a `[0,1]` belief), keeping the Thompson posterior well-defined. This is the verification-grounded uncertainty consumed as option (1) of the Thompson variance in `orchestrator.py:434-435`.

### `ece(labels, bins=10)` (`calibration.py:97-111`)

Expected Calibration Error of the **point** map against outcomes. It is flexible about tuple shape: it reads `item[0]` as raw confidence and `item[-1]` as the outcome, so it accepts both `(raw, y)` and `(raw, width, y)` (`calibration.py:98-99`). It first maps each raw through `self.apply` to get the calibrated probability, then bins:

```
clean = [(apply(raw), y) for rows with raw is not None]     (calibration.py:99)
if empty -> 0.0                                             (calibration.py:100-101)
for b in 0..bins-1:
    bucket = points with lo <= p < hi                        (calibration.py:105)
             (last bin also captures p == 1.0)
    conf = mean p in bucket;  acc = mean y in bucket         (calibration.py:108-109)
    err += (|bucket| / total) * |conf - acc|                 (calibration.py:110)
return err                                                   (calibration.py:111)
```

Bins are equal-width over `[0,1)` (`lo = b/bins`, `hi = (b+1)/bins`, `calibration.py:104`); the final bin is closed at the top so `p == 1.0` is not dropped (`calibration.py:105`). Empty bins are skipped (`calibration.py:106-107`). The return is the standard bin-count-weighted mean of `|confidence - accuracy|`. The orchestrator logs it after each refit (`orchestrator.py:596`); `ece` is diagnostic only — nothing branches on its value.

## Wiring summary

Everything in this module is reachable. `_pav` and `_lookup` are private helpers used only by `Calibrator`. Consumers in `orchestrator.py`:

| Symbol | Consumed at | Purpose |
|--------|-------------|---------|
| `Calibrator(...)` | `orchestrator.py:161` | constructed once per run |
| `.fit(...)` | `orchestrator.py:294`, `orchestrator.py:592` | prior-probe seed and periodic refit |
| `.fitted` | `orchestrator.py:419` | gate the calibrated promotion score |
| `.apply(...)` | `orchestrator.py:420` | calibrated promotion score |
| `.width_fitted` | `orchestrator.py:434` | gate the Thompson variance |
| `.variance(...)` | `orchestrator.py:435` | verify-calibrated Thompson variance |
| `.n`, `.ece(...)` | `orchestrator.py:595-596` | log line after a refit |

No functions in `calibration.py` are dead. The one non-obvious constraint is stated in the docstring rather than enforced in code: the estimator (scorer model + prompt) must stay fixed for the accumulated labels to remain valid (`calibration.py:17`).
