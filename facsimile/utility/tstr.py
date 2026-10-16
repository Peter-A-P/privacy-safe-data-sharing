"""Utility as train-on-synthetic, test-on-real (PLAN.md section 2.4).

For each task, a LightGBM model is trained on the synthetic table and scored on the real test
split, beside the same model trained on the real training split (the ceiling) and a predictor that
knows only the base rate (the floor, AUC 0.5). The score is ROC AUC, which does not depend on a
threshold and is not flattered by the fraud set's 3.5% base rate the way accuracy would be. The
delta against the ceiling is a paired bootstrap over test records: both models score the same
records, so the records are resampled jointly.

A synthetic table with no positive (or no negative) example of a task cannot train a model; it
scores the floor and the record says why.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.data.base import Task
from facsimile.prep import Domain
from facsimile.utility.stats import RESAMPLES

PARAMS: dict[str, Any] = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "verbose": -1,
    "n_jobs": 4,
}


def auc(y: NDArray[np.int64], score: NDArray[np.float64]) -> float:
    """ROC AUC by the rank-sum identity, ties given half credit."""
    pos, neg = y == 1, y == 0
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = pd.Series(score).rank(method="average").to_numpy()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


@dataclass(frozen=True, slots=True)
class Scored:
    scores: NDArray[np.float64]
    trained: bool
    note: str = ""


def fit_score(
    train: pd.DataFrame, test: pd.DataFrame, task: Task, domain: Domain, seed: int
) -> Scored:
    import lightgbm as lgb

    x_train, y_train = task.xy(train, domain)
    x_test, _ = task.xy(test, domain)
    if len(np.unique(y_train)) < 2:
        return Scored(
            np.full(len(x_test), 0.5),
            False,
            f"training labels are all {int(y_train[0]) if len(y_train) else 'absent'}",
        )
    categorical = [c for c in task.features if domain[c].kind == "categorical"]
    model = lgb.LGBMClassifier(random_state=seed, **PARAMS)
    model.fit(
        x_train.astype("int32"),
        y_train,
        categorical_feature=categorical,
    )
    proba = np.asarray(model.predict_proba(x_test.astype("int32")), dtype=np.float64)
    return Scored(proba[:, 1], True)


def paired_auc_delta(
    y: NDArray[np.int64],
    left: NDArray[np.float64],
    right: NDArray[np.float64],
    *,
    resamples: int = RESAMPLES,
    seed: int = 0,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(y)
    deltas = []
    for _ in range(resamples):
        i = rng.integers(0, n, n)
        a, b = auc(y[i], left[i]), auc(y[i], right[i])
        if np.isfinite(a) and np.isfinite(b):
            deltas.append(a - b)
    point = auc(y, left) - auc(y, right)
    return {
        "point": point,
        "lo": float(np.quantile(deltas, 0.025)),
        "hi": float(np.quantile(deltas, 0.975)),
        "n": n,
    }


def bootstrap_auc(
    y: NDArray[np.int64], score: NDArray[np.float64], *, resamples: int = RESAMPLES, seed: int = 0
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = len(y)
    draws = [auc(y[i], score[i]) for i in (rng.integers(0, n, n) for _ in range(resamples))]
    draws = [d for d in draws if np.isfinite(d)]
    return {
        "point": auc(y, score),
        "lo": float(np.quantile(draws, 0.025)),
        "hi": float(np.quantile(draws, 0.975)),
        "n": n,
    }


def tstr(
    synthetic: pd.DataFrame,
    real_train: pd.DataFrame,
    test: pd.DataFrame,
    tasks: tuple[Task, ...],
    domain: Domain,
    *,
    seed: int = 0,
    ceiling_cache: dict[str, Scored] | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for task in tasks:
        _, y = task.xy(test, domain)
        if ceiling_cache is not None and task.name in ceiling_cache:
            ceiling = ceiling_cache[task.name]
        else:
            ceiling = fit_score(real_train, test, task, domain, seed)
            if ceiling_cache is not None:
                ceiling_cache[task.name] = ceiling
        synth = fit_score(synthetic, test, task, domain, seed)
        out[task.name] = {
            "auc_synthetic": bootstrap_auc(y, synth.scores, seed=seed),
            "auc_real_ceiling": bootstrap_auc(y, ceiling.scores, seed=seed),
            "auc_floor": 0.5,
            "delta_vs_ceiling": paired_auc_delta(y, synth.scores, ceiling.scores, seed=seed),
            "synthetic_trained": synth.trained,
            "note": synth.note,
            "test_rows": len(y),
            "test_positive_rate": float(y.mean()),
        }
    return out
