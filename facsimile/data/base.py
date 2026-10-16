"""What a dataset is to this project: a raw loader, an attribute subset, tasks, and split sizes.

Each dataset module (`acs.py`, `ieeecis.py`, `sparcs.py`) declares one `DatasetSpec`. The
attribute subset is the `columns` list and is published with the domain; the tasks say which
column is predicted from which, on which rows, in the coded domain, so a task can be run on a
synthetic table exactly as on a real one.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.data.split import Sizes
from facsimile.prep import ColumnSpec, Domain

ROW_ID = "row_id"
"""The column every raw loader adds: the dataset's own identifier for a record."""


@dataclass(frozen=True, slots=True)
class Condition:
    """A row filter in the coded domain: a numeric column at or above a threshold, or present."""

    column: str
    at_least: float | None = None
    present: bool = False


@dataclass(frozen=True, slots=True)
class Task:
    """A downstream binary task, defined on codes so it runs on real and synthetic tables alike.

    The target is positive where the column's label is in `positive_labels` (categorical) or
    the bin's lower edge is at or above `at_least` (numeric; the threshold must be an edge).
    """

    name: str
    target: str
    features: tuple[str, ...]
    positive_labels: tuple[str, ...] = ()
    at_least: float | None = None
    where: tuple[Condition, ...] = ()
    note: str = ""

    def positive_codes(self, domain: Domain) -> NDArray[np.int64]:
        col = domain[self.target]
        if col.kind == "categorical":
            if not self.positive_labels:
                raise ValueError(f"{self.name}: a categorical target needs positive labels")
            missing = set(self.positive_labels) - set(col.labels)
            if missing:
                raise ValueError(f"{self.name}: labels {sorted(missing)} not in the domain")
            return np.asarray(
                [col.labels.index(lab) for lab in self.positive_labels], dtype=np.int64
            )
        if self.at_least is None:
            raise ValueError(f"{self.name}: a numeric target needs a threshold")
        return np.asarray(_codes_at_least(domain, self.target, self.at_least), dtype=np.int64)

    def rows(self, codes: pd.DataFrame, domain: Domain) -> NDArray[np.bool_]:
        """Which rows are in the task's population."""
        keep = np.ones(len(codes), dtype=bool)
        for cond in self.where:
            col = domain[cond.column]
            values = codes[cond.column].to_numpy()
            if cond.present:
                if not col.nullable:
                    raise ValueError(f"{cond.column}: 'present' on a column with no NA code")
                keep &= values != col.size - 1
            if cond.at_least is not None:
                keep &= np.isin(values, _codes_at_least(domain, cond.column, cond.at_least))
        return keep

    def xy(self, codes: pd.DataFrame, domain: Domain) -> tuple[pd.DataFrame, NDArray[np.int64]]:
        keep = self.rows(codes, domain)
        subset = codes.loc[keep]
        y = np.isin(subset[self.target].to_numpy(), self.positive_codes(domain)).astype(np.int64)
        return subset[list(self.features)], y


def _codes_at_least(domain: Domain, column: str, threshold: float) -> list[int]:
    col = domain[column]
    if col.kind != "numeric":
        raise ValueError(f"{column}: a threshold needs a numeric column")
    edges = list(col.edges)
    if threshold not in edges[:-1]:
        raise ValueError(f"{column}: threshold {threshold} is not a bin edge of {edges}")
    first = edges.index(threshold)
    return list(range(first, len(edges) - 1))


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    name: str
    title: str
    columns: tuple[ColumnSpec, ...]
    tasks: tuple[Task, ...]
    sizes: Sizes
    split_seed: int
    publish_ids: bool
    """Whether split ids may be published. False where a row reference is itself restricted."""
    load_raw: Callable[[], pd.DataFrame]
    """The raw table with `row_id`, restricted to the population and the attribute subset."""
    fetch: Callable[[], None]
    notes: tuple[str, ...] = field(default=())

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]
