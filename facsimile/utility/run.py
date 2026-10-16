"""Score one table of the grid for usefulness: TSTR per task and marginal query error.

Writes `results/<dataset>/utility/<method>/<eps>/seed<k>.json`. The real-data ceiling is the same
model on the real training split, fitted once per dataset and process and reused.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from facsimile import __version__, data
from facsimile.data.build import load_built
from facsimile.paths import results_dir
from facsimile.synth.grid import Cell, load_table
from facsimile.utility.queries import marginal_error
from facsimile.utility.tstr import PARAMS, Scored, tstr

_CEILINGS: dict[str, dict[str, Scored]] = {}


def utility_path(cell: Cell) -> Path:
    return results_dir(cell.dataset) / "utility" / cell.rel.with_suffix(".json")


def run_utility(cell: Cell, *, force: bool = False) -> dict[str, Any]:
    path = utility_path(cell)
    if path.exists() and not force:
        existing: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return existing
    built = load_built(cell.dataset)
    spec = data.get(cell.dataset)
    record = json.loads(cell.record_path.read_text(encoding="utf-8"))
    table = load_table(cell)
    cache = _CEILINGS.setdefault(cell.dataset, {})
    payload = {
        "facsimile": __version__,
        "dataset": cell.dataset,
        "method": cell.method,
        "epsilon": cell.epsilon,
        "seed": cell.seed,
        "table_sha256": record["table_sha256"],
        "model": {"library": "lightgbm", "params": PARAMS, "seed": 0},
        "tasks": tstr(
            table, built.train, built.test, spec.tasks, built.domain, seed=0, ceiling_cache=cache
        ),
        "marginal_error": marginal_error(table, built.train, built.domain, seed=0),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
