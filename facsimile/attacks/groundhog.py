"""Membership inference by shadow modelling: the Groundhog attack (Stadler, Oprisanu and Troncoso,
"Synthetic Data: Anonymisation Groundhog Day", USENIX Security 2022).

The question is whether an attacker who sees a synthetic table can tell if one target record was
in the data it was generated from. The attacker knows the synthesiser and its settings and has
reference data from the same population. For each target:

1. **Shadow training.** Draw many datasets of `n` rows from the attacker's reference pool. In
   half, the target replaces one row ("in"); the other half are left as drawn ("out"). Run the
   synthesiser on each and reduce each synthetic table to a feature vector.
2. **The classifier.** A random forest learns in-versus-out from those vectors.
3. **Evaluation.** Fresh datasets from a disjoint evaluation pool, again half with the target,
   are synthesised and classified. Accuracy over them, against 0.5 for a guess, is the attack's
   success on that target; the advantage is twice the accuracy minus one.

Features, as in the paper: the naive set (mean, median and variance of each column's codes), the
histogram set (every one-way marginal) and the correlation set (pairwise correlation of the
codes), concatenated.

**Scale (PLAN.md section 2.3, amended 2026-10-16 by Peter's decision).** Shadow training needs a
synthesiser fit per shadow dataset, and AIM takes about half an hour to hours per 20,000-row
table on the build desktop, so the attack runs at about 1,000 rows, the scale of the paper, on its
own small grid: a fixed set of targets per dataset and three budgets (epsilon 1, 8, infinity). It
measures membership inference at that scale, not on the 20,000-row grid tables.

Targets are drawn from records outside every split and both pools, half of them outliers (the
records farthest on average from the rest, which are the ones the paper shows leak) and half at
random. No record is named: a target is a row position in the dataset's own file.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.attacks.neighbours import distances
from facsimile.prep import Domain
from facsimile.utility.stats import clopper_pearson

Synthesise = Callable[[pd.DataFrame, int], pd.DataFrame]
"""Fit on a coded frame with a seed and return a synthetic frame of the same size."""


def features(table: pd.DataFrame, domain: Domain) -> NDArray[np.float64]:
    """Naive, histogram and correlation features of a coded table, concatenated."""
    values = table[domain.names].to_numpy(dtype=np.float64)
    naive = np.concatenate([values.mean(axis=0), np.median(values, axis=0), values.var(axis=0)])
    hist = np.concatenate(
        [
            np.bincount(values[:, j].astype(np.int64), minlength=c.size) / len(values)
            for j, c in enumerate(domain.columns)
        ]
    )
    with np.errstate(invalid="ignore", divide="ignore"):
        corr = np.corrcoef(values, rowvar=False)
    upper = np.nan_to_num(corr[np.triu_indices(values.shape[1], k=1)], nan=0.0)
    return np.concatenate([naive, hist, upper])


def choose_targets(
    pool: pd.DataFrame,
    domain: Domain,
    *,
    n_outliers: int,
    n_random: int,
    seed: int,
    sample: int = 2000,
) -> pd.DataFrame:
    """Outliers by mean distance to a sample of the pool, plus records drawn at random."""
    rng = np.random.default_rng(seed)
    picked = pool.iloc[rng.choice(len(pool), min(sample, len(pool)), replace=False)]
    mean_dist = distances(picked, picked, domain, domain.names).mean(axis=1)
    outliers = picked.iloc[np.argsort(-mean_dist)[:n_outliers]]
    rest = picked.drop(index=outliers.index)
    randoms = rest.iloc[rng.choice(len(rest), n_random, replace=False)]
    kinds = ["outlier"] * len(outliers) + ["random"] * len(randoms)
    out = pd.concat([outliers, randoms])
    out.attrs["kinds"] = kinds
    return out


@dataclass(frozen=True, slots=True)
class FitPlan:
    """One shadow or evaluation dataset: which pool rows, whether the target is in, which seed."""

    phase: str  # "shadow" or "eval"
    index: int
    label: int  # 1: the target replaces the last row; 0: left as drawn
    rows: NDArray[np.int64]
    seed: int

    @property
    def name(self) -> str:
        return f"{self.phase}{self.index:02d}"


def plan_target(
    shadow_rows: int, eval_rows: int, *, n: int, n_shadow: int, n_eval: int, seed: int
) -> list[FitPlan]:
    """Every dataset one target's attack needs, drawn in a fixed order from one generator.

    The shadow datasets are drawn first and the evaluation datasets after them, from the same
    generator, so the plan is a function of the seed alone and each fit can run anywhere, in any
    order, and come out the same.
    """
    rng = np.random.default_rng(seed)
    plans = [
        FitPlan("shadow", i, i % 2, rng.choice(shadow_rows, n, replace=False), seed * 100_003 + i)
        for i in range(n_shadow)
    ]
    plans += [
        FitPlan(
            "eval", i, i % 2, rng.choice(eval_rows, n, replace=False), seed * 100_003 + 50_000 + i
        )
        for i in range(n_eval)
    ]
    return plans


def plan_dataset(pool: pd.DataFrame, target: pd.DataFrame, plan: FitPlan) -> pd.DataFrame:
    rows = pool.iloc[plan.rows]
    if plan.label:
        rows = pd.concat([rows.iloc[:-1], target])
    return rows.reset_index(drop=True)


def classify(
    shadow: list[tuple[NDArray[np.float64], int]],
    evaluation: list[tuple[NDArray[np.float64], int]],
    *,
    seed: int,
    target_id: int,
    kind: str,
) -> TargetResult:
    """Train the random forest on the shadow features and score it on the evaluation features."""
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=2)
    model.fit(np.vstack([x for x, _ in shadow]), np.asarray([y for _, y in shadow]))
    guesses = model.predict(np.vstack([x for x, _ in evaluation]))
    labels = np.asarray([y for _, y in evaluation])
    return TargetResult(
        target_id,
        kind,
        int((guesses == labels).sum()),
        len(labels),
        int(((guesses == 1) & (labels == 1)).sum()),
        int(((guesses == 1) & (labels == 0)).sum()),
    )


@dataclass(frozen=True, slots=True)
class TargetResult:
    target_id: int
    kind: str
    correct: int
    trials: int
    true_positive: int
    false_positive: int

    def as_dict(self) -> dict[str, Any]:
        acc = clopper_pearson(self.correct, self.trials)
        half = self.trials // 2
        return {
            "target_id": self.target_id,
            "kind": self.kind,
            "accuracy": acc.as_dict(),
            "advantage": 2 * acc.point - 1,
            "tpr": self.true_positive / half if half else float("nan"),
            "fpr": self.false_positive / half if half else float("nan"),
        }


def attack_target(
    target: pd.DataFrame,
    shadow_pool: pd.DataFrame,
    eval_pool: pd.DataFrame,
    synthesise: Synthesise,
    domain: Domain,
    *,
    n: int,
    n_shadow: int,
    n_eval: int,
    seed: int,
    kind: str = "",
) -> TargetResult:
    """The whole attack on one target, in process. The queue runs the same plan one fit at a time."""
    plans = plan_target(
        len(shadow_pool), len(eval_pool), n=n, n_shadow=n_shadow, n_eval=n_eval, seed=seed
    )
    feats: dict[str, list[tuple[NDArray[np.float64], int]]] = {"shadow": [], "eval": []}
    for plan in plans:
        pool = shadow_pool if plan.phase == "shadow" else eval_pool
        table = synthesise(plan_dataset(pool, target, plan), plan.seed)
        feats[plan.phase].append((features(table, domain), plan.label))
    return classify(
        feats["shadow"], feats["eval"], seed=seed, target_id=int(target.index[0]), kind=kind
    )


def pooled(results: list[TargetResult]) -> dict[str, Any]:
    """Accuracy over every evaluation trial of every target, and per kind."""
    out: dict[str, Any] = {}
    for kind in [*sorted({r.kind for r in results}), "all"]:
        chosen = [r for r in results if kind in ("all", r.kind)]
        correct = sum(r.correct for r in chosen)
        trials = sum(r.trials for r in chosen)
        acc = clopper_pearson(correct, trials)
        out[kind] = {
            "accuracy": acc.as_dict(),
            "advantage": 2 * acc.point - 1,
            "targets": len(chosen),
        }
    return out
