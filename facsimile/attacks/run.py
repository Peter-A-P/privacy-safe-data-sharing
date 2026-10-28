"""Attack one table of the grid: the three criteria, distance to closest record, and the reference.

Writes `results/<dataset>/attacks/<method>/<eps>/seed<k>.json`. Every attack uses the build's
targets and control, which are the same size, and the attack seed is fixed per table so a rerun
reproduces it exactly.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from facsimile import __version__
from facsimile.attacks.config import CONFIGS
from facsimile.attacks.dcr import dcr
from facsimile.attacks.inference import inference
from facsimile.attacks.linkability import linkability
from facsimile.attacks.singling_out import singling_out
from facsimile.data.build import Built, load_built
from facsimile.paths import results_dir
from facsimile.synth.base import hardware
from facsimile.synth.grid import Cell, load_table


def attack_path(cell: Cell) -> Path:
    return results_dir(cell.dataset) / "attacks" / cell.rel.with_suffix(".json")


def attack_table(
    built: Built,
    synthetic: pd.DataFrame,
    *,
    seed: int = 0,
    reference: bool = False,
    targets: pd.DataFrame | None = None,
    control: pd.DataFrame | None = None,
    dcr_too: bool = True,
) -> dict[str, Any]:
    """Every attack on one table. `targets` and `control` replace the build's own for an attack
    on a subset of them (`exposed.py`); singling out then makes no more attacks than there are
    targets."""
    cfg = CONFIGS[built.name]
    domain = built.domain
    targets = built.targets if targets is None else targets
    control = built.control if control is None else control
    n_attacks = min(cfg.n_attacks, len(targets))
    out: dict[str, Any] = {"attacks": {}, "timings": {}}

    def timed(name: str, fn: Any) -> Any:
        start = time.perf_counter()
        value = fn()
        out["timings"][name] = round(time.perf_counter() - start, 2)
        return value

    for mode in ("univariate", "multivariate"):
        res = timed(
            f"singling_out_{mode}",
            lambda mode=mode: singling_out(
                targets,
                control,
                synthetic,
                domain,
                mode=mode,
                n_attacks=n_attacks,
                n_cols=cfg.n_cols,
                seed=seed,
            ),
        )
        out["attacks"][res.attack] = res.as_dict()
    for k in cfg.k_values:
        res = timed(
            f"linkability_k{k}",
            lambda k=k: linkability(
                targets, control, synthetic, domain, a=cfg.half_a, b=cfg.half_b, k=k, seed=seed
            ),
        )
        out["attacks"][f"linkability_k{k}"] = res.as_dict()
    res = timed(
        "inference",
        lambda: inference(targets, control, synthetic, domain, secret=cfg.secret, seed=seed),
    )
    out["attacks"]["inference"] = res.as_dict()
    if dcr_too:
        out["dcr"] = timed("dcr", lambda: dcr(targets, control, synthetic, domain, seed=seed))
    if reference:
        from facsimile.attacks.reference import anonymeter_all

        out["reference"] = {
            "anonymeter": timed(
                "anonymeter",
                lambda: anonymeter_all(targets, control, synthetic, domain, cfg, seed=seed),
            )
        }
    return out


def run_attacks(cell: Cell, *, reference: bool = False, force: bool = False) -> dict[str, Any]:
    path = attack_path(cell)
    if path.exists() and not force:
        existing: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        if not reference or "reference" in existing:
            return existing
        return add_reference(cell, existing)
    built = load_built(cell.dataset)
    record = json.loads(cell.record_path.read_text(encoding="utf-8"))
    table = load_table(cell)
    payload = {
        "facsimile": __version__,
        "dataset": cell.dataset,
        "method": cell.method,
        "epsilon": cell.epsilon,
        "seed": cell.seed,
        "table_sha256": record["table_sha256"],
        **attack_table(built, table, seed=cell.seed, reference=reference),
        "hardware": hardware(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")
    return payload


def add_reference(cell: Cell, existing: dict[str, Any]) -> dict[str, Any]:
    """Run only Anonymeter on a table already attacked, on the same inputs, and add it to the
    record. The project's own attacks are seeded, so rerunning them would reproduce the same
    numbers; this saves the time."""
    from facsimile.attacks.reference import anonymeter_all

    built = load_built(cell.dataset)
    record = json.loads(cell.record_path.read_text(encoding="utf-8"))
    if record["table_sha256"] != existing["table_sha256"]:
        raise ValueError(f"{cell.rel}: the table changed since it was attacked")
    table = load_table(cell)
    start = time.perf_counter()
    existing["reference"] = {
        "anonymeter": anonymeter_all(
            built.targets, built.control, table, built.domain, CONFIGS[built.name], seed=cell.seed
        )
    }
    existing.setdefault("timings", {})["anonymeter"] = round(time.perf_counter() - start, 2)
    existing["reference_hardware"] = hardware()
    path = attack_path(cell)
    path.write_text(json.dumps(existing, indent=2, default=float) + "\n", encoding="utf-8")
    return existing
