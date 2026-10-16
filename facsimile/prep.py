"""Preprocessing: every column becomes a small set of integer codes, and every code has a label.

The 2025 benchmark of differentially private tabular synthesis recommends uniform binning of
numeric columns and merging rare categories at a fixed threshold, and every synthesiser here
works in that one discrete domain. That is what makes the six comparable: the marginal methods
(AIM, MST) can only work on a discrete domain, and giving the deep and statistical methods the
same domain means a difference between them is the method, not the encoding.

**The domain spends no privacy budget, and that is a decision, not a default.** A domain read
off the training data leaks it: a category that appears once in training is a fact about one
person, and SmartNoise's own default (a transformer fitted to the data it is given) does exactly
that without charging epsilon for it. Here:

- Numeric bin edges are fixed in the dataset's spec from public knowledge (the codebook's
  range), uniform or uniform on a log scale for money, and never read from any split.
- Category sets are taken from the **test split**, which no synthesiser ever sees, after
  merging categories below `MIN_SHARE` of it into `OTHER`. The test split stands in for the
  public knowledge of a population's categories that every DP benchmark assumes; the people
  the guarantee protects are the training split, and nothing about them enters the domain.

The domain is published per dataset (`results/<dataset>/domain.json`). It holds category
names and bin edges, never a count.
"""

from __future__ import annotations

import itertools
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal

import numpy as np
import pandas as pd

MIN_SHARE: Final = 0.005
"""Categories rarer than half a percent of the domain split merge into `OTHER`."""

OTHER: Final = "OTHER"
MISSING: Final = "NA"

CODE_DTYPE: Final = "int16"


@dataclass(frozen=True, slots=True)
class Categorical:
    """A categorical column. `values`, when given, is the codebook and overrides the data."""

    name: str
    values: tuple[str, ...] | None = None
    nullable: bool = False
    min_share: float = MIN_SHARE


@dataclass(frozen=True, slots=True)
class Numeric:
    """A numeric column, binned between public bounds. Values outside are clipped.

    `edges`, when given, replaces the uniform grid: used where a task threshold must fall on an
    edge (income above 50,000 is a bin boundary, not a guess inside a bin).
    """

    name: str
    lo: float
    hi: float
    bins: int
    scale: Literal["linear", "log"] = "linear"
    nullable: bool = False
    edges: tuple[float, ...] | None = None


ColumnSpec = Categorical | Numeric


@dataclass(frozen=True, slots=True)
class ColumnDomain:
    """One column's codes: code i means labels[i]. Numeric columns also carry their edges."""

    name: str
    kind: Literal["categorical", "numeric"]
    labels: tuple[str, ...]
    edges: tuple[float, ...] = ()
    nullable: bool = False

    @property
    def size(self) -> int:
        return len(self.labels)


@dataclass(frozen=True, slots=True)
class Domain:
    columns: tuple[ColumnDomain, ...]
    min_share: float = MIN_SHARE
    note: str = field(default="category sets from the test split; bin edges from the spec")

    @property
    def names(self) -> list[str]:
        return [c.name for c in self.columns]

    @property
    def sizes(self) -> dict[str, int]:
        return {c.name: c.size for c in self.columns}

    def __getitem__(self, name: str) -> ColumnDomain:
        for c in self.columns:
            if c.name == name:
                return c
        raise KeyError(name)

    def cells(self) -> int:
        """The size of the full contingency table, which is what makes AIM slow."""
        return math.prod(c.size for c in self.columns)

    def to_json(self) -> dict[str, Any]:
        return {
            "note": self.note,
            "min_share": self.min_share,
            "columns": [
                {
                    "name": c.name,
                    "kind": c.kind,
                    "labels": list(c.labels),
                    "edges": list(c.edges),
                    "nullable": c.nullable,
                }
                for c in self.columns
            ],
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> Domain:
        return cls(
            columns=tuple(
                ColumnDomain(
                    name=c["name"],
                    kind=c["kind"],
                    labels=tuple(c["labels"]),
                    edges=tuple(float(e) for e in c["edges"]),
                    nullable=bool(c["nullable"]),
                )
                for c in payload["columns"]
            ),
            min_share=float(payload["min_share"]),
            note=str(payload["note"]),
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2) + "\n", encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> Domain:
        return cls.from_json(json.loads(path.read_text(encoding="utf-8")))


def bin_edges(spec: Numeric) -> tuple[float, ...]:
    """Uniform edges between the spec's bounds, on a log1p scale for heavy-tailed money."""
    if spec.edges is not None:
        if list(spec.edges) != sorted(set(spec.edges)) or len(spec.edges) < 2:
            raise ValueError(f"{spec.name}: explicit edges must be strictly increasing")
        return tuple(float(e) for e in spec.edges)
    if spec.bins < 1 or not spec.hi > spec.lo:
        raise ValueError(f"{spec.name}: bad binning {spec}")
    if spec.scale == "linear":
        edges = np.linspace(spec.lo, spec.hi, spec.bins + 1)
    else:
        if spec.lo < 0:
            raise ValueError(f"{spec.name}: log binning needs a non-negative lower bound")
        edges = np.expm1(np.linspace(np.log1p(spec.lo), np.log1p(spec.hi), spec.bins + 1))
    return tuple(float(round(e, 6)) for e in edges)


def _bin_labels(edges: Sequence[float]) -> list[str]:
    def fmt(x: float) -> str:
        return f"{x:g}"

    out = [f"[{fmt(a)}, {fmt(b)})" for a, b in itertools.pairwise(edges)]
    out[-1] = out[-1][:-1] + "]"
    return out


def _as_label(series: pd.Series) -> pd.Series:
    """Categorical values as strings, with integer-valued floats written as integers."""

    def one(v: object) -> object:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    return series.map(one)


def _label_order(label: str) -> tuple[int, float, str]:
    """Numeric codes in numeric order, then everything else alphabetically."""
    try:
        return (0, float(label), label)
    except ValueError:
        return (1, 0.0, label)


def fit_domain(specs: Sequence[ColumnSpec], domain_split: pd.DataFrame) -> Domain:
    """Build the domain from the specs and the split that stands in for public knowledge."""
    columns: list[ColumnDomain] = []
    for spec in specs:
        if isinstance(spec, Numeric):
            edges = bin_edges(spec)
            labels = _bin_labels(edges)
            if spec.nullable:
                labels.append(MISSING)
            columns.append(ColumnDomain(spec.name, "numeric", tuple(labels), edges, spec.nullable))
            continue
        if spec.values is not None:
            # A codebook is closed: a value outside it is an error, so there is no OTHER code
            # for a synthesiser to emit.
            labels = list(spec.values)
        else:
            observed = _as_label(domain_split[spec.name]).dropna()
            shares = observed.value_counts(normalize=True)
            keep = sorted(
                (str(v) for v, s in shares.items() if s >= spec.min_share), key=_label_order
            )
            labels = [*keep, OTHER]
        if spec.nullable:
            labels.append(MISSING)
        columns.append(ColumnDomain(spec.name, "categorical", tuple(labels), (), spec.nullable))
    return Domain(
        tuple(columns),
        min_share=min(
            (s.min_share for s in specs if isinstance(s, Categorical)), default=MIN_SHARE
        ),
    )


def encode(frame: pd.DataFrame, domain: Domain) -> pd.DataFrame:
    """Raw values to codes. Every value lands somewhere: rare to OTHER, missing to NA."""
    out: dict[str, np.ndarray[Any, np.dtype[np.int16]]] = {}
    for col in domain.columns:
        raw = frame[col.name]
        if col.kind == "numeric":
            values = pd.to_numeric(raw, errors="coerce").to_numpy(dtype=float)
            missing = np.isnan(values)
            if missing.any() and not col.nullable:
                raise ValueError(
                    f"{col.name}: {int(missing.sum())} missing values in a non-nullable column"
                )
            edges = np.asarray(col.edges)
            clipped = np.clip(np.nan_to_num(values, nan=edges[0]), edges[0], edges[-1])
            n_bins = len(edges) - 1
            codes = np.clip(np.searchsorted(edges, clipped, side="right") - 1, 0, n_bins - 1)
            if col.nullable:
                codes = np.where(missing, n_bins, codes)
        else:
            labels = _as_label(raw)
            index = {label: i for i, label in enumerate(col.labels)}
            other = index.get(OTHER, -1)
            missing_code = index.get(MISSING)
            is_missing = labels.isna().to_numpy()
            if is_missing.any() and missing_code is None:
                raise ValueError(
                    f"{col.name}: {int(is_missing.sum())} missing values in a non-nullable column"
                )
            codes = labels.map(index).fillna(other).to_numpy(dtype=np.int64)
            if other == -1 and ((codes == -1) & ~is_missing).any():
                bad = sorted(set(labels[(codes == -1) & ~is_missing]))[:5]
                raise ValueError(f"{col.name}: values {bad} are outside its codebook")
            if missing_code is not None:
                codes = np.where(is_missing, missing_code, codes)
        out[col.name] = np.asarray(codes, dtype=CODE_DTYPE)
    return pd.DataFrame(out, index=frame.index)


def decode(codes: pd.DataFrame, domain: Domain) -> pd.DataFrame:
    """Codes to labels: the inverse map, for reading a table rather than for computing on it."""
    out = {}
    for col in domain.columns:
        labels = np.asarray(col.labels, dtype=object)
        out[col.name] = labels[codes[col.name].to_numpy()]
    return pd.DataFrame(out, index=codes.index)


def midpoints(codes: pd.DataFrame, domain: Domain) -> pd.DataFrame:
    """Numeric columns at their bin midpoints, NaN for NA; categorical columns as labels."""
    out = decode(codes, domain)
    for col in domain.columns:
        if col.kind != "numeric":
            continue
        edges = np.asarray(col.edges)
        mids = (
            np.append((edges[:-1] + edges[1:]) / 2, np.nan)
            if col.nullable
            else (edges[:-1] + edges[1:]) / 2
        )
        out[col.name] = mids[codes[col.name].to_numpy()]
    return out


def check_codes(codes: pd.DataFrame, domain: Domain) -> None:
    """Every column present, in order, and every code inside its column's range."""
    if list(codes.columns) != domain.names:
        raise ValueError(f"columns {list(codes.columns)} do not match the domain {domain.names}")
    for col in domain.columns:
        values = codes[col.name].to_numpy()
        if values.size and (values.min() < 0 or values.max() >= col.size):
            raise ValueError(f"{col.name}: codes outside 0..{col.size - 1}")
