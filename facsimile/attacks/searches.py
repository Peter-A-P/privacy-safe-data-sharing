"""Singling out averaged over five searches, written into the attack records already on disk
(PLAN.md section 2.12).

The other attacks are seeded and need nothing from the search, so only the two singling-out
entries of each record are replaced, on the same table, targets and control. The first search
uses the table's own seed, which is the run already published, and must reproduce its counts
exactly or the update stops: that is the check that nothing else changed underneath. With
`reference`, Anonymeter runs on the grid tables too, all its attacks, so every record carries its
counts for the report to pool. Resumable: a record already averaged is left alone.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from facsimile.attacks.config import CONFIGS
from facsimile.attacks.exposed import exposed, exposed_path
from facsimile.attacks.reference import anonymeter_all
from facsimile.attacks.run import attack_path
from facsimile.attacks.singling_out import SEARCHES, Mode, singling_out
from facsimile.data.build import load_built
from facsimile.synth import GRID
from facsimile.synth.base import hardware
from facsimile.synth.grid import Cell, load_table

MODES: tuple[Mode, ...] = ("univariate", "multivariate")


def _averaged(entry: dict[str, Any]) -> bool:
    return len(entry.get("params", {}).get("searches", {}).get("seeds", [])) == SEARCHES


def _reference_done(record: dict[str, Any]) -> bool:
    ref = record.get("reference", {}).get("anonymeter")
    if not ref or not all("counts" in v for v in ref.values()):
        return False
    return all(
        len(ref[f"singling_out_{m}"].get("searches", {}).get("seeds", [])) == SEARCHES
        for m in MODES
    )


def _write(path: Path, record: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(json.dumps(record, indent=2, default=float) + "\n", encoding="utf-8")
    tmp.replace(path)


def search_again(
    cell: Cell, *, exposed_records: bool = False, reference: bool = False
) -> dict[str, Any] | None:
    """Replace a record's singling-out entries with the five-search average; None if the table has
    not been attacked."""
    path = exposed_path(cell) if exposed_records else attack_path(cell)
    if not path.exists():
        return None
    record: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    want_reference = reference and not exposed_records and cell.method in GRID
    todo = [m for m in MODES if not _averaged(record["attacks"][f"singling_out_{m}"])]
    if not todo and (not want_reference or _reference_done(record)):
        return record
    synth = json.loads(cell.record_path.read_text(encoding="utf-8"))
    if synth["table_sha256"] != record["table_sha256"]:
        raise ValueError(f"{cell.rel}: the table changed since it was attacked")
    built = load_built(cell.dataset)
    targets: pd.DataFrame
    control: pd.DataFrame
    targets, control = exposed(built) if exposed_records else (built.targets, built.control)
    cfg = CONFIGS[built.name]
    table = load_table(cell)
    for mode in todo:
        key = f"singling_out_{mode}"
        old = record["attacks"][key]
        start = time.perf_counter()
        res = singling_out(
            targets,
            control,
            table,
            built.domain,
            mode=mode,
            n_attacks=min(cfg.n_attacks, len(targets)),
            n_cols=cfg.n_cols,
            seed=cell.seed,
        )
        first = res.params["searches"]
        published = (
            old["main"]["successes"],
            old["control"]["successes"],
            old["baseline"]["successes"],
        )
        if (first["main"][0], first["control"][0], first["baseline"][0]) != published:
            raise ValueError(
                f"{cell.rel} {key}: the first search gives {first['main'][0]}, "
                f"{first['control'][0]}, {first['baseline'][0]}, not the published {published}"
            )
        record["attacks"][key] = res.as_dict()
        record.setdefault("timings", {})[key] = round(time.perf_counter() - start, 2)
        _write(path, record)
    if want_reference and not _reference_done(record):
        start = time.perf_counter()
        record["reference"] = {
            "anonymeter": anonymeter_all(targets, control, table, built.domain, cfg, seed=cell.seed)
        }
        record.setdefault("timings", {})["anonymeter"] = round(time.perf_counter() - start, 2)
        record["reference_hardware"] = hardware()
        _write(path, record)
    return record
