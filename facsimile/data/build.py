"""Build a dataset: load, split, fit the domain on the test split, encode, write, check.

Rows go to `data/build/<dataset>/` (gitignored). What is published goes to `results/<dataset>/`:
the domain, the split manifest and the datasheet, none of which holds a row.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from facsimile.data.base import ROW_ID, DatasetSpec
from facsimile.data.datasheet import write_datasheet
from facsimile.data.split import Split, check_split, frame_hash, make_split
from facsimile.paths import build_dir, results_dir
from facsimile.prep import Domain, check_codes, encode, fit_domain

PARTS = ("train", "control", "test", "targets")


@dataclass(frozen=True, slots=True)
class Built:
    """A built dataset, read back from disk: coded frames indexed by row id, and the domain."""

    name: str
    domain: Domain
    train: pd.DataFrame
    control: pd.DataFrame
    test: pd.DataFrame
    targets: pd.DataFrame
    manifest: dict[str, Any]

    @property
    def train_hash(self) -> str:
        return str(self.manifest["train_frame_sha256"])


def build(spec: DatasetSpec) -> Built:
    raw = spec.load_raw()
    missing = [c for c in spec.column_names if c not in raw.columns]
    if missing:
        raise KeyError(f"{spec.name}: the raw loader did not return {missing}")
    raw = raw.set_index(ROW_ID)[spec.column_names]
    split = make_split(raw.index.to_numpy(), spec.sizes, spec.split_seed)

    domain = fit_domain(spec.columns, raw.loc[split.test])
    parts = {name: encode(raw.loc[getattr(split, name)], domain) for name in PARTS}
    for frame in parts.values():
        check_codes(frame, domain)

    out = build_dir(spec.name)
    out.mkdir(parents=True, exist_ok=True)
    for name, frame in parts.items():
        frame.to_parquet(out / f"{name}.parquet")

    manifest: dict[str, Any] = {
        "dataset": spec.name,
        "population_rows": len(raw),
        "split": split.manifest(publish_ids=spec.publish_ids),
        "train_frame_sha256": frame_hash(parts["train"]),
        "domain_cells": domain.cells(),
    }
    published = results_dir(spec.name)
    domain.write(published / "domain.json")
    _write_json(published / "split.json", manifest)
    _write_json(out / "manifest.json", manifest)
    write_datasheet(spec, domain, parts, manifest, published / "datasheet.md")
    return load_built(spec.name)


def load_built(name: str) -> Built:
    out = build_dir(name)
    if not (out / "manifest.json").exists():
        raise FileNotFoundError(f"{name} is not built; run `facsimile build {name}`")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    domain = Domain.read(results_dir(name) / "domain.json")
    frames = {part: pd.read_parquet(out / f"{part}.parquet") for part in PARTS}
    built = Built(name=name, domain=domain, manifest=manifest, **frames)
    check_built(built)
    return built


def check_built(built: Built) -> None:
    """The leakage check, on every read of a build: disjoint, targets in train, hash matches."""
    split = Split(
        train=built.train.index.to_numpy(),
        control=built.control.index.to_numpy(),
        test=built.test.index.to_numpy(),
        targets=built.targets.index.to_numpy(),
        seed=int(built.manifest["split"]["seed"]),
    )
    check_split(split)
    if frame_hash(built.train) != built.train_hash:
        raise AssertionError(f"{built.name}: train on disk does not match the manifest's hash")
    for frame in (built.train, built.control, built.test, built.targets):
        check_codes(frame, built.domain)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
