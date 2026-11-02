"""Singling-out risk (Giomi et al. 2023, section 4.1): isolate one real record with a predicate.

The attacker reads predicates off the synthetic table that match exactly one synthetic record,
and bets that each matches exactly one real record too. Two kinds, as in the paper:

- **Univariate**: one attribute. A category that occurs once in the synthetic table, and for a
  numeric attribute "at most its minimum" and "at least its maximum".
- **Multivariate**: `n_cols` attributes of a synthetic record chosen at random, each as equality
  for a category, and for a numeric attribute "at least" its value if the value is above the
  column's median and "at most" otherwise.

A predicate succeeds if it matches exactly one record of the set attacked. The main attack is
on the targets, the control attack on the control records, which are the same size so that no
size correction is needed; the baseline uses random predicates that ignore the synthetic table's
records. The success rate's denominator is the number of predicates asked for, so a table that
yields fewer singling-out predicates scores lower, as in the reference library.

Following the reference library, duplicate rows are dropped from each table before predicates
are made or counted. `docs/attacks.md` records the choice and its effect.

Which predicates the search finds is random, and that noise alone moved one configuration across
the detection line (PLAN.md section 2.12). So a risk averages `SEARCHES` independent searches on
the same table and the same records: the successes are the mean over the searches and the trials
stay at the number of attacks, because the searches reuse the same records and are not
independent trials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.attacks.risk import AttackResult, result
from facsimile.prep import Domain

Mode = Literal["univariate", "multivariate"]

EQ, NE, LT, GT, LE, GE = range(6)
BATCH = 10_000
SEARCHES: Final = 5
SEARCH_STRIDE: Final = 1_000


def search_seeds(seed: int, searches: int = SEARCHES) -> list[int]:
    """The seeds of the searches averaged: the table's own seed first, so the first search is the
    one run before section 2.12, then a stride apart."""
    return [seed + SEARCH_STRIDE * k for k in range(searches)]


@dataclass(frozen=True, slots=True)
class Predicates:
    """A batch of conjunctive predicates: column index, operator and code for each term."""

    cols: NDArray[np.int64]  # (q, t)
    ops: NDArray[np.int64]  # (q, t)
    vals: NDArray[np.int64]  # (q, t)

    def __len__(self) -> int:
        return int(self.cols.shape[0])

    def keys(self) -> list[bytes]:
        order = np.argsort(self.cols, axis=1, kind="stable")
        stacked = np.stack(
            [np.take_along_axis(a, order, axis=1) for a in (self.cols, self.ops, self.vals)], axis=2
        )
        return [row.tobytes() for row in stacked]

    def subset(self, keep: NDArray[np.bool_] | NDArray[np.int64]) -> Predicates:
        return Predicates(self.cols[keep], self.ops[keep], self.vals[keep])


_POPCOUNT = np.array([bin(i).count("1") for i in range(256)], dtype=np.int64)


class Bitsets:
    """For every column, operator and code, the set of rows it matches, packed eight to a byte.

    A predicate's count is then the popcount of the AND of its terms' bitsets, which is what makes
    a million candidate predicates against twenty thousand rows a matter of seconds.
    """

    def __init__(self, values: NDArray[np.int16]) -> None:
        self.rows = len(values)
        self.width = max(int(values.max()) + 2, 2) if values.size else 2
        tables = []
        for j in range(values.shape[1]):
            col = values[:, j][None, :]
            codes = np.arange(self.width)[:, None]
            per_op = [
                col == codes,
                col != codes,
                col < codes,
                col > codes,
                col <= codes,
                col >= codes,
            ]
            tables.append(np.stack([np.packbits(m, axis=1) for m in per_op]))  # (6, width, bytes)
        self.tables = np.stack(tables)  # (cols, 6, width, bytes)

    def counts(self, preds: Predicates) -> NDArray[np.int64]:
        out = np.empty(len(preds), dtype=np.int64)
        for start in range(0, len(preds), 2000):
            cols = preds.cols[start : start + 2000]
            ops = preds.ops[start : start + 2000]
            vals = np.clip(preds.vals[start : start + 2000], 0, self.width - 1)
            terms = self.tables[cols, ops, vals]  # (q, t, bytes)
            joint = np.bitwise_and.reduce(terms, axis=1)
            out[start : start + 2000] = _POPCOUNT[joint].sum(axis=1)
        return out


def counts(values: NDArray[np.int16] | Bitsets, preds: Predicates) -> NDArray[np.int64]:
    """How many rows of `values` each predicate matches."""
    if len(preds) == 0:
        return np.zeros(0, dtype=np.int64)
    bits = values if isinstance(values, Bitsets) else Bitsets(values)
    return bits.counts(preds)


def _unique_rows(frame: pd.DataFrame) -> NDArray[np.int16]:
    return np.unique(frame.to_numpy(dtype=np.int16), axis=0)


def univariate(
    syn: NDArray[np.int16], numeric: NDArray[np.bool_], n: int, rng: np.random.Generator
) -> Predicates:
    cols, ops, vals = [], [], []
    for j in range(syn.shape[1]):
        column = syn[:, j]
        values, freq = np.unique(column, return_counts=True)
        for v in values[freq == 1]:
            cols.append(j)
            ops.append(EQ)
            vals.append(int(v))
        if numeric[j]:
            cols += [j, j]
            ops += [LE, GE]
            vals += [int(column.min()), int(column.max())]
    order = rng.permutation(len(cols))
    preds = Predicates(
        np.asarray(cols, dtype=np.int64)[order, None],
        np.asarray(ops, dtype=np.int64)[order, None],
        np.asarray(vals, dtype=np.int64)[order, None],
    )
    return _keep_singling(syn, preds, n)


def multivariate(
    syn: NDArray[np.int16],
    numeric: NDArray[np.bool_],
    n: int,
    n_cols: int,
    max_attempts: int,
    rng: np.random.Generator,
) -> Predicates:
    medians = np.median(syn, axis=0)
    bits = Bitsets(syn)
    kept: list[Predicates] = []
    seen: set[bytes] = set()
    total, attempts = 0, 0
    while total < n and attempts < max_attempts:
        size = min(BATCH, max_attempts - attempts)
        rows = syn[rng.integers(0, len(syn), size)]
        cols = np.stack([rng.choice(syn.shape[1], n_cols, replace=False) for _ in range(size)])
        vals = np.take_along_axis(rows, cols, axis=1).astype(np.int64)
        above = vals > medians[cols]
        ops = np.where(numeric[cols], np.where(above, GE, LE), EQ)
        batch = Predicates(cols.astype(np.int64), ops.astype(np.int64), vals)
        single = counts(bits, batch) == 1
        batch = batch.subset(single)
        fresh = []
        for i, key in enumerate(batch.keys()):
            if key not in seen:
                seen.add(key)
                fresh.append(i)
        batch = batch.subset(np.asarray(fresh, dtype=np.int64))
        kept.append(batch)
        total += len(batch)
        attempts += size
    if not kept:
        return Predicates(*(np.zeros((0, n_cols), dtype=np.int64) for _ in range(3)))
    joined = Predicates(
        *(np.concatenate([getattr(k, f) for k in kept]) for f in ("cols", "ops", "vals"))
    )
    return joined.subset(np.arange(min(n, len(joined))))


def _keep_singling(syn: NDArray[np.int16], preds: Predicates, n: int) -> Predicates:
    single = np.flatnonzero(counts(syn, preds) == 1)
    seen: set[bytes] = set()
    keep = []
    keys = preds.keys()
    for i in single:
        if keys[i] not in seen:
            seen.add(keys[i])
            keep.append(i)
        if len(keep) >= n:
            break
    return preds.subset(np.asarray(keep, dtype=np.int64))


def random_predicates(
    syn: NDArray[np.int16],
    numeric: NDArray[np.bool_],
    n: int,
    n_cols: int,
    rng: np.random.Generator,
) -> Predicates:
    """The baseline: random columns, a random value each column takes, a random operator."""
    uniques = [np.unique(syn[:, j]) for j in range(syn.shape[1])]
    cols = np.stack([rng.choice(syn.shape[1], n_cols, replace=False) for _ in range(n)])
    vals = np.vectorize(lambda j: int(rng.choice(uniques[j])))(cols)
    ops = np.where(numeric[cols], rng.integers(0, 6, cols.shape), rng.integers(0, 2, cols.shape))
    return Predicates(cols.astype(np.int64), ops.astype(np.int64), vals.astype(np.int64))


def _search(
    tgt: NDArray[np.int16],
    ctl: NDArray[np.int16],
    syn: NDArray[np.int16],
    numeric: NDArray[np.bool_],
    mode: Mode,
    n_attacks: int,
    n_cols: int,
    max_attempts: int,
    seed: int,
) -> tuple[int, int, int, int]:
    """One search: successes on the targets, the control and the baseline, and predicates found."""
    rng = np.random.default_rng(seed)
    if mode == "univariate":
        preds = univariate(syn, numeric, n_attacks, rng)
        width = 1
    else:
        preds = multivariate(syn, numeric, n_attacks, n_cols, max_attempts, rng)
        width = n_cols
    tgt_bits = Bitsets(tgt)
    main = int((counts(tgt_bits, preds) == 1).sum())
    ctrl = int((counts(ctl, preds) == 1).sum())
    base_preds = random_predicates(syn, numeric, n_attacks, width, rng)
    base = int((counts(tgt_bits, base_preds) == 1).sum())
    return main, ctrl, base, len(preds)


def singling_out(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    *,
    mode: Mode = "multivariate",
    n_attacks: int = 2000,
    n_cols: int = 3,
    max_attempts: int = 1_000_000,
    seed: int = 0,
    searches: int = SEARCHES,
) -> AttackResult:
    if len(targets) != len(control):
        raise ValueError(
            "the target and control sets must be the same size for the rates to compare"
        )
    if searches < 1:
        raise ValueError("at least one search")
    names = domain.names
    numeric = np.array([domain[c].kind == "numeric" for c in names])
    syn = _unique_rows(synthetic[names])
    tgt = _unique_rows(targets[names])
    ctl = _unique_rows(control[names])
    seeds = search_seeds(seed, searches)
    runs = [
        _search(tgt, ctl, syn, numeric, mode, n_attacks, n_cols, max_attempts, s) for s in seeds
    ]
    main, ctrl, base, found = (np.asarray(x, dtype=np.int64) for x in zip(*runs, strict=True))
    return result(
        f"singling_out_{mode}",
        n_attacks,
        float(main.mean()),
        float(ctrl.mean()),
        float(base.mean()),
        {
            "mode": mode,
            "n_cols": 1 if mode == "univariate" else n_cols,
            "predicates_found": int(found.min()),
            "max_attempts": max_attempts,
            "unique_rows": {"synthetic": len(syn), "targets": len(tgt), "control": len(ctl)},
            "seed": seed,
            "searches": {
                "seeds": seeds,
                "main": main.tolist(),
                "control": ctrl.tolist(),
                "baseline": base.tolist(),
                "predicates_found": found.tolist(),
            },
        },
    )
