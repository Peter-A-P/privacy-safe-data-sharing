"""ACS PUMS, California 2018 one-year person file, with folktables' task definitions.

The standard benchmark of the differential-privacy literature (PLAN.md section 2.1). The file is
fetched from the Census Bureau directly rather than through `folktables`' downloader, because
that downloader deletes the archive after extracting it and so leaves nothing to checksum; the
task definitions (features, filters, targets) are folktables' own, read from its source.

**One table, two tasks.** ACSIncome and ACSEmployment are defined on different populations. The
synthesiser grid is fitted once per dataset, so this project uses the employment population
(age 17 to 89, `employment_filter`) as the table and applies ACSIncome's own filter (income above
100, hours worked present) as the income task's population, in the coded domain. The income task
is then ACSIncome exactly, except that the 90-and-over are absent. The employment task uses the
ten ACSEmployment features in the subset; the six it leaves out (ESP, MIG, ANC, DEAR, DEYE, DREM)
are dropped to keep AIM tractable, so its numbers sit beside published ones loosely, not exactly.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from facsimile.data import fetch, terms
from facsimile.data.base import ROW_ID, Condition, DatasetSpec, Task
from facsimile.data.split import Sizes
from facsimile.paths import RAW
from facsimile.prep import Categorical, Numeric

NAME: Final = "acs"
YEAR: Final = "2018"
STATE: Final = "ca"
URL: Final = (
    f"https://www2.census.gov/programs-surveys/acs/data/pums/{YEAR}/1-Year/csv_p{STATE}.zip"
)
ARCHIVE: Final = RAW / NAME / f"csv_p{STATE}_{YEAR}.zip"
MEMBER: Final = "psam_p06.csv"

RAW_COLUMNS: Final = (
    "AGEP", "COW", "SCHL", "MAR", "OCCP", "POBP", "RELP", "WKHP", "SEX", "RAC1P",
    "DIS", "CIT", "MIL", "NATIVITY", "PINCP", "ESR", "PWGTP",
)  # fmt: skip

INCOME_FEATURES: Final = (
    "AGEP",
    "COW",
    "SCHL",
    "MAR",
    "OCCP",
    "POBP",
    "RELP",
    "WKHP",
    "SEX",
    "RAC1P",
)
EMPLOYMENT_FEATURES: Final = (
    "AGEP",
    "SCHL",
    "MAR",
    "RELP",
    "DIS",
    "CIT",
    "MIL",
    "NATIVITY",
    "SEX",
    "RAC1P",
)

# Closed codebooks are from the ACS 2018 PUMS data dictionary; the others take their category
# sets from the test split (prep.py).
COLUMNS = (
    Numeric("AGEP", lo=17, hi=89, bins=8),
    Categorical("COW", values=tuple(str(i) for i in range(1, 10)), nullable=True),
    Categorical("SCHL", nullable=True),
    Categorical("MAR", values=("1", "2", "3", "4", "5")),
    Categorical("OCCP", nullable=True),
    Categorical("POBP"),
    Categorical("RELP"),
    # 40 hours is a spike in the distribution and gets its own bin.
    Numeric("WKHP", lo=1, hi=99, bins=7, nullable=True, edges=(1, 20, 30, 40, 41, 50, 60, 99)),
    Categorical("SEX", values=("1", "2")),
    Categorical("RAC1P", values=tuple(str(i) for i in range(1, 10))),
    Categorical("DIS", values=("1", "2")),
    Categorical("CIT", values=("1", "2", "3", "4", "5")),
    Categorical("MIL", values=("1", "2", "3", "4"), nullable=True),
    Categorical("NATIVITY", values=("1", "2")),
    # Edges at 101 and 50,001 because ACSIncome's filter is PINCP > 100 and its target is
    # PINCP > 50,000 on integer dollars: both are bin boundaries, not guesses inside a bin.
    Numeric(
        "PINCP",
        lo=-20000,
        hi=1_500_000,
        bins=10,
        edges=(-20000, 101, 10000, 20000, 30000, 40000, 50001, 75000, 100000, 150000, 1_500_000),
    ),
    Categorical("ESR", values=tuple(str(i) for i in range(1, 7)), nullable=True),
)

TASKS = (
    Task(
        name="income",
        target="PINCP",
        features=INCOME_FEATURES,
        at_least=50001,
        where=(Condition("PINCP", at_least=101), Condition("WKHP", present=True)),
        note="ACSIncome: PINCP > 50,000 among adults with income above 100 and hours worked",
    ),
    Task(
        name="employment",
        target="ESR",
        features=EMPLOYMENT_FEATURES,
        positive_labels=("1",),
        note="ACSEmployment: ESR == 1 (civilian employed, at work), ten of its sixteen features",
    ),
)


def fetch_raw() -> None:
    terms.require(NAME)
    if not ARCHIVE.exists():
        print(f"fetching {URL}")
        fetch.download(URL, ARCHIVE)
    fetch.verify_or_record(NAME, ARCHIVE, source=URL)


def load_raw() -> pd.DataFrame:
    terms.require(NAME)
    if not ARCHIVE.exists():
        raise FileNotFoundError(f"{ARCHIVE} is missing; run `facsimile data fetch {NAME}`")
    fetch.verify(NAME, ARCHIVE)
    with zipfile.ZipFile(ARCHIVE) as zf, zf.open(MEMBER) as f:
        frame = pd.read_csv(f, usecols=list(RAW_COLUMNS), dtype=float)
    frame[ROW_ID] = np.arange(len(frame), dtype=np.int64)
    # folktables.employment_filter, verbatim in effect: AGEP > 16, AGEP < 90, PWGTP >= 1.
    frame = frame[(frame["AGEP"] > 16) & (frame["AGEP"] < 90) & (frame["PWGTP"] >= 1)]
    return frame.drop(columns=["PWGTP"]).reset_index(drop=True)


SPEC = DatasetSpec(
    name=NAME,
    title="ACS PUMS, California 2018, one-year person file",
    columns=COLUMNS,
    tasks=TASKS,
    sizes=Sizes(train=20_000, control=2_000, test=10_000),
    split_seed=20261016,
    publish_ids=True,
    load_raw=load_raw,
    fetch=fetch_raw,
    notes=(
        "row_id is the record's 0-based position in psam_p06.csv inside the checksummed archive",
    ),
)


def archive_path() -> Path:
    return ARCHIVE
