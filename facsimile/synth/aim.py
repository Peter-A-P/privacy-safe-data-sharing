"""AIM (SmartNoise, on Private-PGM): the state of the art at every budget in the 2025 benchmark.

Library defaults: two-way workload, model size capped at 80 MB, 16 rounds per attribute. The
domain transformer is fitted to the domain (`smartnoise_common.py`), so no budget is spent on
preprocessing and none is needed.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth import accounting
from facsimile.synth.base import DELTA, Fitted, Timer, Wrapped, seed_everything
from facsimile.synth.smartnoise_common import as_frame, transformer

PARAMS: dict[str, Any] = {"degree": 2, "max_model_size": 80, "max_cells": 10000, "rounds": None}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from snsynth.aim.aim import AIMSynthesizer

    assert epsilon is not None
    seed_everything(seed)
    synth = AIMSynthesizer(epsilon=epsilon, delta=DELTA, **PARAMS)
    with accounting.observe("snsynth.aim.aim", "cdp_rho") as calls, Timer() as fit_t:
        synth.fit(
            train.reset_index(drop=True),
            transformer=transformer(domain, "cube"),
            preprocessor_eps=0.0,
        )
    seed_everything(seed + 1_000_003)
    with Timer() as sample_t:
        table = as_frame(synth.sample(n), domain)
    record = accounting.zcdp_record(calls, epsilon=epsilon, delta=DELTA, method="aim")
    record["epsilon_after_preprocessing"] = float(synth.epsilon)
    return Fitted(table, {"delta": DELTA, **PARAMS}, record, fit_t.seconds, sample_t.seconds, "cpu")


METHOD = Wrapped("aim", "smartnoise-synth", "dp marginal", _run)
