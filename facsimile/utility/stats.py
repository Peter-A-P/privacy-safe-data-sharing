"""Intervals and paired deltas: project 02's arithmetic, carried across.

`Interval` and `bootstrap` are 02's (`mselect.experiments.analysis`, v0.3.1) with the same
percentile bootstrap over units and the same rule: never a bare number. Copied rather than
imported because `mselect` brings an item-response stack this project does not use, and the
function is twelve lines. `tests/test_stats.py` holds it to a stream with a known answer.

Two additions this project needs and 02 did not: the Clopper-Pearson interval for a count of
successes, which is what an attack's success rate is, and the paired bootstrap of a difference
in means over the same units, which is what a utility delta against the real-data ceiling is.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats

RESAMPLES = 2000


@dataclass(frozen=True, slots=True)
class Interval:
    """A point estimate and its 95% interval. Never a bare number."""

    point: float
    lo: float
    hi: float
    n: int

    def fmt(self, *, percent: bool = True) -> str:
        if self.n == 0:
            return "n/a"
        if percent:
            return f"{self.point:.1%} ({self.lo:.1%} to {self.hi:.1%}, n = {self.n})"
        return f"{self.point:.3f} ({self.lo:.3f} to {self.hi:.3f}, n = {self.n})"

    def as_dict(self) -> dict[str, float | int]:
        return {"point": self.point, "lo": self.lo, "hi": self.hi, "n": self.n}


def bootstrap(values: Sequence[float], *, resamples: int = RESAMPLES, seed: int = 0) -> Interval:
    """Percentile bootstrap of the mean over units (02's function, unchanged)."""
    data = np.asarray([v for v in values if np.isfinite(v)], dtype=float)
    if data.size == 0:
        return Interval(float("nan"), float("nan"), float("nan"), 0)
    rng = np.random.default_rng(seed)
    draws = data[rng.integers(0, data.size, (resamples, data.size))].mean(axis=1)
    return Interval(
        float(data.mean()),
        float(np.quantile(draws, 0.025)),
        float(np.quantile(draws, 0.975)),
        int(data.size),
    )


def paired_delta(
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    *,
    resamples: int = RESAMPLES,
    seed: int = 0,
) -> Interval:
    """Mean of left minus right over the same units, resampling units jointly.

    Resampling the pairs rather than each side separately is what makes the interval narrow
    enough to mean something when both models are scored on the same test records: most of
    the variance between test sets is shared, and the difference cancels it.
    """
    if left.shape != right.shape:
        raise ValueError(f"paired arrays differ in shape: {left.shape} against {right.shape}")
    keep = np.isfinite(left) & np.isfinite(right)
    diff = (left - right)[keep]
    return bootstrap(diff.tolist(), resamples=resamples, seed=seed)


def clopper_pearson(successes: int, trials: int, *, level: float = 0.95) -> Interval:
    """Exact binomial interval for a success rate. Zero-width intervals cannot occur."""
    if trials <= 0:
        return Interval(float("nan"), float("nan"), float("nan"), 0)
    if not 0 <= successes <= trials:
        raise ValueError(f"{successes} successes out of {trials} trials")
    alpha = 1.0 - level
    lo = (
        0.0
        if successes == 0
        else float(stats.beta.ppf(alpha / 2, successes, trials - successes + 1))
    )
    hi = (
        1.0
        if successes == trials
        else float(stats.beta.ppf(1 - alpha / 2, successes + 1, trials - successes))
    )
    return Interval(successes / trials, lo, hi, trials)
