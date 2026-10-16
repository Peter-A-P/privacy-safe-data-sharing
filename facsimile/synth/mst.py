"""MST (SmartNoise, on Private-PGM): the NIST 2018 winner, a maximum spanning tree of 2-way marginals.

Library defaults. The domain transformer is fitted to the domain, so no budget goes to
preprocessing.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth import accounting
from facsimile.synth.base import DELTA, Fitted, Timer, Wrapped, seed_everything
from facsimile.synth.smartnoise_common import as_frame, transformer

PARAMS: dict[str, Any] = {}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from snsynth.mst.mst import MSTSynthesizer

    assert epsilon is not None
    seed_everything(seed)
    synth = MSTSynthesizer(epsilon=epsilon, delta=DELTA, **PARAMS)
    with accounting.observe("snsynth.mst.mst", "cdp_rho") as calls, Timer() as fit_t:
        synth.fit(
            train.reset_index(drop=True),
            transformer=transformer(domain, "cube"),
            preprocessor_eps=0.0,
        )
    seed_everything(seed + 1_000_003)
    with Timer() as sample_t:
        table = as_frame(synth.sample(n), domain)
    record = accounting.zcdp_record(calls, epsilon=epsilon, delta=DELTA, method="mst")
    record["epsilon_after_preprocessing"] = float(synth.epsilon)
    return Fitted(table, {"delta": DELTA, **PARAMS}, record, fit_t.seconds, sample_t.seconds, "cpu")


METHOD = Wrapped("mst", "smartnoise-synth", "dp marginal", _run)
