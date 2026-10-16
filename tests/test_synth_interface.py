"""The one interface: budgets where they belong, codes in the domain, the input left untouched."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from facsimile.prep import Categorical, Domain, encode, fit_domain
from facsimile.synth import EPSILONS, methods
from facsimile.synth.base import Fitted, Wrapped
from facsimile.synth.grid import Cell, cells


def _tiny() -> tuple[pd.DataFrame, Domain]:
    rng = np.random.default_rng(0)
    specs = (Categorical("a", values=("0", "1", "2")), Categorical("b", values=("0", "1")))
    raw = pd.DataFrame({"a": rng.integers(0, 3, 300), "b": rng.integers(0, 2, 300)})
    domain = fit_domain(specs, raw)
    return encode(raw, domain), domain


def test_six_methods_three_dp() -> None:
    registry = methods()
    assert sorted(registry) == ["aim", "copula", "ctgan", "mst", "pate_ctgan", "tvae"]
    assert sorted(n for n, m in registry.items() if m.dp) == ["aim", "mst", "pate_ctgan"]


def test_budgets_go_only_where_they_belong() -> None:
    train, domain = _tiny()
    with pytest.raises(ValueError, match="needs an epsilon"):
        methods()["mst"].run(train, domain, seed=0, epsilon=None, n=10)
    with pytest.raises(ValueError, match="infinity"):
        methods()["copula"].run(train, domain, seed=0, epsilon=1.0, n=10)


def _fake(table: pd.DataFrame, mutate: bool = False) -> Wrapped:
    def fn(train: pd.DataFrame, domain: Domain, seed: int, eps: float | None, n: int) -> Fitted:
        if mutate:
            train.loc[train.index[0], "a"] = 1 - int(train["a"].iloc[0])
        return Fitted(table, {}, {"dp": False}, 0.0, 0.0, "cpu")

    return Wrapped("fake", "none", "non-dp statistical", fn)


def test_a_table_outside_the_domain_is_refused() -> None:
    train, domain = _tiny()
    bad = train.head(10).copy()
    bad.iloc[0, 0] = 7
    with pytest.raises(ValueError, match="outside"):
        _fake(bad).run(train, domain, seed=0, epsilon=None, n=10)


def test_a_method_that_edits_its_training_frame_is_refused() -> None:
    train, domain = _tiny()
    with pytest.raises(AssertionError, match="modified"):
        _fake(train.head(10).copy(), mutate=True).run(train, domain, seed=0, epsilon=None, n=10)


def test_the_grid_is_six_methods_five_budgets_plus_non_dp_three_seeds() -> None:
    grid = cells(["acs"])
    assert len(grid) == (3 * 1 + 3 * len(EPSILONS)) * 3
    assert Cell("acs", "copula", None, 0) in grid and Cell("acs", "aim", 0.5, 2) in grid


@pytest.mark.slow
def test_copula_returns_codes_in_the_domain() -> None:
    train, domain = _tiny()
    fitted = methods()["copula"].run(train, domain, seed=0, epsilon=None, n=50)
    assert len(fitted.table) == 50
    assert set(fitted.table["a"]) <= {0, 1, 2} and set(fitted.table["b"]) <= {0, 1}
