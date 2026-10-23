"""The report pools seeds the way PLAN.md says and fills only the README's marked section."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from facsimile import report


def _attack(main: float, control: float, n: int = 2000) -> dict[str, dict[str, float]]:
    return {
        "main": {"successes": main, "trials": n},
        "control": {"successes": control, "trials": n},
    }


def test_pooling_adds_successes_across_seeds_before_the_risk() -> None:
    one = report.pooled_risk([_attack(300, 200)], 0.95)
    three = report.pooled_risk([_attack(300, 200)] * 3, 0.95)
    assert one["value"] == pytest.approx(three["value"], abs=1e-3)
    assert three["hi"] - three["lo"] < one["hi"] - one["lo"], "three seeds narrow the interval"
    assert three["trials"] == 6000


def test_equal_success_is_no_risk() -> None:
    r = report.pooled_risk([_attack(250, 250)] * 3, 0.99)
    assert r["value"] == 0.0 and r["lo"] == 0.0


def test_the_readme_is_filled_between_the_markers_only(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(report, "RESULTS", tmp_path)
    monkeypatch.setattr(report, "DOCS", tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text(f"# Title\n\nbefore\n{report.START}\nold table\n{report.END}\nafter\n")
    payload: dict[str, Any] = {"rule": {}, "versions": {}, "cells": [], "surface": [], "leaks": []}
    report.write(payload, readme=readme)
    text = readme.read_text()
    assert text.startswith("# Title\n\nbefore\n") and text.endswith("after\n")
    assert "old table" not in text and "No attack detected" in text
    with pytest.raises(ValueError):
        (tmp_path / "bare.md").write_text("no markers")
        report.write(payload, readme=tmp_path / "bare.md")
