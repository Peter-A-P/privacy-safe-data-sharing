"""Distance to closest record: the metric vendors quote, computed beside the attacks on the same tables.

Rule C candidate 1 (PLAN.md section 10) is that DCR is a privacy metric. To test it, the same
distance the attacks use is reported the two ways it is usually quoted:

- **Exact-copy rate**: the share of target records with a synthetic record at distance zero,
  beside the same share for the control records. A copy of a training row shows up here.
- **Closer-to-training share** (the "DCR protection" form): for each synthetic record, whether
  its nearest real record is a target rather than a control record, ties split evenly. Half is
  what a table that knows nothing about the targets scores, and is what "passes".

Both are reported with intervals; neither is a risk in the paper's sense, and the README reports
them as what they are.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from facsimile.attacks.neighbours import nearest
from facsimile.prep import Domain
from facsimile.utility.stats import bootstrap, clopper_pearson


def closest(records: pd.DataFrame, pool: pd.DataFrame, domain: Domain, seed: int) -> np.ndarray:
    _, dist = nearest(records, pool, domain, domain.names, k=1, rng=np.random.default_rng(seed))
    return dist[:, 0]


def dcr(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    *,
    seed: int = 0,
    sample: int = 4000,
) -> dict[str, Any]:
    if len(targets) != len(control):
        raise ValueError("the target and control sets must be the same size")
    d_targets = closest(targets, synthetic, domain, seed)
    d_control = closest(control, synthetic, domain, seed + 1)
    rng = np.random.default_rng(seed + 2)
    picked = synthetic.iloc[rng.choice(len(synthetic), min(sample, len(synthetic)), replace=False)]
    to_t = closest(picked, targets, domain, seed + 3)
    to_c = closest(picked, control, domain, seed + 4)
    closer = np.where(to_t < to_c, 1.0, np.where(to_t > to_c, 0.0, 0.5))
    n = len(targets)
    return {
        "exact_copy_targets": clopper_pearson(int((d_targets == 0).sum()), n).as_dict(),
        "exact_copy_control": clopper_pearson(int((d_control == 0).sum()), n).as_dict(),
        "median_dcr_targets": float(np.median(d_targets)),
        "median_dcr_control": float(np.median(d_control)),
        "mean_dcr_targets": bootstrap(d_targets.tolist(), seed=seed).as_dict(),
        "mean_dcr_control": bootstrap(d_control.tolist(), seed=seed + 1).as_dict(),
        "closer_to_training_share": bootstrap(closer.tolist(), seed=seed + 2).as_dict(),
        "synthetic_sampled": len(picked),
    }
