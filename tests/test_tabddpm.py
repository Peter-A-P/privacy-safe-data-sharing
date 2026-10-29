"""TabDDPM's bridge: floats back into codes, and a clear failure without its environment."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from facsimile.prep import Categorical, Domain, check_codes, encode, fit_domain
from facsimile.synth import GRID, methods, tabddpm


def _tiny() -> tuple[pd.DataFrame, Domain]:
    rng = np.random.default_rng(0)
    specs = (Categorical("a", values=("0", "1", "2")), Categorical("b", values=("0", "1")))
    raw = pd.DataFrame({"a": rng.integers(0, 3, 300), "b": rng.integers(0, 2, 300)})
    domain = fit_domain(specs, raw)
    return encode(raw, domain), domain


def test_floats_are_rounded_and_clipped_into_the_domain() -> None:
    _, domain = _tiny()
    raw = pd.DataFrame({"b": [0, 1, 1, 0], "a": [-0.7, 0.4, 1.6, 2.9]})
    codes, clipped = tabddpm.to_codes(raw, domain)
    check_codes(codes, domain)
    assert codes["a"].tolist() == [0, 0, 2, 2]
    assert clipped == {"a": 2, "b": 0}, "-0.7 rounds to -1 and 2.9 to 3, both outside 0..2"


def test_missing_values_and_columns_are_refused() -> None:
    _, domain = _tiny()
    with pytest.raises(ValueError, match="missing values"):
        tabddpm.to_codes(pd.DataFrame({"a": [0.0, np.nan], "b": [0, 1]}), domain)
    with pytest.raises(ValueError, match="no column"):
        tabddpm.to_codes(pd.DataFrame({"a": [0, 1]}), domain)


def test_without_its_environment_it_says_where_to_get_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    train, domain = _tiny()
    monkeypatch.setenv("FACSIMILE_SYNTHCITY_PYTHON", str(tmp_path / "no-python"))
    with pytest.raises(FileNotFoundError, match="synthcity-requirements"):
        tabddpm.METHOD.run(train, domain, seed=0, epsilon=None, n=10)


def test_not_in_the_grid_until_the_spike() -> None:
    assert "tabddpm" not in GRID and "tabddpm" not in methods()
    assert tabddpm.METHOD.family == "non-dp deep" and not tabddpm.METHOD.dp
