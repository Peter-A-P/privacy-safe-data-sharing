"""IEEE-CIS Fraud Detection: the card-transaction set, under the terms project 09 recorded.

Reused from 09 as written (PLAN.md section 5): the competition rules read and quoted on
2026-09-12 (docs/data.md quotes them again), the checksums of the files as downloaded, and the
posture they imply. Nothing here downloads anything. The account holder downloads the archive;
on the build desktop this loader reads 09's verified copy through `FACSIMILE_IEEE_CIS_DIR`.

What 09's terms reading binds here, beyond "nothing raw is committed":

- **No row-level output is published**, and a synthetic table fitted to this data is row-level
  output derived from it, so the grid stays under `data/` like the raw files.
- **Split ids are not published.** A list of TransactionIDs is a row-level reference into the
  Competition Data; the split manifest carries counts and hashes, and the split is reproducible
  exactly from the files and the seed.

Attribute subset: fifteen predictors and the label, raw columns only (no engineered features),
chosen to cover the amount, the product, the card's issuer descriptors, the billing region, the
email domains, two counters, a day offset, two match flags, the device type and the hour.
`card1` (an issuer identifier with thousands of values) is left out; `addr1` (a billing region)
is in, rare values merged, because it is the quasi-identifier an attacker would reach for.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from facsimile.data import fetch, terms
from facsimile.data.base import ROW_ID, DatasetSpec, Task
from facsimile.data.split import Sizes
from facsimile.paths import IEEE_CIS_DIR
from facsimile.prep import Categorical, Numeric

NAME: Final = "ieeecis"
TRANSACTIONS: Final = "train_transaction.csv"
IDENTITY: Final = "train_identity.csv"

TRANSACTION_COLUMNS: Final = (
    "TransactionID", "isFraud", "TransactionDT", "TransactionAmt", "ProductCD", "card4", "card6",
    "addr1", "addr2", "dist1", "P_emaildomain", "R_emaildomain", "C1", "C2", "D1", "M4", "M6",
)  # fmt: skip

COLUMNS = (
    Numeric("TransactionAmt", lo=0, hi=32000, bins=12, scale="log"),
    Categorical("ProductCD"),
    Categorical("card4", nullable=True),
    Categorical("card6", nullable=True),
    Categorical("addr1", nullable=True),
    Categorical("addr2", nullable=True),
    Numeric("dist1", lo=0, hi=10000, bins=8, scale="log", nullable=True),
    Categorical("P_emaildomain", nullable=True),
    Categorical("R_emaildomain", nullable=True),
    Numeric("C1", lo=0, hi=5000, bins=8, scale="log"),
    Numeric("C2", lo=0, hi=5000, bins=8, scale="log"),
    Numeric("D1", lo=0, hi=640, bins=8, nullable=True),
    Categorical("M4", nullable=True),
    Categorical("M6", nullable=True),
    Categorical("DeviceType", nullable=True),
    Numeric("hour", lo=0, hi=24, bins=8),
    Categorical("isFraud", values=("0", "1")),
)

FEATURES: Final = tuple(c.name for c in COLUMNS if c.name != "isFraud")

TASKS = (
    Task(
        name="fraud",
        target="isFraud",
        features=FEATURES,
        positive_labels=("1",),
        note="fraud classification on all fifteen predictors",
    ),
)


def _path(name: str) -> Path:
    return IEEE_CIS_DIR / name


def fetch_raw() -> None:
    """Verify the account holder's download; this project never downloads competition data."""
    terms.require(NAME)
    for name in (TRANSACTIONS, IDENTITY):
        path = _path(name)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} is missing. Download the archive from the competition's Data tab "
                "(docs/data.md) and point FACSIMILE_IEEE_CIS_DIR at the extracted folder."
            )
        fetch.verify_or_record(
            NAME, path, source="https://www.kaggle.com/competitions/ieee-fraud-detection/data"
        )


def load_raw() -> pd.DataFrame:
    terms.require(NAME)
    for name in (TRANSACTIONS, IDENTITY):
        fetch.verify(NAME, _path(name))
    tx = pd.read_csv(_path(TRANSACTIONS), usecols=list(TRANSACTION_COLUMNS))
    ident = pd.read_csv(_path(IDENTITY), usecols=["TransactionID", "DeviceType"])
    frame = tx.merge(ident, on="TransactionID", how="left", validate="one_to_one")
    # TransactionDT is an offset in whole seconds from an unstated reference (09, docs/data.md);
    # the hour of day is the only clock this table keeps, and it is relative to that reference.
    frame["hour"] = (frame["TransactionDT"] // 3600) % 24
    frame[ROW_ID] = frame["TransactionID"].astype(np.int64)
    return frame.drop(columns=["TransactionID", "TransactionDT"]).reset_index(drop=True)


SPEC = DatasetSpec(
    name=NAME,
    title="IEEE-CIS Fraud Detection, training transactions",
    columns=COLUMNS,
    tasks=TASKS,
    sizes=Sizes(train=20_000, control=2_000, test=10_000),
    split_seed=20261016,
    publish_ids=False,
    load_raw=load_raw,
    fetch=fetch_raw,
    notes=("row_id is TransactionID; never published (competition rules 7.B)",),
)
