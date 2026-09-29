"""Posterior calibration from the verification stream (Component B).

Two things are calibrated against VERIFY's own confirm/refute labels, both via isotonic regression
(Pool-Adjacent-Violators, no numpy/sklearn):

  1. POINT (mean): raw self-reported confidence -> P(true). LLM verbalized confidence is overconfident
     (Xiong et al. 2306.13063); this map corrects the level. Used for the FDR cost and the honesty of the
     reported belief (a monotone map barely changes the beam's rank order, by design).

  2. INTERVAL (spread): the LLM also emits a ~90% credible interval per claim; its WIDTH is the model's
     stated uncertainty. We calibrate that too — learn `stated_width -> actual outcome variance` (the mean
     squared error of the calibrated belief for claims the model stated that width). This is what drives
     Thompson exploration, so it matters more than the point map for a beam+Thompson policy: if the LLM's
     widths don't track real error the map flattens and everyone gets the base-rate spread; if they do,
     wide-stated claims get wide posteriors.

No-op until `min_labels` labels accrue. The estimator (scorer model + prompt) must stay fixed.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _pav(pairs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Pool-Adjacent-Violators isotonic fit. `pairs` = (x, target) sorted by x ascending; target is any
    real (a {0,1} outcome for the point map, a squared error for the width map). Returns ascending
    (x_min, fitted_mean) blocks — a non-decreasing step function."""
    blocks: list[list[float]] = []   # each: [sum_target, count, x_min]
    for x, t in pairs:
        blocks.append([t, 1.0, x])
        while len(blocks) >= 2 and blocks[-2][0] / blocks[-2][1] >= blocks[-1][0] / blocks[-1][1]:
            st2, c2, _ = blocks.pop()
            st1, c1, x1 = blocks.pop()
            blocks.append([st1 + st2, c1 + c2, x1])   # merge, keep the left block's x_min
    return [(b[2], b[0] / b[1]) for b in blocks]


def _lookup(steps: list[tuple[float, float]], x: float):
    """Evaluate an ascending step function at x (None if unfitted)."""
    if not steps:
        return None
    x = float(x)
    val = steps[0][1]
    for x_min, value in steps:
        if x >= x_min:
            val = value
        else:
            break
    return val


@dataclass
class Calibrator:
    """Isotonic calibration of the point belief AND the interval width, from verify labels."""
    min_labels: int = 12
    steps: list[tuple[float, float]] = field(default_factory=list)         # point: raw -> P(true)
    width_steps: list[tuple[float, float]] = field(default_factory=list)   # width -> outcome variance
    n: int = 0

    @property
    def fitted(self) -> bool:
        return bool(self.steps)

    @property
    def width_fitted(self) -> bool:
        return bool(self.width_steps)

    def fit(self, labels: list) -> "Calibrator":
        """`labels` = (raw_confidence, stated_width, outcome). stated_width < 0 (or None) = no interval."""
        clean = [(float(r), (float(w) if w is not None else -1.0), 1.0 if y else 0.0)
                 for (r, w, y) in labels if r is not None]
        self.n = len(clean)
        if self.n < self.min_labels:
            self.steps = []
            self.width_steps = []
            return self
        # POINT map: raw confidence -> empirical P(true)
        self.steps = _pav(sorted([(r, y) for r, _w, y in clean], key=lambda p: p[0]))
        # WIDTH map: stated interval width -> squared error of the calibrated belief (a variance proxy),
        # over claims that carried a real interval. Non-decreasing: wider stated interval -> more error.
        wpts = sorted([(w, (self.apply(r) - y) ** 2) for r, w, y in clean if 0.0 <= w <= 1.0],
                      key=lambda p: p[0])
        self.width_steps = _pav(wpts) if len(wpts) >= self.min_labels else []
        return self

    def apply(self, raw: float) -> float:
        """Point-calibrated mean P(true) (identity until fitted)."""
        v = _lookup(self.steps, raw)
        return float(raw) if v is None else v

    def variance(self, width: float):
        """Calibrated posterior variance for a claim whose LLM stated-interval width was `width` — the
        verification-grounded uncertainty that should drive Thompson. None if the width map isn't fitted."""
        v = _lookup(self.width_steps, width)
        return None if v is None else max(1e-4, min(0.2499, v))

    def ece(self, labels: list, bins: int = 10) -> float:
        """Expected Calibration Error of the POINT map vs outcome (accepts (raw,y) or (raw,width,y))."""
        clean = [(self.apply(item[0]), 1.0 if item[-1] else 0.0) for item in labels if item[0] is not None]
        if not clean:
            return 0.0
        tot, err = len(clean), 0.0
        for b in range(bins):
            lo, hi = b / bins, (b + 1) / bins
            bucket = [(p, y) for p, y in clean if (lo <= p < hi or (b == bins - 1 and p == 1.0))]
            if not bucket:
                continue
            conf = sum(p for p, _ in bucket) / len(bucket)
            acc = sum(y for _, y in bucket) / len(bucket)
            err += (len(bucket) / tot) * abs(conf - acc)
        return err
