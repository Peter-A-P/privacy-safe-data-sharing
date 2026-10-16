"""Tasks are defined on codes, so they run on a synthetic table exactly as on a real one."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from facsimile import data
from facsimile.data.base import Condition, Task
from facsimile.prep import Categorical, Numeric, encode, fit_domain

SPECS = (
    Numeric("income", lo=-100, hi=1000, bins=3, edges=(-100, 101, 501, 1000)),
    Numeric("hours", lo=1, hi=99, bins=2, edges=(1, 40, 99), nullable=True),
    Categorical("status", values=("1", "2", "3")),
)

RAW = pd.DataFrame(
    {
        "income": [50, 200, 600, 900, 700],
        "hours": [10, np.nan, 45, 45, 20],
        "status": [1, 2, 1, 3, 1],
    }
)


def test_numeric_target_threshold_must_be_an_edge() -> None:
    domain = fit_domain(SPECS, RAW)
    ok = Task("rich", "income", ("status",), at_least=501)
    assert ok.positive_codes(domain).tolist() == [2]
    with pytest.raises(ValueError, match="not a bin edge"):
        Task("rich", "income", ("status",), at_least=500).positive_codes(domain)


def test_population_conditions_and_targets() -> None:
    domain = fit_domain(SPECS, RAW)
    codes = encode(RAW, domain)
    task = Task(
        "rich",
        "income",
        ("status",),
        at_least=501,
        where=(Condition("income", at_least=101), Condition("hours", present=True)),
    )
    x, y = task.xy(codes, domain)
    # Row 0 fails income >= 101, row 1 has no hours; rows 2, 3, 4 remain, all above 501.
    assert len(x) == 3 and y.tolist() == [1, 1, 1]
    cat = Task("one", "status", ("income",), positive_labels=("1",))
    assert cat.xy(codes, domain)[1].tolist() == [1, 0, 1, 0, 1]


def test_every_registered_task_names_columns_that_exist() -> None:
    for spec in data.registry().values():
        names = set(spec.column_names)
        for task in spec.tasks:
            assert task.target in names
            assert set(task.features) <= names
            assert task.target not in task.features
            for cond in task.where:
                assert cond.column in names
