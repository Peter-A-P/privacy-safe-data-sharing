"""TabDDPM (synthcity): the diffusion model, the seventh synthesiser (PLAN.md section 2.11).

Prepared, not yet in the registry: it joins `methods()` and `GRID` after the timing spike, in the
commit that adds it to the report, the Groundhog budgets and the queue's timings.

synthcity cannot be installed on Python 3.13, so it runs in its own environment
(`envs/synthcity-requirements.txt`) and this wrapper calls `envs/synthcity_tabddpm.py` there in a
subprocess, as the TAPAS cross-check does. The training codes go to it as a parquet file in a
temporary directory and the table and a record come back; nothing is written under `data/` or
`results/` here, the grid does that as for every other method.

synthcity's defaults are used, as for every other arm. One of them changes what the method sees:
a column with more than 10 distinct values is diffused as a number, not as a category, and comes
back as a float. `to_codes` rounds it to the nearest code and clips it into the column's range,
and the record says how many values the clipping moved. That is the project's post-processing,
not the library's, and is the least that puts the table back in the domain.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from facsimile.paths import REPO
from facsimile.prep import CODE_DTYPE, Domain
from facsimile.synth.base import Fitted, Wrapped

SCRIPT: Final = REPO / "envs" / "synthcity_tabddpm.py"


def python_path() -> Path:
    """The synthcity environment's interpreter: `FACSIMILE_SYNTHCITY_PYTHON`, or `.venv-synthcity`."""
    if env := os.environ.get("FACSIMILE_SYNTHCITY_PYTHON"):
        return Path(env)
    venv = REPO / ".venv-synthcity"
    return venv / "Scripts" / "python.exe" if sys.platform == "win32" else venv / "bin" / "python"


def to_codes(raw: pd.DataFrame, domain: Domain) -> tuple[pd.DataFrame, dict[str, int]]:
    """The library's output as codes in the domain, and per column how many values were clipped."""
    missing = [c for c in domain.names if c not in raw.columns]
    if missing:
        raise ValueError(f"synthcity returned no column {missing}")
    out: dict[str, np.ndarray[Any, Any]] = {}
    clipped: dict[str, int] = {}
    for col in domain.columns:
        values = pd.to_numeric(raw[col.name]).to_numpy(dtype=float)
        if np.isnan(values).any():
            raise ValueError(f"{col.name}: synthcity returned missing values")
        rounded = np.rint(values)
        codes = np.clip(rounded, 0, col.size - 1)
        clipped[col.name] = int((codes != rounded).sum())
        out[col.name] = codes.astype(CODE_DTYPE)
    return pd.DataFrame(out, columns=domain.names), clipped


def _run(train: pd.DataFrame, domain: Domain, seed: int, epsilon: float | None, n: int) -> Fitted:
    python = python_path()
    if not python.exists():
        raise FileNotFoundError(
            f"no synthcity environment at {python}; create it as envs/synthcity-requirements.txt "
            "says, or set FACSIMILE_SYNTHCITY_PYTHON"
        )
    with tempfile.TemporaryDirectory(prefix="facsimile-tabddpm-") as tmp:
        work = Path(tmp)
        train.reset_index(drop=True).to_parquet(work / "train.parquet", index=False)
        done = subprocess.run(
            [str(python), str(SCRIPT), str(work / "train.parquet"), str(work), str(seed), str(n)],
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode != 0:
            raise RuntimeError(f"synthcity TabDDPM failed:\n{done.stderr[-4000:]}")
        record = json.loads((work / "record.json").read_text(encoding="utf-8"))
        raw = pd.read_parquet(work / "table.parquet")
    table, clipped = to_codes(raw, domain)
    numeric = [c for c in domain.names if c not in record["discrete_columns"]]
    return Fitted(
        table=table,
        params={
            "library_version": record["library_version"],
            "torch": record["torch"],
            "python": record["python"],
            **record["params"],
        },
        accounting={"dp": False, "epsilon": "inf"},
        fit_seconds=record["fit_seconds"],
        sample_seconds=record["sample_seconds"],
        device=record["device"],
        notes=[
            f"diffused as numbers (more than 10 values in training): {', '.join(numeric) or 'none'}",
            f"values clipped into the domain: {sum(clipped.values())} ({clipped})",
        ],
    )


METHOD = Wrapped("tabddpm", "synthcity", "non-dp deep", _run)
