"""What the three SDV methods share: metadata that says every column is categorical.

Every column arrives as integer codes, and SDV would otherwise detect them as numbers and fit a
continuous distribution to a category index. Declaring them categorical keeps SDV inside the
domain, so that a copula, a GAN and a VAE are compared on the same footing as AIM and MST.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd

from facsimile.prep import Domain
from facsimile.synth.base import Fitted, Timer, device, seed_everything

TABLE = "t"


def metadata(domain: Domain) -> Any:
    from sdv.metadata import Metadata

    md = Metadata()
    md.add_table(TABLE)
    for name in domain.names:
        md.add_column(name, table_name=TABLE, sdtype="categorical")
    return md


def fit_sample(
    make: Callable[[Any], Any],
    params: dict[str, Any],
    train: pd.DataFrame,
    domain: Domain,
    seed: int,
    n: int,
) -> Fitted:
    import sdv

    seed_everything(seed)
    synth = make(metadata(domain))
    with Timer() as fit_t:
        synth.fit({TABLE: train.reset_index(drop=True)})
    seed_everything(seed + 1_000_003)
    with Timer() as sample_t:
        out = synth.sample(num_rows=n)
    table = out[TABLE] if isinstance(out, dict) else out
    return Fitted(
        table=table,
        params={"library_version": sdv.__version__, **params},
        accounting={"dp": False, "epsilon": "inf"},
        fit_seconds=fit_t.seconds,
        sample_seconds=sample_t.seconds,
        device=device() if params.get("enable_gpu") else "cpu",
    )
