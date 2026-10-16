"""The bootstrap and the exact interval against answers worked out independently."""

from __future__ import annotations

import numpy as np
import pytest

from facsimile.utility.stats import bootstrap, clopper_pearson, paired_delta


def test_bootstrap_of_a_constant_has_no_width() -> None:
    iv = bootstrap([0.7] * 50)
    assert iv.n == 50
    assert (
        iv.point == pytest.approx(0.7)
        and iv.lo == pytest.approx(0.7)
        and iv.hi == pytest.approx(0.7)
    )


def test_bootstrap_matches_the_normal_interval_on_a_large_bernoulli_stream() -> None:
    # 4,000 draws at p = 0.3: the textbook 95% half-width is 1.96 * sqrt(0.21 / 4000) = 0.0142.
    rng = np.random.default_rng(1)
    values = (rng.random(4000) < 0.3).astype(float)
    iv = bootstrap(values.tolist(), resamples=4000)
    half = (iv.hi - iv.lo) / 2
    assert half == pytest.approx(
        1.96 * np.sqrt(values.mean() * (1 - values.mean()) / 4000), rel=0.08
    )
    assert iv.lo < values.mean() < iv.hi


def test_bootstrap_ignores_non_finite_and_reports_empty_as_nan() -> None:
    assert bootstrap([1.0, float("nan"), 0.0]).n == 2
    assert np.isnan(bootstrap([]).point)


def test_clopper_pearson_known_values() -> None:
    # Reference values from the beta quantiles, as tabulated in Clopper and Pearson (1934)
    # and reproduced by every statistics package: 0 of 10 gives an upper bound of 0.3085,
    # 5 of 10 gives 0.1871 to 0.8129.
    zero = clopper_pearson(0, 10)
    assert (zero.lo, round(zero.hi, 4)) == (0.0, 0.3085)
    half = clopper_pearson(5, 10)
    assert (round(half.lo, 4), round(half.hi, 4)) == (0.1871, 0.8129)
    full = clopper_pearson(10, 10)
    assert full.hi == 1.0 and round(full.lo, 4) == 0.6915


def test_clopper_pearson_rejects_impossible_counts() -> None:
    with pytest.raises(ValueError):
        clopper_pearson(11, 10)


def test_paired_delta_cancels_shared_variance() -> None:
    rng = np.random.default_rng(2)
    shared = rng.normal(0, 5, 2000)
    left = shared + 0.1
    right = shared
    iv = paired_delta(left, right)
    assert iv.point == pytest.approx(0.1)
    assert iv.hi - iv.lo < 1e-9  # the difference is constant, so the interval is a point


def test_paired_delta_refuses_unpaired_arrays() -> None:
    with pytest.raises(ValueError):
        paired_delta(np.zeros(3), np.zeros(4))
