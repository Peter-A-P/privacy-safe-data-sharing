"""Linkability risk (Giomi et al. 2023, section 4.2): join two halves of a record through the table.

The attacker holds two datasets about the same people with different attributes, A and B, and
uses the synthetic table to decide which rows belong together. For each target the attacker finds
its k nearest synthetic records on A alone and its k nearest on B alone; if the two neighbour sets
share a record, the halves are linked. Main attack on the targets, control attack on the control
records, and a baseline that draws both neighbour sets at random from the synthetic table.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from facsimile.attacks.neighbours import nearest
from facsimile.attacks.risk import AttackResult, result
from facsimile.prep import Domain


def linked(
    records: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    a: Sequence[str],
    b: Sequence[str],
    k: int,
    rng: np.random.Generator,
) -> np.ndarray:
    idx_a, _ = nearest(records, synthetic, domain, a, k=k, rng=rng)
    idx_b, _ = nearest(records, synthetic, domain, b, k=k, rng=rng)
    return np.array([bool(set(ra) & set(rb)) for ra, rb in zip(idx_a, idx_b, strict=True)])


def linkability(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    *,
    a: Sequence[str],
    b: Sequence[str],
    k: int = 1,
    seed: int = 0,
) -> AttackResult:
    if len(targets) != len(control):
        raise ValueError(
            "the target and control sets must be the same size for the rates to compare"
        )
    if set(a) & set(b):
        raise ValueError("the two halves must not share an attribute")
    rng = np.random.default_rng(seed)
    n = len(targets)
    main = linked(targets, synthetic, domain, a, b, k, rng)
    ctrl = linked(control, synthetic, domain, a, b, k, rng)
    m = len(synthetic)
    base = np.array(
        [
            bool(set(rng.choice(m, k, replace=False)) & set(rng.choice(m, k, replace=False)))
            for _ in range(n)
        ]
    )
    return result(
        "linkability",
        n,
        float(main.sum()),
        float(ctrl.sum()),
        float(base.sum()),
        {"a": list(a), "b": list(b), "k": k, "seed": seed},
    )
