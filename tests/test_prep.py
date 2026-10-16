"""Preprocessing: every value lands in the domain, and the inverse map round-trips."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest

from facsimile.prep import (
    MISSING,
    OTHER,
    Categorical,
    Domain,
    Numeric,
    bin_edges,
    check_codes,
    decode,
    encode,
    fit_domain,
    midpoints,
)

SPECS = (
    Categorical("colour"),
    Categorical("flag", values=("0", "1")),
    Categorical("region", nullable=True),
    Numeric("age", lo=0, hi=100, bins=10),
    Numeric("amount", lo=0, hi=10000, bins=8, scale="log", nullable=True),
    Numeric("income", lo=0, hi=100, bins=2, edges=(0, 50, 100)),
)


def frame(n: int = 1000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    colours = rng.choice(["red", "green", "blue", "violet"], size=n, p=[0.5, 0.3, 0.198, 0.002])
    region = rng.choice(["north", "south", None], size=n, p=[0.6, 0.3, 0.1])
    amount = np.where(rng.random(n) < 0.05, np.nan, rng.lognormal(3, 2, n))
    return pd.DataFrame(
        {
            "colour": colours,
            "flag": rng.integers(0, 2, n),
            "region": region,
            "age": rng.integers(-5, 120, n),
            "amount": amount,
            "income": rng.uniform(0, 100, n),
        }
    )


def test_rare_categories_merge_into_other_and_missing_gets_its_own_code() -> None:
    domain = fit_domain(SPECS, frame())
    assert domain["colour"].labels == ("blue", "green", "red", OTHER)
    assert domain["region"].labels[-1] == MISSING
    assert domain["flag"].labels == ("0", "1")  # a codebook has no OTHER


def test_every_value_lands_in_the_domain_including_ones_never_seen() -> None:
    domain = fit_domain(SPECS, frame(seed=0))
    other = frame(seed=1)
    other.loc[0, "colour"] = "a colour nobody has seen"
    codes = encode(other, domain)
    check_codes(codes, domain)
    assert decode(codes, domain).loc[0, "colour"] == OTHER


def test_out_of_range_numbers_are_clipped_to_the_end_bins() -> None:
    domain = fit_domain(SPECS, frame())
    codes = encode(pd.DataFrame({**frame(3).to_dict("list"), "age": [-5, 50, 1000]}), domain)
    assert codes["age"].tolist() == [0, 5, 9]


def test_a_value_outside_a_codebook_is_an_error_not_a_silent_merge() -> None:
    domain = fit_domain(SPECS, frame())
    bad = frame(3)
    bad["flag"] = [0, 1, 7]
    with pytest.raises(ValueError, match="codebook"):
        encode(bad, domain)


def test_missing_in_a_non_nullable_column_is_an_error() -> None:
    domain = fit_domain(SPECS, frame())
    bad = frame(3)
    bad["age"] = [1.0, np.nan, 3.0]
    with pytest.raises(ValueError, match="missing"):
        encode(bad, domain)


def test_round_trip_codes_to_labels_to_codes() -> None:
    domain = fit_domain(SPECS, frame())
    codes = encode(frame(seed=3), domain)
    labels = decode(codes, domain)
    mids = midpoints(codes, domain)
    again = encode(
        pd.DataFrame(
            {
                c.name: (mids[c.name] if c.kind == "numeric" else labels[c.name])
                for c in domain.columns
            }
        ).replace({MISSING: None}),
        domain,
    )
    pd.testing.assert_frame_equal(again, codes)


def test_explicit_edges_and_log_edges() -> None:
    assert bin_edges(Numeric("x", 0, 100, 2, edges=(0, 50, 100))) == (0.0, 50.0, 100.0)
    log = bin_edges(Numeric("x", 0, 10000, 4, scale="log"))
    assert log[0] == 0 and log[-1] == pytest.approx(10000)
    widths = np.diff(log)
    assert all(b > a for a, b in itertools.pairwise(widths))
    with pytest.raises(ValueError):
        bin_edges(Numeric("x", 0, 1, 2, edges=(0, 1, 1)))


def test_domain_json_round_trip(tmp_path: pytest.TempPathFactory) -> None:
    domain = fit_domain(SPECS, frame())
    path = tmp_path / "domain.json"  # type: ignore[operator]
    domain.write(path)
    assert Domain.read(path) == domain
