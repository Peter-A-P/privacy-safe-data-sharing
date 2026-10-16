"""The three-way split, the attack targets, and the check that keeps them apart.

PLAN.md section 2.5. Each dataset is split once, by a seed:

- **train**: what every synthesiser is fitted on. The people the guarantee protects.
- **control**: real records no synthesiser ever sees, the same size as the target set. An
  attack's success on them is what the synthetic table reveals about anyone; the excess on the
  targets is the leak.
- **test**: utility only, and the stand-in for public knowledge of the population's categories
  (`prep.py`). Never seen by a synthesiser either.

The targets are drawn from train. The leakage check runs on every build and on every table in
the grid: the three splits are disjoint, the targets are inside train, the control is the size
of the target set, and the frame a synthesiser was fitted on is train exactly (by hash).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

Ids = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class Sizes:
    train: int
    control: int
    test: int

    @property
    def total(self) -> int:
        return self.train + self.control + self.test

    @property
    def targets(self) -> int:
        """The target set is the control's size, so that the two success rates are comparable."""
        return self.control


@dataclass(frozen=True, slots=True)
class Split:
    train: Ids
    control: Ids
    test: Ids
    targets: Ids
    seed: int

    def manifest(self, *, publish_ids: bool) -> dict[str, Any]:
        """What is published. Ids only where the terms allow a row reference to be published."""
        out: dict[str, Any] = {"seed": self.seed}
        for name in ("train", "control", "test", "targets"):
            ids: Ids = getattr(self, name)
            entry: dict[str, Any] = {"n": int(ids.size), "sha256": ids_hash(ids)}
            if publish_ids:
                entry["ids"] = sorted(int(i) for i in ids)
            out[name] = entry
        return out


class LeakageError(AssertionError):
    """A split, a target set or a fitted frame broke the separation the attacks depend on."""


def ids_hash(ids: Ids) -> str:
    return hashlib.sha256(np.sort(np.asarray(ids, dtype=np.int64)).tobytes()).hexdigest()


def frame_hash(frame: pd.DataFrame) -> str:
    """A hash of a coded frame's values in row order, so a reordered or edited frame differs."""
    h = hashlib.sha256()
    h.update(",".join(map(str, frame.columns)).encode())
    h.update(np.ascontiguousarray(frame.to_numpy(dtype=np.int64)).tobytes())
    return h.hexdigest()


def make_split(ids: Ids, sizes: Sizes, seed: int) -> Split:
    """Draw the three splits and the targets from `ids` (a dataset's own row identifiers)."""
    ids = np.asarray(ids, dtype=np.int64)
    if np.unique(ids).size != ids.size:
        raise LeakageError("row identifiers are not unique, so no split on them can be disjoint")
    if ids.size < sizes.total:
        raise ValueError(f"{ids.size} rows cannot fill a split of {sizes.total}")
    rng = np.random.default_rng(seed)
    drawn = rng.permutation(ids)[: sizes.total]
    train = drawn[: sizes.train]
    control = drawn[sizes.train : sizes.train + sizes.control]
    test = drawn[sizes.train + sizes.control :]
    targets = rng.choice(train, size=sizes.targets, replace=False)
    split = Split(np.sort(train), np.sort(control), np.sort(test), np.sort(targets), seed)
    check_split(split)
    return split


def check_split(split: Split) -> None:
    """The three splits are disjoint, the targets are inside train, control matches targets."""
    sets = {name: set(getattr(split, name).tolist()) for name in ("train", "control", "test")}
    for a, b in (("train", "control"), ("train", "test"), ("control", "test")):
        shared = sets[a] & sets[b]
        if shared:
            raise LeakageError(f"{len(shared)} records in both {a} and {b}")
    outside = set(split.targets.tolist()) - sets["train"]
    if outside:
        raise LeakageError(f"{len(outside)} attack targets are not in train")
    if split.targets.size != split.control.size:
        raise LeakageError(
            f"{split.targets.size} targets against {split.control.size} control records"
        )
    if np.unique(split.targets).size != split.targets.size:
        raise LeakageError("an attack target was drawn twice")


def check_fitted_on_train(fitted_hash: str, train_hash: str) -> None:
    """A synthesiser's recorded input is the train split, byte for byte, and nothing else."""
    if fitted_hash != train_hash:
        raise LeakageError(
            f"a table was fitted on frame {fitted_hash[:12]}, not on train {train_hash[:12]}"
        )
