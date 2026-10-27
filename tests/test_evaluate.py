"""The one-call entry point on raw tables: a copy is caught, an independent table is not.

The same sanity pair as `test_attack_sanity.py`, but through `evaluate`, on tables that were
never coded: string categories, raw ages and hours, and the coding read from the control set. If
the reusable path codes or wires anything differently from the project's own, this fails.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from facsimile.attacks.evaluate import evaluate, infer_columns
from facsimile.cli import main
from facsimile.prep import Categorical, Numeric

CONTROL_LEVEL = 0.02


def raw_population(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    job = rng.integers(0, 20, n)
    age = rng.integers(18, 90, n)
    return pd.DataFrame(
        {
            "region": [f"r{v}" for v in rng.zipf(1.6, n) % 30],
            "postcode": [f"p{v}" for v in rng.integers(0, 2000, n)],
            "job": [f"job{v}" for v in job],
            "sex": rng.choice(["F", "M"], n),
            "age": age,
            "hours": rng.integers(0, 80, n),
            "secret": [f"s{v}" for v in (job // 4 + age // 45 + rng.integers(0, 2, n)) % 6],
        }
    )


@pytest.fixture(scope="module")
def tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = raw_population(9000, seed=0)
    train = raw.iloc[:3000].reset_index(drop=True)
    return train.iloc[:600], raw.iloc[3000:3600], train, raw.iloc[6000:9000]


def test_columns_are_read_from_the_control_alone(tables) -> None:  # type: ignore[no-untyped-def]
    _, control, _, _ = tables
    specs = {s.name: s for s in infer_columns(control)}
    assert isinstance(specs["age"], Numeric) and isinstance(specs["hours"], Numeric)
    assert specs["age"].lo == control["age"].min() and specs["age"].hi == control["age"].max()
    assert isinstance(specs["job"], Categorical) and isinstance(specs["sex"], Categorical)


def test_a_copy_is_caught_and_an_independent_table_is_not(tables) -> None:  # type: ignore[no-untyped-def]
    targets, control, train, independent = tables
    a, b = ["region", "job", "sex"], ["age", "hours", "secret"]
    copied = evaluate(
        targets, control, train, secret="secret", n_attacks=300, k_values=(5,), link_a=a, link_b=b
    )
    assert {"inference", "linkability_k5"} <= set(copied.detected), copied.markdown()
    assert copied.attacks["inference"].risk.value > 0.6
    fresh = evaluate(
        targets,
        control,
        independent,
        secret="secret",
        n_attacks=300,
        k_values=(5,),
        link_a=a,
        link_b=b,
    )
    for name, r in fresh.attacks.items():
        assert r.risk.lo < CONTROL_LEVEL, (name, fresh.markdown())


def test_unequal_targets_and_control_are_refused(tables) -> None:  # type: ignore[no-untyped-def]
    targets, control, train, _ = tables
    with pytest.raises(ValueError, match="same size"):
        evaluate(targets, control.iloc[:-1], train, secret="secret")


def test_the_command_reads_files_and_writes_the_result(tables, tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    targets, control, train, _ = tables
    paths = []
    for name, frame in (("t.csv", targets), ("c.csv", control), ("s.parquet", train)):
        path = tmp_path / name
        frame.to_parquet(path) if name.endswith(".parquet") else frame.to_csv(path, index=False)
        paths.append(str(path))
    out = tmp_path / "result.json"
    assert (
        main(["evaluate", *paths, "--secret", "secret", "--n-attacks", "200", "--out", str(out)])
        == 0
    )
    assert "| inference |" in capsys.readouterr().out
    assert "inference" in out.read_text(encoding="utf-8")
