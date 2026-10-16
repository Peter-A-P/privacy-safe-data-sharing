"""From attack successes to a risk with an interval, as Giomi et al. define it.

Each attack is run three ways: against the targets (records the synthesiser was fitted on),
against the control (records it never saw), and as a baseline that ignores the synthetic table.
Success rates are Wilson score estimates (Wilson 1927), as in the paper. The risk is the excess
of the main attack's success over the control's, normalised by the room the control leaves:

    risk = (r_main - r_control) / (1 - r_control)

with the error propagated from both rates to first order, and the result bounded to [0, 1]. A
risk is only read as a leak when its interval excludes zero. The baseline is a sanity floor: an
attack that does no better than the baseline on the targets has not found anything, whatever the
risk says.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from scipy.stats import norm

CONFIDENCE = 0.95


@dataclass(frozen=True, slots=True)
class Rate:
    """A Wilson score estimate of a success rate and its symmetric error at the confidence level."""

    value: float
    error: float
    successes: float
    trials: int

    @property
    def lo(self) -> float:
        return max(0.0, self.value - self.error)

    @property
    def hi(self) -> float:
        return min(1.0, self.value + self.error)


def wilson(successes: float, trials: int, confidence: float = CONFIDENCE) -> Rate:
    if trials <= 0:
        raise ValueError("an attack with no trials has no rate")
    z = float(norm.ppf(0.5 * (1.0 + confidence)))
    z2 = z * z
    denominator = trials + z2
    value = (successes + 0.5 * z2) / denominator
    error = (z / denominator) * math.sqrt(successes * (trials - successes) / trials + 0.25 * z2)
    return Rate(value, error, successes, trials)


@dataclass(frozen=True, slots=True)
class Risk:
    value: float
    lo: float
    hi: float

    @property
    def detected(self) -> bool:
        """The interval excludes zero: the targets were attacked more successfully than the control."""
        return self.lo > 0.0


def residual(main: Rate, control: Rate) -> Risk:
    """The paper's risk: excess success over the control, normalised, with propagated error."""
    if control.value >= 1.0:
        return Risk(0.0, 0.0, 1.0)
    point = (main.value - control.value) / (1.0 - control.value)
    d_main = 1.0 / abs(1.0 - control.value)
    d_control = (main.value - 1.0) / (1.0 - control.value) ** 2
    error = math.sqrt((main.error * d_main) ** 2 + (control.error * d_control) ** 2)

    def bound(x: float) -> float:
        return min(max(x, 0.0), 1.0)

    return Risk(bound(point), bound(point - error), bound(point + error))


@dataclass(frozen=True, slots=True)
class AttackResult:
    attack: str
    n_attacks: int
    main: Rate
    control: Rate
    baseline: Rate
    params: dict[str, Any]

    @property
    def risk(self) -> Risk:
        return residual(self.main, self.control)

    @property
    def beats_baseline(self) -> bool:
        return self.main.lo > self.baseline.hi

    def as_dict(self) -> dict[str, Any]:
        def rate(r: Rate) -> dict[str, float]:
            return {
                "value": r.value,
                "lo": r.lo,
                "hi": r.hi,
                "successes": r.successes,
                "trials": r.trials,
            }

        risk = self.risk
        return {
            "attack": self.attack,
            "n_attacks": self.n_attacks,
            "main": rate(self.main),
            "control": rate(self.control),
            "baseline": rate(self.baseline),
            "risk": {"value": risk.value, "lo": risk.lo, "hi": risk.hi, "detected": risk.detected},
            "beats_baseline": self.beats_baseline,
            "params": self.params,
        }


def result(
    attack: str,
    n_attacks: int,
    main: float,
    control: float,
    baseline: float,
    params: dict[str, Any],
) -> AttackResult:
    return AttackResult(
        attack,
        n_attacks,
        wilson(main, n_attacks),
        wilson(control, n_attacks),
        wilson(baseline, n_attacks),
        params,
    )
