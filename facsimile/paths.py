"""Where things live on disk.

Two kinds of output, kept apart because one may be committed and the other may not:

- `data/` holds anything with a row in it: raw downloads, the built splits, every synthetic
  table. Gitignored in full (`tests/test_data_terms.py` asks git itself).
- `results/` holds what is published: domains, split manifests, run records, measurements.
  No row of any table, real or synthetic, is ever written there.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

REPO: Final = Path(__file__).resolve().parent.parent

DATA: Final = Path(os.environ.get("FACSIMILE_DATA", REPO / "data"))
RAW: Final = DATA / "raw"
BUILD: Final = DATA / "build"
SYNTH: Final = DATA / "synth"

RESULTS: Final = REPO / "results"
DOCS: Final = REPO / "docs"

IEEE_CIS_DIR: Final = Path(os.environ.get("FACSIMILE_IEEE_CIS_DIR", RAW / "ieee-fraud-detection"))
"""The IEEE-CIS competition files, downloaded by the account holder (docs/data.md).

Nothing in this project downloads them. On the build desktop they are the copy project 09
verified on 2026-09-12; point this variable at that folder rather than copying the data again.
"""


def build_dir(dataset: str) -> Path:
    return BUILD / dataset


def synth_dir(dataset: str) -> Path:
    return SYNTH / dataset


def results_dir(dataset: str) -> Path:
    return RESULTS / dataset
