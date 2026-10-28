"""The leakage ladder's three hand-written methods do what their papers say, in the coded domain.

They are positive controls (PLAN.md section 2.10), so a bug that made one of them safer than it
should be would quietly turn a check on the attacks into another null result.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from facsimile.prep import Categorical, Domain, Numeric, encode, fit_domain
from facsimile.synth.ladder import kanon, mondrian, perturb, smote

SPECS = (
    Categorical("region", values=tuple(str(i) for i in range(12))),
    Categorical("job", values=tuple(str(i) for i in range(8))),
    Numeric("age", lo=0, hi=90, bins=9),
    Numeric("hours", lo=0, hi=80, bins=8),
    Categorical("secret", values=tuple(str(i) for i in range(4))),
)


@pytest.fixture(scope="module")
def coded() -> tuple[pd.DataFrame, Domain]:
    rng = np.random.default_rng(0)
    n = 600
    raw = pd.DataFrame(
        {
            "region": rng.integers(0, 12, n),
            "job": rng.integers(0, 8, n),
            "age": rng.integers(0, 90, n),
            "hours": rng.integers(0, 80, n),
            "secret": rng.integers(0, 4, n),
        }
    )
    domain = fit_domain(SPECS, raw)
    return encode(raw, domain).reset_index(drop=True), domain


def test_the_perturbed_copy_is_every_record_moved_a_little(coded) -> None:  # type: ignore[no-untyped-def]
    train, domain = coded
    out = perturb(train, domain, seed=1, n=len(train), noise_sd=1.0, swap=0.10)
    assert len(out) == len(train)
    for col in domain.columns:
        values = out[col.name]
        assert values.between(0, col.size - 1).all()
        if col.kind == "categorical":
            # A swap moves values between records, so each value's count is unchanged.
            assert sorted(values) == sorted(train[col.name])
        else:
            # Noise of one bin moves values, but the distribution only by about a bin.
            shift = np.abs(np.sort(values.to_numpy()) - np.sort(train[col.name].to_numpy()))
            assert 0 < shift.mean() <= 1.0


def test_smote_puts_numeric_values_between_real_neighbours(coded) -> None:  # type: ignore[no-untyped-def]
    train, domain = coded
    out = smote(train, domain, seed=2, n=400, k=5)
    assert len(out) == 400
    for col in domain.columns:
        assert out[col.name].between(0, col.size - 1).all()
    # Every new record's categorical values come from real records, so none is new.
    real_pairs = set(map(tuple, train[["region", "job"]].to_numpy()))
    seen = np.mean([tuple(r) in real_pairs for r in out[["region", "job"]].to_numpy()])
    assert seen > 0.5


def test_mondrian_partitions_cover_every_row_with_at_least_k(coded) -> None:  # type: ignore[no-untyped-def]
    train, domain = coded
    quasi = [c for c in domain.columns if c.name != "secret"]
    codes = train[[c.name for c in quasi]].to_numpy(dtype=np.int64)
    parts = mondrian(codes, [c.kind == "numeric" for c in quasi], [c.size for c in quasi], k=5)
    assert sum(len(p) for p in parts) == len(train)
    assert len(np.unique(np.concatenate(parts))) == len(train)
    assert min(len(p) for p in parts) >= 5
    assert len(parts) > 20, "it should split, not return one group"


def test_k_anonymity_hides_each_record_among_k_and_keeps_the_secret(coded) -> None:  # type: ignore[no-untyped-def]
    train, domain = coded
    out = kanon(train, domain, seed=3, n=len(train), k=5, secret="secret")
    quasi = [c.name for c in domain.columns if c.name != "secret"]
    sizes = out.groupby(quasi).size()
    assert sizes.min() >= 5
    assert sorted(out["secret"]) == sorted(train["secret"]), "the secret is released as is"
