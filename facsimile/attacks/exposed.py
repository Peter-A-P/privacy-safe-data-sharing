"""The attacks on the most exposed records (PLAN.md section 2.10).

Unusual people leak first: a record with no near neighbours in the population is the one a
synthetic table can only reproduce by remembering it (Stadler et al. 2022 make the same point for
membership inference). The grid's attacks use 2,000 targets drawn at random, so most of them are
ordinary. Here the same attacks run again on the same table, on the quarter of the targets that
are most unusual against the quarter of the control records that are most unusual, measured the
same way, so that the control is still the like-for-like comparison.

How unusual a record is: its mean mixed-type distance to a fixed sample of 2,000 test-split
records. The test split stands in for public knowledge of the population, as it does for the
domain, and no synthesiser sees it. Writes `results/<dataset>/attacks_exposed/<method>/<eps>/
seed<k>.json`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd

from facsimile import __version__
from facsimile.attacks.neighbours import distances
from facsimile.attacks.run import attack_table
from facsimile.data.build import Built, load_built
from facsimile.paths import results_dir
from facsimile.synth.base import hardware
from facsimile.synth.grid import Cell, load_table

SHARE: Final = 0.25
REFERENCE_ROWS: Final = 2000
SEED: Final = 20261027


def rarity(records: pd.DataFrame, reference: pd.DataFrame, built: Built) -> np.ndarray:
    """Mean distance from each record to the reference sample: higher is more unusual."""
    names = built.domain.names
    out: np.ndarray = distances(records[names], reference[names], built.domain, names).mean(axis=1)
    return out


def exposed(built: Built) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The most unusual quarter of the targets and, ranked the same way, of the control."""
    rng = np.random.default_rng(SEED)
    reference = built.test.iloc[rng.choice(len(built.test), REFERENCE_ROWS, replace=False)]
    n = int(len(built.targets) * SHARE)

    def top(frame: pd.DataFrame) -> pd.DataFrame:
        order = np.argsort(-rarity(frame, reference, built), kind="stable")
        return frame.iloc[order[:n]]

    return top(built.targets), top(built.control)


def exposed_path(cell: Cell) -> Path:
    return results_dir(cell.dataset) / "attacks_exposed" / cell.rel.with_suffix(".json")


def run_exposed(cell: Cell, *, force: bool = False) -> dict[str, Any]:
    path = exposed_path(cell)
    if path.exists() and not force:
        existing: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return existing
    built = load_built(cell.dataset)
    targets, control = exposed(built)
    record = json.loads(cell.record_path.read_text(encoding="utf-8"))
    start = time.perf_counter()
    payload = {
        "facsimile": __version__,
        "dataset": cell.dataset,
        "method": cell.method,
        "epsilon": cell.epsilon,
        "seed": cell.seed,
        "table_sha256": record["table_sha256"],
        "subset": {
            "share": SHARE,
            "targets": len(targets),
            "control": len(control),
            "ranked_by": f"mean mixed-type distance to {REFERENCE_ROWS} test-split records",
        },
        **attack_table(
            built, load_table(cell), seed=cell.seed, targets=targets, control=control, dcr_too=False
        ),
        "seconds": round(time.perf_counter() - start, 1),
        "hardware": hardware(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")
    return payload
