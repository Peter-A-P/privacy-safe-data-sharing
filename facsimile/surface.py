"""The epsilon-utility-risk surface and the recommendation rule (PLAN.md section 2.6).

The rule, stated before the grid was attacked or scored (2026-10-16), so it cannot be fitted to
the answer:

    For each dataset and synthesiser, recommend the smallest epsilon at which
    (1) every task is non-inferior to the real-data ceiling at margin DELTA, on every seed: the
        95% interval of the AUC difference, synthetic-trained minus real-trained, lies above
        -DELTA; and
    (2) no attack detects a risk: for each attack, successes pooled over the three seeds, the
        risk's interval at confidence 1 - 0.05 / (number of attacks) includes zero.
    If no budget satisfies both, say that no such point exists for that synthesiser.

DELTA is 0.02 AUC. It was set after three single-table smoke runs on ACS had been seen, none of
them within 0.05 of the ceiling, and before any table had been scored on purpose. The confidence
in (2) is a Bonferroni correction across the attacks, because five attacks at 95% would call a
leak by chance in about one cell in five. Epsilon infinity (the non-DP methods) is a budget like
any other here and is recommended only if it passes, which is what Rule C candidate 3 tests.

SENSITIVITY_DELTA, 0.05 AUC, is not the rule. It was added on 2026-11-03, after every table had
been scored and the rule had recommended nothing, to show what a reader who accepts more loss
would get: the same rule, run again at the looser margin, reported beside the first and never in
its place.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from facsimile.attacks.risk import residual, wilson

DELTA = 0.02
SENSITIVITY_DELTA = 0.05
ALPHA = 0.05


@dataclass(frozen=True, slots=True)
class Point:
    """One budget of one synthesiser: what each seed said."""

    epsilon: float | None
    """None is epsilon infinity."""
    utility_lo: Mapping[str, Sequence[float]]
    """Per task, per seed: the lower 95% bound of AUC(synthetic) - AUC(real ceiling)."""
    attacks: Mapping[str, Sequence[tuple[float, float, int]]]
    """Per attack, per seed: (main successes, control successes, attacks run)."""

    @property
    def order(self) -> float:
        return math.inf if self.epsilon is None else self.epsilon


def utility_ok(point: Point, delta: float = DELTA) -> bool:
    return all(lo > -delta for seeds in point.utility_lo.values() for lo in seeds) and bool(
        point.utility_lo
    )


def pooled_risk_lo(seeds: Sequence[tuple[float, float, int]], confidence: float) -> float:
    main = sum(s[0] for s in seeds)
    control = sum(s[1] for s in seeds)
    n = sum(s[2] for s in seeds)
    return residual(wilson(main, n, confidence), wilson(control, n, confidence)).lo


def risk_ok(point: Point, alpha: float = ALPHA) -> bool:
    if not point.attacks:
        return False
    confidence = 1.0 - alpha / len(point.attacks)
    return all(pooled_risk_lo(seeds, confidence) == 0.0 for seeds in point.attacks.values())


@dataclass(frozen=True, slots=True)
class Recommendation:
    epsilon: float | None
    exists: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {"epsilon": self.epsilon, "exists": self.exists, "reason": self.reason}


def recommend(
    points: Iterable[Point], delta: float = DELTA, alpha: float = ALPHA
) -> Recommendation:
    ordered = sorted(points, key=lambda p: p.order)
    for p in ordered:
        if utility_ok(p, delta) and risk_ok(p, alpha):
            label = "infinity" if p.epsilon is None else f"{p.epsilon:g}"
            return Recommendation(p.epsilon, True, f"smallest budget passing both: epsilon {label}")
    useful = [p for p in ordered if utility_ok(p, delta)]
    safe = [p for p in ordered if risk_ok(p, alpha)]
    if not useful:
        why = f"no budget is within {delta} AUC of the real-data ceiling on every task and seed"
    elif not safe:
        why = "every budget has an attack whose risk is detected"
    else:
        why = "the budgets that are useful leak and the budgets that do not leak are not useful"
    return Recommendation(None, False, why)
