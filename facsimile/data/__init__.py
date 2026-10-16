"""The three datasets: loaders, attribute subsets, tasks and the three-way split."""

from __future__ import annotations

from facsimile.data.base import DatasetSpec


def registry() -> dict[str, DatasetSpec]:
    from facsimile.data import acs, ieeecis, sparcs

    return {spec.name: spec for spec in (acs.SPEC, ieeecis.SPEC, sparcs.SPEC)}


def get(name: str) -> DatasetSpec:
    specs = registry()
    if name not in specs:
        raise KeyError(f"unknown dataset {name!r}; known: {sorted(specs)}")
    return specs[name]
