"""The gate's items estimate AUC, never reuse a record, and the candidates follow the stated rule."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from facsimile import gate, report
from facsimile.utility.tstr import auc


def test_pairs_are_disjoint_and_one_of_each_class() -> None:
    y = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0], dtype=np.int64)
    items = gate.pairs(y)
    assert len(items) == 3, "as many pairs as the smaller class"
    assert (y[items[:, 0]] == 1).all() and (y[items[:, 1]] == 0).all()
    assert len(set(items.ravel())) == items.size, "no record in two pairs"


def test_share_of_pairs_correct_estimates_auc() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 20_000).astype(np.int64)
    scores = rng.normal(size=len(y)) + 0.8 * y
    got, level = gate.outcomes(scores, gate.pairs(y))
    assert level == 0
    assert np.mean(list(got.values())) == pytest.approx(auc(y, scores), abs=0.015)


def test_a_level_pair_is_left_out_and_counted() -> None:
    scores = np.array([0.9, 0.1, 0.5, 0.5])
    items = np.array([[0, 1], [2, 3]])
    got, level = gate.outcomes(scores, items)
    assert got == {"pair-0": True} and level == 1


def _cell(ds: str, method: str, eps: float | None, deltas: list[float]) -> dict[str, Any]:
    return {
        "dataset": ds,
        "method": method,
        "epsilon": eps,
        "utility": {f"t{i}": {"delta": d} for i, d in enumerate(deltas)},
    }


def test_candidates_are_nearest_overall_and_nearest_with_a_budget() -> None:
    cells = [
        _cell("acs", "tvae", None, [-0.05, -0.04]),
        _cell("acs", "ctgan", None, [-0.03, -0.09]),
        _cell("acs", "aim", 1.0, [-0.12, -0.15]),
        _cell("acs", "mst", 8.0, [-0.30, -0.10]),
    ]
    assert gate.candidates({"cells": cells}) == [("acs", "tvae", None), ("acs", "aim", 1.0)]


def test_a_run_whose_every_suite_warns_is_not_a_pass(tmp_path: Any) -> None:
    suite = {"verdict": "warn", "difference": -0.1, "lo": -0.15, "hi": -0.05}
    (tmp_path / "gate.json").write_text(
        '{"delta_points": 2.0, "runs": [{"suites": [' + str(suite).replace("'", '"') + "]}]}",
        encoding="utf-8",
    )
    assert report.gate_runs(tmp_path)["runs"][0]["outcome"] == "not decided"
