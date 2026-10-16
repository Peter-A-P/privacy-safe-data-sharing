"""The terms gate and the rule that nothing raw is committed, asked of the real files."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from facsimile import data
from facsimile.data import terms
from facsimile.paths import REPO


def test_every_dataset_has_a_register_row_that_permits_it() -> None:
    entries = terms.register()
    for name in data.registry():
        assert name in entries, f"{name} has no row in docs/data.md's terms register"
        assert entries[name].allowed, f"{name}: {entries[name]}"


def _register(tmp_path: Path, row: str) -> Path:
    path = tmp_path / "data.md"
    path.write_text(
        "# Data\n\n## Terms register\n\n| Key | Dataset | Read | Permitted |\n|---|---|---|---|\n"
        f"{row}\n\n## Next\n",
        encoding="utf-8",
    )
    return path


def test_a_dataset_without_a_row_is_refused(tmp_path: Path) -> None:
    path = _register(tmp_path, "| `acs` | ACS | 2026-10-16 | Yes |")
    with pytest.raises(terms.TermsError, match="no row"):
        terms.require("sparcs", path)


@pytest.mark.parametrize(
    "row",
    [
        "| `sparcs` | SPARCS | pending | Yes |",
        "| `sparcs` | SPARCS | 2026-10-16 | No: research use only |",
        "| `sparcs` | SPARCS | 2026-10-16 | pending |",
    ],
)
def test_an_undated_or_unpermitted_row_is_refused(tmp_path: Path, row: str) -> None:
    with pytest.raises(terms.TermsError, match="nothing is fetched"):
        terms.require("sparcs", _register(tmp_path, row))


def _ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path], cwd=REPO, capture_output=True, check=False
    )
    return result.returncode == 0


@pytest.mark.parametrize(
    "path",
    [
        "data/raw/acs/csv_pca_2018.zip",
        "data/raw/ieee-fraud-detection/train_transaction.csv",
        "data/build/acs/train.parquet",
        "data/synth/ieeecis/ctgan/inf/seed0.parquet",
        ".env",
        "kaggle.json",
    ],
)
def test_git_itself_ignores_anything_with_a_row_in_it(path: str) -> None:
    assert _ignored(path), f"{path} is not ignored by git"


def test_results_are_not_ignored() -> None:
    assert not _ignored("results/acs/domain.json")
