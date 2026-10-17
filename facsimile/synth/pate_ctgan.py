"""PATE-CTGAN (SmartNoise): the deep DP arm the 2025 benchmark expects to lose (Rule C candidate 2).

Library defaults, run as shipped. Three properties of smartnoise-synth 1.0.8's implementation,
read from its source on 2026-10-16, checked against the grid on 2026-10-17, and recorded rather
than patched, because the project measures what the library does (docs/synthesisers.md):

1. The moments accountant is written to depend on the teachers' votes, but at the default
   noise_multiplier of 1e-3 its clamp always binds, so every increment is the same and the
   epsilon spent depends only on the number of student steps.
2. The training loop compares the budget with the target before each iteration, so the last
   iteration carries the total past the target (37.7% over at epsilon 0.5, measured).
   `accounting.pate_record` reports what the finished model consumed (`epsilon_spent`).
3. `Discriminator.__init__` calls `torch.manual_seed(0)` each time a teacher or the student is
   built; the three seeds still give three different tables, because sampling is reseeded here.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth import accounting
from facsimile.synth.base import DELTA, Fitted, Timer, Wrapped, device, seed_everything
from facsimile.synth.smartnoise_common import as_frame, transformer

MOMENTS_ORDER = 100
PARAMS: dict[str, Any] = {"moments_order": MOMENTS_ORDER, "verbose": False}


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    from snsynth.pytorch.nn.patectgan import PATECTGAN

    assert epsilon is not None
    seed_everything(seed)
    dev = device()
    synth = PATECTGAN(epsilon=epsilon, delta=DELTA, cuda=dev == "cuda", **PARAMS)
    with (
        accounting.observe("snsynth.pytorch.nn.patectgan", "moments_acc") as calls,
        Timer() as fit_t,
    ):
        synth.fit(
            train.reset_index(drop=True),
            transformer=transformer(domain, "gan"),
            preprocessor_eps=0.0,
        )
    seed_everything(seed + 1_000_003)
    with Timer() as sample_t:
        table = as_frame(synth.sample(n), domain)
    record = accounting.pate_record(
        calls, epsilon=epsilon, delta=DELTA, moments_order=MOMENTS_ORDER
    )
    return Fitted(
        table,
        {"delta": DELTA, "cuda": dev == "cuda", **PARAMS},
        record,
        fit_t.seconds,
        sample_t.seconds,
        dev,
    )


METHOD = Wrapped("pate_ctgan", "smartnoise-synth", "dp deep", _run)
