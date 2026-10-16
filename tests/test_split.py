"""The three-way split: disjoint on every build, targets inside train, control the targets' size."""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from facsimile.data.split import (
    LeakageError,
    Sizes,
    Split,
    check_fitted_on_train,
    check_split,
    frame_hash,
    ids_hash,
    make_split,
)

SIZES = Sizes(train=500, control=50, test=200)


def ids(n: int = 2000) -> np.ndarray:
    return np.random.default_rng(0).permutation(np.arange(10_000, 10_000 + n))


def test_split_is_disjoint_and_sized() -> None:
    split = make_split(ids(), SIZES, seed=7)
    assert (split.train.size, split.control.size, split.test.size) == (500, 50, 200)
    assert split.targets.size == split.control.size
    assert set(split.targets) <= set(split.train)
    assert not set(split.train) & set(split.control)
    assert not set(split.train) & set(split.test)
    assert not set(split.control) & set(split.test)


def test_split_is_a_function_of_the_seed() -> None:
    a, b = make_split(ids(), SIZES, seed=7), make_split(ids(), SIZES, seed=7)
    assert ids_hash(a.train) == ids_hash(b.train) and ids_hash(a.targets) == ids_hash(b.targets)
    c = make_split(ids(), SIZES, seed=8)
    assert ids_hash(a.train) != ids_hash(c.train)


@pytest.mark.parametrize("where", ["control", "test"])
def test_a_planted_overlap_is_caught(where: str) -> None:
    split = make_split(ids(), SIZES, seed=7)
    leaked = getattr(split, where).copy()
    leaked[0] = split.train[0]
    planted = _replace(split, where, leaked)
    with pytest.raises(LeakageError, match=f"train and {where}"):
        check_split(planted)


def test_a_target_outside_train_is_caught() -> None:
    split = make_split(ids(), SIZES, seed=7)
    targets = split.targets.copy()
    targets[0] = split.control[0]
    with pytest.raises(LeakageError, match="not in train"):
        check_split(_replace(split, "targets", targets))


def test_a_control_of_the_wrong_size_is_caught() -> None:
    split = make_split(ids(), SIZES, seed=7)
    with pytest.raises(LeakageError, match="targets against"):
        check_split(_replace(split, "control", split.control[:-1]))


def test_duplicate_row_ids_refuse_to_split() -> None:
    dup = ids()
    dup[1] = dup[0]
    with pytest.raises(LeakageError, match="not unique"):
        make_split(dup, SIZES, seed=7)


def test_a_synthesiser_fitted_on_anything_but_train_is_caught() -> None:
    train = pd.DataFrame({"a": [0, 1, 2], "b": [1, 1, 0]})
    edited = train.copy()
    edited.iloc[0, 0] = 2
    check_fitted_on_train(frame_hash(train), frame_hash(train.copy()))
    with pytest.raises(LeakageError):
        check_fitted_on_train(frame_hash(edited), frame_hash(train))
    with pytest.raises(LeakageError):
        check_fitted_on_train(frame_hash(train.iloc[::-1]), frame_hash(train))


def test_published_manifest_withholds_ids_when_told_to() -> None:
    split = make_split(ids(), SIZES, seed=7)
    hidden = split.manifest(publish_ids=False)
    assert "ids" not in hidden["train"] and hidden["train"]["n"] == 500
    shown = split.manifest(publish_ids=True)
    assert len(shown["targets"]["ids"]) == 50


def _replace(split: Split, name: str, ids: np.ndarray) -> Split:
    fields = {f.name: getattr(split, f.name) for f in dataclasses.fields(split)}
    fields[name] = ids
    return Split(**fields)
