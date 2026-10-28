"""The one interface every synthesiser is wrapped in.

`fit(train, seed, epsilon) -> sample(n)` (PLAN.md section 4), as one call that returns the
table and everything needed to defend it: the hyperparameters as passed, what the library's own
accountant says was spent, the wall-clock of each half, and the device. Every method works on
the coded domain from `prep.py` and must hand back codes in that domain; `check_codes` holds it
to that before a table is written.
"""

from __future__ import annotations

import os
import platform
import random
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal, Protocol

import numpy as np
import pandas as pd

from facsimile.prep import CODE_DTYPE, Domain, check_codes

DELTA: Final = 1e-5
"""PLAN.md section 2.2. Below 1/n for every train split here (n = 20,000)."""

Family = Literal[
    "non-dp statistical",
    "non-dp deep",
    "dp marginal",
    "dp deep",
    # The leakage ladder (`ladder.py`, PLAN.md section 2.10), the grid's positive controls.
    "non-dp perturbation",
    "non-dp interpolation",
    "non-dp generalisation",
]


@dataclass(frozen=True, slots=True)
class Fitted:
    table: pd.DataFrame
    params: dict[str, Any]
    accounting: dict[str, Any]
    fit_seconds: float
    sample_seconds: float
    device: str
    notes: list[str] = field(default_factory=list)


class Method(Protocol):
    name: str
    library: str
    family: Family

    @property
    def dp(self) -> bool: ...

    def run(
        self, train: pd.DataFrame, domain: Domain, *, seed: int, epsilon: float | None, n: int
    ) -> Fitted: ...


@dataclass(frozen=True, slots=True)
class Wrapped:
    """A method as a name, a library, a family and a function that fits and samples."""

    name: str
    library: str
    family: Family
    fn: Callable[[pd.DataFrame, Domain, int, float | None, int], Fitted]

    @property
    def dp(self) -> bool:
        return self.family.startswith("dp")

    def run(
        self, train: pd.DataFrame, domain: Domain, *, seed: int, epsilon: float | None, n: int
    ) -> Fitted:
        if self.dp and epsilon is None:
            raise ValueError(f"{self.name} is differentially private and needs an epsilon")
        if not self.dp and epsilon is not None:
            raise ValueError(f"{self.name} is not differentially private; its epsilon is infinity")
        check_codes(train, domain)
        before = train.copy()
        fitted = self.fn(train, domain, seed, epsilon, n)
        if not train.equals(before):
            raise AssertionError(f"{self.name} modified the training frame it was given")
        table = fitted.table[domain.names].astype(CODE_DTYPE).reset_index(drop=True)
        check_codes(table, domain)
        if len(table) != n:
            raise AssertionError(f"{self.name} returned {len(table)} rows, asked for {n}")
        return Fitted(
            table, fitted.params, fitted.accounting, fitted.fit_seconds, fitted.sample_seconds,
            fitted.device, fitted.notes,
        )  # fmt: skip


def seed_everything(seed: int) -> None:
    """Python, numpy's global state and torch, CPU and GPU. Libraries that reseed are recorded."""
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def device() -> str:
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def hardware() -> dict[str, Any]:
    """What a timing was measured on. Every timing in this project names it."""
    import torch

    cpu = platform.processor()
    # sys.platform, not platform.system(): mypy narrows on it, so the Linux CI check skips winreg.
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            cpu = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    elif sys.platform == "linux":
        # platform.processor() says only "x86_64" on Linux; the model name is in /proc/cpuinfo.
        try:
            for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("model name"):
                    cpu = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    out: dict[str, Any] = {
        "cpu": cpu,
        "logical_cores": os.cpu_count(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "torch": torch.__version__,
    }
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        out["gpu"] = props.name
        out["gpu_memory_gb"] = round(props.total_memory / 2**30, 1)
    return out


class Timer:
    def __enter__(self) -> Timer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc: object) -> None:
        self.seconds = time.perf_counter() - self.start
