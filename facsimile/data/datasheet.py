"""A short published datasheet per built dataset: the subset, the domain sizes, the tasks.

Aggregates only. The positive rate of each task is reported on the test split, which is the
only split whose statistics this project treats as public.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from facsimile.data.base import DatasetSpec
from facsimile.prep import Domain


def write_datasheet(
    spec: DatasetSpec,
    domain: Domain,
    parts: dict[str, pd.DataFrame],
    manifest: dict[str, Any],
    path: Path,
) -> None:
    sizes = spec.sizes
    lines = [
        f"# {spec.title}",
        "",
        "Written by `facsimile build`; do not edit by hand.",
        "",
        f"- Population after the dataset's filter: {manifest['population_rows']:,} records",
        f"- Split seed {spec.split_seed}: train {sizes.train:,}, control {sizes.control:,}, "
        f"test {sizes.test:,}, attack targets {sizes.targets:,} drawn from train",
        f"- Split ids published: {'yes, in split.json' if spec.publish_ids else 'no, counts and hashes only'}",
        f"- Full contingency table: {domain.cells():.3g} cells",
        "",
        "## Attribute subset and domain",
        "",
        "| Column | Kind | Codes | Labels |",
        "|---|---|---:|---|",
    ]
    for col in domain.columns:
        shown = ", ".join(col.labels[:8]) + (", ..." if col.size > 8 else "")
        lines.append(f"| `{col.name}` | {col.kind} | {col.size} | {shown} |")
    lines += [
        "",
        "## Tasks",
        "",
        "| Task | Target | Features | Test rows | Positive rate (test) | Note |",
        "|---|---|---:|---:|---:|---|",
    ]
    test = parts["test"]
    for task in spec.tasks:
        _, y = task.xy(test, domain)
        rate = f"{y.mean():.1%}" if y.size else "n/a"
        lines.append(
            f"| {task.name} | `{task.target}` | {len(task.features)} | {y.size:,} | {rate} | {task.note} |"
        )
    if spec.notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in spec.notes]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
