"""The attack sanity pair: a copied table scores near-maximum risk, an independent one control-level.

PLAN.md section 4, "Tests that matter". Run on a small synthetic population with the shape of the
real data (mixed categorical and binned numeric columns, a skewed secret), so the test needs no
dataset. A copy of the targets' source table must be detected by every attack; a table drawn from
the same population but independent of the targets must score at control level.

"Control level" is a risk whose interval starts below two points, not "never detected": a 95%
interval excludes zero by chance about one time in twenty, and a test that demanded otherwise
would be testing luck (seed 0 of this world gives linkability 15 successes against 4, and seeds
1 to 4 give 10 against 12, 19 against 12, 9 against 15 and 13 against 21).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from facsimile.attacks.dcr import dcr
from facsimile.attacks.inference import inference
from facsimile.attacks.linkability import linkability
from facsimile.attacks.risk import residual, wilson
from facsimile.attacks.singling_out import SEARCHES, Mode, search_seeds, singling_out
from facsimile.prep import Categorical, Domain, Numeric, encode, fit_domain

CONTROL_LEVEL = 0.02

SPECS = (
    Categorical("region", values=tuple(str(i) for i in range(30))),
    # A postcode-like attribute with rare values, which is what univariate singling out feeds on.
    Categorical("postcode", values=tuple(str(i) for i in range(2000))),
    Categorical("job", values=tuple(str(i) for i in range(20))),
    Categorical("sex", values=("1", "2")),
    Numeric("age", lo=0, hi=90, bins=9),
    Numeric("hours", lo=0, hi=80, bins=8),
    Categorical("secret", values=tuple(str(i) for i in range(6))),
)


def population(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    region = rng.zipf(1.6, n) % 30
    job = rng.integers(0, 20, n)
    age = rng.integers(0, 90, n)
    # The secret depends on job and age, so the synthetic table is genuinely useful for inference
    # on anyone: the control attack succeeds well above chance, and only the excess is a leak.
    secret = (job // 4 + age // 45 + rng.integers(0, 2, n)) % 6
    return pd.DataFrame(
        {
            "region": region,
            "postcode": rng.integers(0, 2000, n),
            "job": job,
            "sex": rng.integers(1, 3, n),
            "age": age,
            "hours": rng.integers(0, 80, n),
            "secret": secret,
        }
    )


@pytest.fixture(scope="module")
def world() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Domain]:
    raw = population(9000, seed=0)
    domain = fit_domain(SPECS, raw)
    coded = encode(raw, domain)
    train = coded.iloc[:3000]
    targets = train.iloc[:600]
    control = coded.iloc[3000:3600]
    independent = coded.iloc[6000:9000].reset_index(drop=True)
    return train, targets, control, independent, domain


def test_inference_copy_is_detected_and_independent_is_not(world) -> None:  # type: ignore[no-untyped-def]
    train, targets, control, independent, domain = world
    copied = inference(targets, control, train.reset_index(drop=True), domain, secret="secret")
    assert copied.risk.detected and copied.risk.value > 0.6, copied.as_dict()
    # Not every target finds itself: identical auxiliary rows tie, and the tie is broken at random.
    assert copied.main.value > 0.9
    fresh = inference(targets, control, independent, domain, secret="secret")
    assert fresh.risk.lo < CONTROL_LEVEL, fresh.as_dict()
    assert fresh.control.value > fresh.baseline.value + 0.1  # useful, not leaking


def test_linkability_copy_is_detected_and_independent_is_not(world) -> None:  # type: ignore[no-untyped-def]
    train, targets, control, independent, domain = world
    a, b = ["region", "job", "sex"], ["age", "hours", "secret"]  # no postcode: too easy
    copied = linkability(targets, control, train.reset_index(drop=True), domain, a=a, b=b, k=5)
    assert copied.risk.detected and copied.risk.value > 0.3, copied.as_dict()
    fresh = linkability(targets, control, independent, domain, a=a, b=b, k=5)
    assert fresh.risk.lo < CONTROL_LEVEL, fresh.as_dict()


@pytest.mark.parametrize("mode", ["univariate", "multivariate"])
def test_singling_out_copy_is_detected_and_independent_is_not(world, mode: Mode) -> None:  # type: ignore[no-untyped-def]
    _, targets, control, independent, domain = world
    copied = singling_out(
        targets,
        control,
        targets.reset_index(drop=True),
        domain,
        mode=mode,
        n_attacks=300,
    )
    assert copied.risk.detected, copied.as_dict()
    fresh = singling_out(targets, control, independent, domain, mode=mode, n_attacks=300)
    assert fresh.risk.lo < CONTROL_LEVEL, fresh.as_dict()


def test_singling_out_averages_its_searches_without_counting_them_as_trials(world) -> None:  # type: ignore[no-untyped-def]
    """PLAN.md section 2.12: the mean over the searches, the trials left at the number of attacks,
    and the first search is the single search it replaced."""
    _, targets, control, independent, domain = world
    five = singling_out(targets, control, independent, domain, n_attacks=300, seed=7)
    runs = five.params["searches"]
    assert runs["seeds"] == search_seeds(7) == [7, 1007, 2007, 3007, 4007]
    assert len(runs["main"]) == SEARCHES
    assert five.main.successes == pytest.approx(np.mean(runs["main"]))
    assert five.control.successes == pytest.approx(np.mean(runs["control"]))
    assert five.main.trials == five.control.trials == 300
    one = singling_out(targets, control, independent, domain, n_attacks=300, seed=7, searches=1)
    assert (one.main.successes, one.control.successes, one.baseline.successes) == (
        runs["main"][0],
        runs["control"][0],
        runs["baseline"][0],
    )
    assert len(set(runs["main"])) > 1, "the searches should differ, or there is nothing to average"


def test_dcr_sees_a_copy_and_calls_an_independent_table_even(world) -> None:  # type: ignore[no-untyped-def]
    _, targets, control, independent, domain = world
    copied = dcr(targets, control, targets.reset_index(drop=True), domain, sample=600)
    assert copied["exact_copy_targets"]["point"] == 1.0
    assert copied["closer_to_training_share"]["lo"] > 0.6
    fresh = dcr(targets, control, independent, domain, sample=600)
    share = fresh["closer_to_training_share"]
    assert share["lo"] < 0.5 < share["hi"]


def test_risk_arithmetic() -> None:
    main, control = wilson(900, 1000), wilson(500, 1000)
    risk = residual(main, control)
    assert risk.value == pytest.approx((main.value - control.value) / (1 - control.value))
    assert risk.lo < risk.value < risk.hi
    same = residual(wilson(500, 1000), wilson(500, 1000))
    assert same.value == 0.0 and same.lo == 0.0 and not same.detected
