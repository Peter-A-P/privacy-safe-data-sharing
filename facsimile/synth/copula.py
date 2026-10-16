"""Gaussian copula (SDV): the baseline every vendor starts from. Library defaults throughout."""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth.base import Fitted, Wrapped
from facsimile.synth.sdv_common import fit_sample

PARAMS: dict[str, Any] = {"default_distribution": "beta"}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from sdv.single_table import GaussianCopulaSynthesizer

    return fit_sample(
        lambda md: GaussianCopulaSynthesizer(md, **PARAMS), PARAMS, train, domain, seed, n
    )


METHOD = Wrapped("copula", "sdv", "non-dp statistical", _run)
