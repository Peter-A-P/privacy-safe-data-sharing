"""TVAE (SDV): the variational autoencoder beside CTGAN. SDV's defaults, on the GPU if any."""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth.base import Fitted, Wrapped
from facsimile.synth.sdv_common import fit_sample

PARAMS: dict[str, Any] = {"epochs": 300, "batch_size": 500, "enable_gpu": True}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from sdv.single_table import TVAESynthesizer

    return fit_sample(lambda md: TVAESynthesizer(md, **PARAMS), PARAMS, train, domain, seed, n)


METHOD = Wrapped("tvae", "sdv", "non-dp deep", _run)
