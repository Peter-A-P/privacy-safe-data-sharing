"""What the three SmartNoise methods share: a transformer fitted to the domain, not to the data.

SmartNoise's default, given `categorical_columns`, fits a label transformer to the training
data it is handed, which reads the set of categories off the people the guarantee protects and
charges no epsilon for it. Here the transformer is fitted to a frame that contains every code of
every column and nothing else, so it is complete before it sees a record and the library never
fits it (`snsynth.base.Synthesizer._get_train_data` skips fitting a complete transformer).
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

from facsimile.prep import Domain


def domain_frame(domain: Domain) -> pd.DataFrame:
    """Every code of every column at least once, padded by repeating; no record in it."""
    width = max(c.size for c in domain.columns)
    return pd.DataFrame({c.name: np.resize(np.arange(c.size), width) for c in domain.columns})


def transformer(domain: Domain, style: Literal["cube", "gan"]) -> Any:
    from snsynth.transform import (
        ChainTransformer,
        LabelTransformer,
        OneHotEncoder,
        TableTransformer,
    )

    if style == "cube":
        parts = [LabelTransformer(nullable=False) for _ in domain.columns]
    else:
        parts = [
            ChainTransformer([LabelTransformer(nullable=False), OneHotEncoder()])
            for _ in domain.columns
        ]
    tt = TableTransformer(parts)
    tt.fit(domain_frame(domain))
    if not tt.fit_complete:
        raise AssertionError("the domain transformer did not complete its fit")
    if style == "cube" and list(tt.cardinality) != [c.size for c in domain.columns]:
        raise AssertionError(f"transformer cardinality {tt.cardinality} is not the domain's")
    return tt


def as_frame(samples: Any, domain: Domain) -> pd.DataFrame:
    if isinstance(samples, pd.DataFrame):
        frame = samples.copy()
        frame.columns = domain.names
        return frame
    return pd.DataFrame(np.asarray(list(samples)), columns=domain.names)
