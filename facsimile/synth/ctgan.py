"""CTGAN (SDV): the method most synthetic-data products ship. SDV's defaults, on the GPU if any."""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth.base import Fitted, Wrapped
from facsimile.synth.sdv_common import fit_sample

PARAMS: dict[str, Any] = {"epochs": 300, "batch_size": 500, "enable_gpu": True}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from sdv.single_table import CTGANSynthesizer

    return fit_sample(lambda md: CTGANSynthesizer(md, **PARAMS), PARAMS, train, domain, seed, n)


METHOD = Wrapped("ctgan", "sdv", "non-dp deep", _run)
