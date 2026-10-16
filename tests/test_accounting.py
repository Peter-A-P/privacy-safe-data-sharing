"""The accountant test: every DP table's recorded epsilon and delta are what the library was asked for.

Two halves. The first runs a small fit and checks the observation itself: the library's own
conversion was called once with the requested budget and nothing was spent on preprocessing.
The second walks every published record of a DP table in `results/` and recomputes, with the
pinned OpenDP, the rho that budget implies, so a record that drifted from its request, or a
library upgrade that changed the conversion, fails here before any number ships.
"""

from __future__ import annotations

import json
import math
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from facsimile.paths import RESULTS
from facsimile.prep import Categorical, fit_domain
from facsimile.synth import accounting, methods
from facsimile.synth.base import DELTA
from facsimile.synth.smartnoise_common import transformer


@cache
def _cdp_rho(epsilon: float, delta: float) -> float:
    from snsynth.utils import cdp_rho

    return float(cdp_rho(epsilon, delta))


def _records() -> list[tuple[Path, dict[str, Any]]]:
    out = []
    for path in sorted(RESULTS.glob("*/synth/*/*/seed*.json")):
        if path.name.endswith(".failed.json"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload["accounting"].get("dp"):
            out.append((path, payload))
    return out


@pytest.mark.parametrize(
    ("path", "record"),
    [pytest.param(path, record, id=str(path.relative_to(RESULTS))) for path, record in _records()]
    or [pytest.param(None, None, marks=pytest.mark.skip(reason="no DP tables yet"))],
)
def test_every_published_dp_record_matches_its_request(path: Path, record: dict[str, Any]) -> None:
    acc = record["accounting"]
    assert acc["epsilon_requested"] == record["epsilon"], path
    assert acc["delta"] == DELTA, path
    if record["method"] in {"aim", "mst"}:
        assert acc["epsilon_passed_to_accountant"] == record["epsilon"], (
            "budget spent before the accountant"
        )
        assert acc["delta_passed_to_accountant"] == DELTA
        assert acc["epsilon_after_preprocessing"] == record["epsilon"], "preprocessing spent budget"
        assert acc["rho"] == pytest.approx(_cdp_rho(record["epsilon"], DELTA), rel=1e-9)
    elif record["method"] == "pate_ctgan":
        assert acc["epsilon_spent"] == pytest.approx(acc["epsilon_requested"] + acc["overshoot"])
        assert acc["accountant_calls"] > 0
    else:
        pytest.fail(f"{path}: a DP record from an unknown method {record['method']}")


def test_pate_epsilon_is_the_library_formula() -> None:
    import torch

    # The library's own expression (patectgan.py, the stopping test), on its own tensor types:
    # eps = min((alphas - math.log(delta)) / l_list), l_list = 1 + range(moments_order).
    alphas = [5.0, 1.0, 9.0]
    l_list = 1 + torch.tensor(range(len(alphas)))
    library = float(min((torch.tensor(alphas) - math.log(1e-5)) / l_list))
    assert accounting.pate_epsilon(alphas, 1e-5) == pytest.approx(library)
    # Worked by hand: 16.51, 6.26, 6.84 for l = 1, 2, 3, so the l = 2 term is the minimum.
    assert library == pytest.approx((1.0 - math.log(1e-5)) / 2)


def _tiny() -> tuple[pd.DataFrame, Any]:
    rng = np.random.default_rng(0)
    specs = (Categorical("a", values=("0", "1", "2")), Categorical("b", values=("0", "1")))
    raw = pd.DataFrame({"a": rng.integers(0, 2, 400), "b": rng.integers(0, 2, 400)})
    domain = fit_domain(specs, raw)
    from facsimile.prep import encode

    return encode(raw, domain), domain


def test_the_domain_transformer_is_complete_before_it_sees_a_record() -> None:
    train, domain = _tiny()
    assert 2 not in set(train["a"])  # code 2 never occurs in the training data
    tt = transformer(domain, "cube")
    assert tt.fit_complete and list(tt.cardinality) == [3, 2]


@pytest.mark.slow
def test_mst_calls_the_accountant_once_with_the_request_and_spends_nothing_on_preprocessing() -> (
    None
):
    train, domain = _tiny()
    fitted = methods()["mst"].run(train, domain, seed=0, epsilon=1.0, n=100)
    acc = fitted.accounting
    assert acc["epsilon_passed_to_accountant"] == 1.0 and acc["delta_passed_to_accountant"] == DELTA
    assert acc["rho"] == pytest.approx(_cdp_rho(1.0, DELTA))
    assert acc["epsilon_after_preprocessing"] == 1.0
    assert len(fitted.table) == 100 and set(fitted.table["a"]) <= {0, 1, 2}
