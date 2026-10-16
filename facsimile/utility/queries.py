"""Fidelity: error on one-, two- and three-way marginal queries. Reported as fidelity, never as utility.

For each k, the total variation distance between the synthetic table's k-way marginal and the
training split's, over every one-way marginal and a seeded sample of the two- and three-way ones.
The mean over marginals carries a bootstrap interval over marginals.
"""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
import pandas as pd

from facsimile.prep import Domain
from facsimile.utility.stats import bootstrap

SAMPLE = 200


def tvd(a: pd.DataFrame, b: pd.DataFrame, cols: list[str]) -> float:
    pa = a.groupby(cols).size() / len(a)
    pb = b.groupby(cols).size() / len(b)
    joined = pd.concat([pa, pb], axis=1).fillna(0.0)
    return float(0.5 * (joined.iloc[:, 0] - joined.iloc[:, 1]).abs().sum())


def marginal_error(
    synthetic: pd.DataFrame, real: pd.DataFrame, domain: Domain, *, seed: int = 0
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    out: dict[str, Any] = {}
    for k in (1, 2, 3):
        combos = list(itertools.combinations(domain.names, k))
        if len(combos) > SAMPLE:
            combos = [combos[i] for i in sorted(rng.choice(len(combos), SAMPLE, replace=False))]
        errors = [tvd(synthetic, real, list(c)) for c in combos]
        out[f"{k}way"] = {**bootstrap(errors, seed=seed).as_dict(), "marginals": len(combos)}
    return out
