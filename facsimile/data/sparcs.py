"""New York SPARCS de-identified hospital inpatient discharges, 2024.

The health set (PLAN.md section 2.1), used because the New York State Department of Health's
Data Use Policy Statement, read and quoted in docs/data.md on 2026-10-16, places no controls on
end use and asks for attribution, the access date and a fixed disclaimer.

Fetched through the portal's SODA API with only the sixteen columns in the subset, in the
portal's own row order (`$order=:id`) so that the file, and its checksum, are the same on every
fetch until the state revises the data, which its page says it may: a revision is then a
checksum error, not a quiet change in a published number.

Both tasks predict from the fourteen attributes known at or near admission and leave out length
of stay and charges, so that neither task can read the other's answer.
"""

from __future__ import annotations

import csv
import io
import urllib.parse
import urllib.request
from typing import Final

import numpy as np
import pandas as pd

from facsimile.data import fetch, terms
from facsimile.data.base import ROW_ID, DatasetSpec, Task
from facsimile.data.split import Sizes
from facsimile.paths import RAW
from facsimile.prep import Categorical, Numeric

NAME: Final = "sparcs"
DATASET_ID: Final = "sf4k-39ay"
ENDPOINT: Final = f"https://health.data.ny.gov/resource/{DATASET_ID}.csv"
PAGE: Final = 500_000
CSV_PATH: Final = RAW / NAME / f"sparcs_inpatient_2024_{DATASET_ID}.csv"

FIELDS: Final = (
    "age_group", "gender", "race", "ethnicity", "zip_code", "health_service_area",
    "type_of_admission", "patient_disposition", "apr_mdc_code", "apr_severity_of_illness_code",
    "apr_risk_of_mortality", "apr_medical_surgical", "payment_typology_1",
    "emergency_department_indicator", "length_of_stay", "total_charges",
)  # fmt: skip

COLUMNS = (
    Categorical("age_group"),
    Categorical("gender"),
    Categorical("race"),
    Categorical("ethnicity"),
    # Three digits, blank where the state suppressed it (population under 20,000, a small cell,
    # or an abortion record). The quasi-identifier an attacker would reach for first.
    Categorical("zip_code", nullable=True),
    Categorical("health_service_area", nullable=True),
    Categorical("type_of_admission"),
    Categorical("patient_disposition"),
    Categorical("apr_mdc_code"),
    Categorical("apr_severity_of_illness_code"),
    Categorical("apr_risk_of_mortality", nullable=True),
    Categorical("apr_medical_surgical"),
    Categorical("payment_typology_1", nullable=True),
    Categorical("emergency_department_indicator"),
    # "120+" is the state's top code and is read as 120. Edge at 6 for the task: stay > 5 days.
    Numeric("length_of_stay", lo=1, hi=120, bins=10, edges=(1, 2, 3, 4, 5, 6, 8, 11, 15, 31, 120)),
    Numeric(
        "total_charges",
        lo=0,
        hi=10_000_000,
        bins=10,
        edges=(0, 5000, 10000, 20000, 30000, 50000, 75000, 100000, 200000, 500000, 10_000_000),
    ),
)

ADMISSION_FEATURES: Final = tuple(
    c.name for c in COLUMNS if c.name not in {"length_of_stay", "total_charges"}
)

TASKS = (
    Task(
        name="long_stay",
        target="length_of_stay",
        features=ADMISSION_FEATURES,
        at_least=6,
        note="length of stay above five days, from the fourteen non-outcome attributes",
    ),
    Task(
        name="high_charge",
        target="total_charges",
        features=ADMISSION_FEATURES,
        at_least=50000,
        note="total charges of US$50,000 or more, from the fourteen non-outcome attributes",
    ),
)


def _page_url(offset: int) -> str:
    query = {
        "$select": ",".join(FIELDS),
        "$order": ":id",
        "$limit": str(PAGE),
        "$offset": str(offset),
    }
    return f"{ENDPOINT}?{urllib.parse.urlencode(query)}"


def fetch_raw() -> None:
    terms.require(NAME)
    if not CSV_PATH.exists():
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CSV_PATH.with_suffix(".part")
        offset = 0
        with tmp.open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out, lineterminator="\n")
            while True:
                url = _page_url(offset)
                print(f"fetching rows {offset:,} onward")
                request = urllib.request.Request(url, headers={"User-Agent": fetch.USER_AGENT})
                with urllib.request.urlopen(request, timeout=900) as response:
                    rows = list(csv.reader(io.TextIOWrapper(response, encoding="utf-8")))
                header, body = rows[0], rows[1:]
                if offset == 0:
                    writer.writerow(header)
                writer.writerows(body)
                offset += len(body)
                if len(body) < PAGE:
                    break
        tmp.replace(CSV_PATH)
    fetch.verify_or_record(
        NAME, CSV_PATH, source=f"{ENDPOINT} ($select of {len(FIELDS)} fields, $order=:id)"
    )


def load_raw() -> pd.DataFrame:
    terms.require(NAME)
    fetch.verify(NAME, CSV_PATH)
    frame = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False, na_values=[""])
    frame["length_of_stay"] = pd.to_numeric(
        frame["length_of_stay"].str.replace(r"\s*\+$", "", regex=True)
    )
    frame["total_charges"] = pd.to_numeric(frame["total_charges"].str.replace(",", "", regex=False))
    frame[ROW_ID] = np.arange(len(frame), dtype=np.int64)
    return frame


SPEC = DatasetSpec(
    name=NAME,
    title="New York SPARCS de-identified inpatient discharges, 2024",
    columns=COLUMNS,
    tasks=TASKS,
    sizes=Sizes(train=20_000, control=2_000, test=10_000),
    split_seed=20261016,
    publish_ids=True,
    load_raw=load_raw,
    fetch=fetch_raw,
    notes=("row_id is the record's 0-based position in the fetched file ($order=:id)",),
)
