"""Run the Groundhog attack for one dataset, synthesiser and budget, one fit at a time, anywhere.

Three steps, so that the expensive one can run in parallel on another machine:

1. **prepare** (once per dataset, on the machine with the raw data): the pools come from records
   of the dataset's population outside the train, control and test splits, encoded in the
   build's domain: a shadow pool (the attacker's reference data), a disjoint evaluation pool and
   a third disjoint slice the targets are chosen from. Written to
   `data/groundhog/<dataset>/pools.parquet` with the targets in `targets.json`.
2. **fit** (one per shadow or evaluation dataset): build the dataset from its plan, synthesise,
   reduce to features, write `data/groundhog/<dataset>/<method>/<eps>/t<i>/<phase><k>.npy` and
   the synthetic table beside it as `.parquet`.
3. **assemble**: for every target whose 60 feature files exist, train and score the classifier
   and write `results/<dataset>/groundhog/<method>/<eps>.json`.

The plan for each target is a function of the seed alone (`groundhog.plan_target`), so a fit
run on the desktop and one run on a rented machine are the same fit.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile import __version__, data
from facsimile.attacks.groundhog import (
    FitPlan,
    TargetResult,
    choose_targets,
    classify,
    features,
    plan_dataset,
    plan_target,
    pooled,
)
from facsimile.data.base import ROW_ID
from facsimile.data.build import load_built
from facsimile.paths import DATA, results_dir
from facsimile.prep import encode
from facsimile.synth import methods
from facsimile.synth.base import hardware

BUDGETS: dict[str, tuple[float | None, ...]] = {
    "copula": (None,),
    "ctgan": (None,),
    "tvae": (None,),
    "aim": (1.0, 8.0),
    "mst": (1.0, 8.0),
    "pate_ctgan": (1.0, 8.0),
}
"""PLAN.md section 2.3 as amended: epsilon 1, 8 and infinity."""


@dataclass(frozen=True, slots=True)
class Scale:
    n: int = 1000
    n_shadow: int = 40
    n_eval: int = 20
    n_outliers: int = 3
    n_random: int = 3
    pool_rows: int = 50_000
    seed: int = 20261017


SCALE = Scale()


def tag(epsilon: float | None) -> str:
    return "inf" if epsilon is None else f"eps{epsilon:g}"


def work_dir(dataset: str) -> Path:
    return DATA / "groundhog" / dataset


def feature_path(dataset: str, method: str, epsilon: float | None, target: int, name: str) -> Path:
    return work_dir(dataset) / method / tag(epsilon) / f"t{target}" / f"{name}.npy"


def result_path(dataset: str, method: str, epsilon: float | None) -> Path:
    return results_dir(dataset) / "groundhog" / method / f"{tag(epsilon)}.json"


# 1. prepare


def prepare(dataset: str, scale: Scale = SCALE) -> None:
    out = work_dir(dataset)
    if (out / "pools.parquet").exists() and (out / "targets.json").exists():
        return
    spec = data.get(dataset)
    built = load_built(dataset)
    raw = spec.load_raw().set_index(ROW_ID)[spec.column_names]
    used = set(built.train.index) | set(built.control.index) | set(built.test.index)
    rest = raw.loc[~raw.index.isin(used)]
    rng = np.random.default_rng(scale.seed)
    order = rng.permutation(len(rest))[: 2 * scale.pool_rows + 5000]
    picked = encode(rest.iloc[order], built.domain)
    n_candidates = len(picked) - 2 * scale.pool_rows
    labels = (
        ["shadow"] * scale.pool_rows + ["eval"] * scale.pool_rows + ["candidate"] * n_candidates
    )
    targets = choose_targets(
        picked.iloc[2 * scale.pool_rows :],
        built.domain,
        n_outliers=scale.n_outliers,
        n_random=scale.n_random,
        seed=scale.seed,
    )
    out.mkdir(parents=True, exist_ok=True)
    picked.assign(_pool=labels).to_parquet(out / "pools.parquet")
    listed = [
        {"row": int(r), "kind": k}
        for r, k in zip(targets.index, targets.attrs["kinds"], strict=True)
    ]
    (out / "targets.json").write_text(
        json.dumps({"scale": asdict(scale), "targets": listed}, indent=2) + "\n", encoding="utf-8"
    )


@dataclass(frozen=True, slots=True)
class Pools:
    shadow: pd.DataFrame
    evaluation: pd.DataFrame
    targets: pd.DataFrame
    kinds: list[str]


def load_pools(dataset: str) -> Pools:
    out = work_dir(dataset)
    frame = pd.read_parquet(out / "pools.parquet")
    meta = json.loads((out / "targets.json").read_text(encoding="utf-8"))
    rows = [t["row"] for t in meta["targets"]]
    coded = frame.drop(columns="_pool")
    return Pools(
        shadow=coded[frame["_pool"] == "shadow"],
        evaluation=coded[frame["_pool"] == "eval"],
        targets=coded.loc[rows],
        kinds=[t["kind"] for t in meta["targets"]],
    )


def plans(pools: Pools, target_index: int, scale: Scale = SCALE) -> list[FitPlan]:
    return plan_target(
        len(pools.shadow),
        len(pools.evaluation),
        n=scale.n,
        n_shadow=scale.n_shadow,
        n_eval=scale.n_eval,
        seed=scale.seed + target_index,
    )


def fit_names(scale: Scale = SCALE) -> list[str]:
    return [f"shadow{i:02d}" for i in range(scale.n_shadow)] + [
        f"eval{i:02d}" for i in range(scale.n_eval)
    ]


# 2. fit


def fit_one(
    dataset: str,
    method: str,
    epsilon: float | None,
    target_index: int,
    name: str,
    *,
    pools: Pools | None = None,
    scale: Scale = SCALE,
) -> Path:
    path = feature_path(dataset, method, epsilon, target_index, name)
    if path.exists():
        return path
    pools = pools or load_pools(dataset)
    domain = load_built(dataset).domain
    plan = next(p for p in plans(pools, target_index, scale) if p.name == name)
    pool = pools.shadow if plan.phase == "shadow" else pools.evaluation
    target = pools.targets.iloc[[target_index]]
    start = time.perf_counter()
    table = (
        methods()[method]
        .run(
            plan_dataset(pool, target, plan),
            domain,
            seed=plan.seed % 2**31,
            epsilon=epsilon,
            n=scale.n,
        )
        .table
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    # The table is kept beside its features (a few kilobytes), so a change to the feature map or
    # a reference implementation never needs the synthesiser again.
    table.to_parquet(path.with_suffix(".parquet"))
    tmp = path.with_name(path.stem + ".partial.npy")
    np.save(tmp, features(table, domain))
    tmp.replace(path)
    path.with_suffix(".seconds").write_text(
        f"{time.perf_counter() - start:.1f}\n", encoding="utf-8"
    )
    return path


# 3. assemble


def assemble(
    dataset: str, method: str, epsilon: float | None, scale: Scale = SCALE
) -> dict[str, Any]:
    pools = load_pools(dataset)
    publish_ids = data.get(dataset).publish_ids
    rows: list[dict[str, Any]] = []
    results: list[TargetResult] = []
    seconds: list[float] = []
    missing = 0
    for i, kind in enumerate(pools.kinds):
        feats: dict[str, list[tuple[NDArray[np.float64], int]]] = {"shadow": [], "eval": []}
        complete = True
        for plan in plans(pools, i, scale):
            path = feature_path(dataset, method, epsilon, i, plan.name)
            if not path.exists():
                complete = False
                missing += 1
                continue
            feats[plan.phase].append((np.load(path), plan.label))
            timing = path.with_suffix(".seconds")
            if timing.exists():
                seconds.append(float(timing.read_text(encoding="utf-8")))
        if not complete:
            continue
        res = classify(
            feats["shadow"],
            feats["eval"],
            seed=scale.seed + i,
            # A row id is a row-level reference: published only where the split ids are.
            target_id=int(pools.targets.index[i]) if publish_ids else -1,
            kind=kind,
        )
        results.append(res)
        rows.append({**res.as_dict(), "raw": asdict(res)})
    payload = {
        "facsimile": __version__,
        "dataset": dataset,
        "method": method,
        "epsilon": epsilon,
        "scale": asdict(scale),
        "targets": rows,
        "targets_complete": len(rows),
        "fits_missing": missing,
        "pooled": pooled(results) if results else {},
        "fit_seconds_median": float(np.median(seconds)) if seconds else None,
        "hardware": hardware(),
    }
    path = result_path(dataset, method, epsilon)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def run_groundhog(
    dataset: str, method: str, epsilon: float | None, scale: Scale = SCALE
) -> dict[str, Any]:
    """Every fit in this process, then assemble. The queue does the same fits in parallel."""
    prepare(dataset, scale)
    pools = load_pools(dataset)
    for i in range(len(pools.kinds)):
        for name in fit_names(scale):
            fit_one(dataset, method, epsilon, i, name, pools=pools, scale=scale)
        print(f"  target {i + 1}/{len(pools.kinds)} ({pools.kinds[i]}) fitted", flush=True)
    return assemble(dataset, method, epsilon, scale)


# 4. the reference: the same tables for TAPAS


def reference_dir(dataset: str, method: str, epsilon: float | None) -> Path:
    return DATA / "tapas" / dataset / method / tag(epsilon)


def reference_path(dataset: str, method: str, epsilon: float | None) -> Path:
    return results_dir(dataset) / "groundhog_reference" / f"{method}-{tag(epsilon)}.json"


def export_for_reference(
    dataset: str, method: str, epsilon: float | None, scale: Scale = SCALE
) -> dict[str, Any]:
    """Write every shadow and evaluation table of one Groundhog run to parquet, so that TAPAS (in
    its own Python 3.10 environment, `reference/tapas_groundhog.py`) classifies the same tables,
    and score them here with this project's features and classifier.

    `method` may be "copy", the positive control: the "synthetic" table is the input dataset
    itself, so whether the target is in is written into it. Every other method is refitted from
    its plan and seed; where the Groundhog run kept its feature file, the refitted table must
    reproduce it exactly, which checks that the tables TAPAS sees are the ones the run scored.
    """
    pools = load_pools(dataset)
    domain = load_built(dataset).domain
    out = reference_dir(dataset, method, epsilon)
    targets: list[dict[str, Any]] = []
    for i, kind in enumerate(pools.kinds):
        feats: dict[str, list[tuple[NDArray[np.float64], int]]] = {"shadow": [], "eval": []}
        listed = []
        for plan in plans(pools, i, scale):
            path = out / f"t{i}" / f"{plan.name}.parquet"
            kept_table = feature_path(dataset, method, epsilon, i, plan.name).with_suffix(
                ".parquet"
            )
            if kept_table.exists() and not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(kept_table.read_bytes())
            if path.exists():
                table = pd.read_parquet(path)
            else:
                pool = pools.shadow if plan.phase == "shadow" else pools.evaluation
                real = plan_dataset(pool, pools.targets.iloc[[i]], plan)
                if method == "copy":
                    table = real
                else:
                    table = (
                        methods()[method]
                        .run(real, domain, seed=plan.seed % 2**31, epsilon=epsilon, n=scale.n)
                        .table
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                table.to_parquet(path)
            f = features(table, domain)
            kept = feature_path(dataset, method, epsilon, i, plan.name)
            if method != "copy" and kept.exists() and not np.allclose(np.load(kept), f):
                raise ValueError(f"{path}: the refitted table does not reproduce {kept.name}")
            feats[plan.phase].append((f, plan.label))
            listed.append({"name": plan.name, "phase": plan.phase, "label": plan.label})
        res = classify(feats["shadow"], feats["eval"], seed=scale.seed + i, target_id=-1, kind=kind)
        targets.append({"target": i, "kind": kind, "plans": listed, "ours": asdict(res)})
    manifest = {
        "dataset": dataset,
        "method": method,
        "epsilon": epsilon,
        "columns": [{"name": c.name, "kind": c.kind, "size": c.size} for c in domain.columns],
        "targets": targets,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    payload = {
        "facsimile": __version__,
        "dataset": dataset,
        "method": method,
        "epsilon": epsilon,
        "ours": {
            "features": "naive, histogram and correlation of the codes (facsimile.attacks.groundhog)",
            "classifier": "random forest, 200 trees",
            "targets": [{k: t[k] for k in ("target", "kind", "ours")} for t in targets],
            "pooled": pooled([TargetResult(**t["ours"]) for t in targets]),
        },
    }
    path = reference_path(dataset, method, epsilon)
    if path.exists():
        payload["tapas"] = json.loads(path.read_text(encoding="utf-8")).get("tapas")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
