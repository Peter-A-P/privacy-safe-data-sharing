"""The recommendation rule on hand-built surfaces with known answers."""

from __future__ import annotations

from facsimile.surface import DELTA, Point, recommend, risk_ok, utility_ok

QUIET = {"inference": [(500.0, 500.0, 2000)] * 3, "linkability": [(30.0, 30.0, 2000)] * 3}
LEAKY = {"inference": [(900.0, 500.0, 2000)] * 3, "linkability": [(30.0, 30.0, 2000)] * 3}


def point(
    eps: float | None, lo: float, attacks: dict[str, list[tuple[float, float, int]]]
) -> Point:
    return Point(eps, {"task": [lo, lo, lo]}, attacks)


def test_the_smallest_budget_that_is_useful_and_quiet_is_chosen() -> None:
    # Utility rises with the budget and crosses -DELTA at epsilon 2; nothing leaks below 8.
    surface = [
        point(0.5, -0.10, QUIET),
        point(1, -0.05, QUIET),
        point(2, -0.015, QUIET),
        point(4, -0.01, QUIET),
        point(8, -0.005, LEAKY),
        point(None, 0.0, LEAKY),
    ]
    rec = recommend(surface)
    assert rec.exists and rec.epsilon == 2


def test_no_such_point_when_usefulness_arrives_only_with_the_leak() -> None:
    surface = [point(1, -0.10, QUIET), point(8, -0.01, LEAKY), point(None, 0.0, LEAKY)]
    rec = recommend(surface)
    assert not rec.exists and "useful leak" in rec.reason


def test_no_such_point_when_nothing_is_useful() -> None:
    rec = recommend([point(e, -0.2, QUIET) for e in (0.5, 1, 8)])
    assert not rec.exists and "within" in rec.reason


def test_non_dp_is_a_budget_like_any_other() -> None:
    rec = recommend([point(None, -0.001, QUIET)])
    assert rec.exists and rec.epsilon is None


def test_utility_must_hold_on_every_seed_and_task() -> None:
    p = Point(1, {"a": [-0.001, -0.001, -(DELTA + 0.001)], "b": [0.0] * 3}, QUIET)
    assert not utility_ok(p)
    assert utility_ok(Point(1, {"a": [-0.001] * 3, "b": [0.0] * 3}, QUIET))


def test_one_seed_of_chance_does_not_make_a_leak_but_a_pooled_excess_does() -> None:
    # One seed at 560 of 2000 against 500 alone is a 95% detection; pooled with two seeds at
    # parity and corrected for two attacks it is not.
    chance = {"inference": [(560.0, 500.0, 2000), (500.0, 500.0, 2000), (500.0, 500.0, 2000)]}
    assert risk_ok(Point(1, {"t": [0.0]}, chance))
    assert not risk_ok(Point(1, {"t": [0.0]}, LEAKY))
