"""TAPAS's Groundhog classifier on the tables a facsimile Groundhog run scored.

Runs in the TAPAS environment (Python 3.10, `reference/tapas-requirements.txt`), not the
project's: TAPAS needs Python below 3.11, pandas 1.x and numpy 1.x. It reads the tables and the
manifest that `facsimile groundhog-reference` wrote under `data/tapas/<dataset>/<method>/<eps>/`,
and for each target fits TAPAS's own set classifier, the one its `GroundhogAttack` uses: the
naive, histogram and correlation features of Stadler et al. (`NaiveSetFeature`,
`HistSetFeature`, `CorrSetFeature`) and a random forest of 100 trees, TAPAS's default. It
trains on the 40 shadow tables, scores the 20 evaluation tables, and adds the result to
`results/<dataset>/groundhog_reference/<method>-<eps>.json` beside the project's own.

The columns are described to TAPAS as `finite` for categorical attributes (TAPAS one-hot encodes
them) and as `real` for binned numeric ones, with the bin code scaled to [0, 1] (TAPAS keeps the
value and histograms it in ten bins). `finite/ordered` would be the natural description of a bin,
but TAPAS 1.0.0's `HistSetFeature` treats every type starting with "finite" as one-hot and reads
as many encoded columns as the column has values. An ordered column is encoded in one, so the
histogram features after it are taken from the wrong columns. The first reference run used that
description; it was redone with this one (`docs/attacks.md`).

    .venv-tapas/Scripts/python reference/tapas_groundhog.py DATASET METHOD EPS_TAG
"""

from __future__ import annotations

import json
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from tapas.attacks.set_classifiers import (
    CorrSetFeature,
    FeatureBasedSetClassifier,
    HistSetFeature,
    NaiveSetFeature,
)
from tapas.datasets import TabularDataset
from tapas.datasets.data_description import DataDescription

REPO = Path(__file__).resolve().parent.parent
SEED = 20261017


def description(columns: list[dict]) -> DataDescription:
    return DataDescription(
        [
            {
                "name": c["name"],
                "type": "finite" if c["kind"] == "categorical" else "real",
                "representation": int(c["size"]) if c["kind"] == "categorical" else "number",
            }
            for c in columns
        ],
        label="facsimile coded table",
    )


def scaled(frame: pd.DataFrame, columns: list[dict]) -> pd.DataFrame:
    out = {}
    for c in columns:
        codes = frame[c["name"]].astype("int64")
        if c["kind"] == "categorical":
            out[c["name"]] = codes
        else:
            out[c["name"]] = codes / max(int(c["size"]) - 1, 1)
    return pd.DataFrame(out)


def main(dataset: str, method: str, eps_tag: str) -> None:
    here = REPO / "data" / "tapas" / dataset / method / eps_tag
    manifest = json.loads((here / "manifest.json").read_text(encoding="utf-8"))
    desc = description(manifest["columns"])
    rows = []
    for t in manifest["targets"]:
        sets: dict[str, list[TabularDataset]] = {"shadow": [], "eval": []}
        labels: dict[str, list[int]] = {"shadow": [], "eval": []}
        for plan in t["plans"]:
            frame = pd.read_parquet(here / f"t{t['target']}" / f"{plan['name']}.parquet")
            sets[plan["phase"]].append(TabularDataset(scaled(frame, manifest["columns"]), desc))
            labels[plan["phase"]].append(int(plan["label"]))
        clf = FeatureBasedSetClassifier(
            NaiveSetFeature() + HistSetFeature() + CorrSetFeature(),
            RandomForestClassifier(n_estimators=100, random_state=SEED + t["target"]),
        )
        clf.fit(sets["shadow"], labels["shadow"])
        guesses = np.asarray(clf.predict(sets["eval"]))
        truth = np.asarray(labels["eval"])
        rows.append(
            {
                "target": t["target"],
                "kind": t["kind"],
                "correct": int((guesses == truth).sum()),
                "trials": len(truth),
                "true_positive": int(((guesses == 1) & (truth == 1)).sum()),
                "false_positive": int(((guesses == 1) & (truth == 0)).sum()),
            }
        )
    out = REPO / "results" / dataset / "groundhog_reference" / f"{method}-{eps_tag}.json"
    record = json.loads(out.read_text(encoding="utf-8"))
    record["tapas"] = {
        "version": "tapas 1.0.0 at a7069d7 (privacy-sdg-toolbox)",
        "environment": {pkg: metadata.version(pkg) for pkg in ("numpy", "pandas", "scikit-learn")}
        | {"python": sys.version.split()[0]},
        "features": "NaiveSetFeature + HistSetFeature + CorrSetFeature",
        "classifier": "random forest, 100 trees (TAPAS's default for GroundhogAttack)",
        "targets": rows,
        "correct": sum(r["correct"] for r in rows),
        "trials": sum(r["trials"] for r in rows),
    }
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        f"{dataset} {method} {eps_tag}: TAPAS {record['tapas']['correct']}/{record['tapas']['trials']}"
        f" correct; ours {sum(t['ours']['correct'] for t in record['ours']['targets'])}/"
        f"{sum(t['ours']['trials'] for t in record['ours']['targets'])}"
    )


if __name__ == "__main__":
    main(*sys.argv[1:4])
