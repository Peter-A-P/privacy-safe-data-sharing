"""The table grid: datasets x methods x budgets x seeds, one table per cell, resumable.

Each cell runs in its own process (`facsimile synth ...`), so a library that leaks GPU memory or
crashes takes one cell with it rather than the grid, and every cell starts from the same state.
A cell writes two things:

- `data/synth/<dataset>/<method>/<eps>/seed<k>.parquet`: the table. Row-level, gitignored.
- `results/<dataset>/synth/<method>/<eps>/seed<k>.json`: its record. Published: the method,
  library versions, hyperparameters as passed, what the accountant says, the hash of the frame
  it was fitted on (checked against train's), the hash of the table, wall-clock and hardware.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from facsimile import __version__
from facsimile.data.build import load_built
from facsimile.data.split import check_fitted_on_train, frame_hash
from facsimile.paths import results_dir, synth_dir
from facsimile.synth import EPSILONS
from facsimile.synth import methods as registry
from facsimile.synth.base import hardware


@dataclass(frozen=True, slots=True)
class Cell:
    dataset: str
    method: str
    epsilon: float | None
    seed: int

    @property
    def eps_tag(self) -> str:
        return "inf" if self.epsilon is None else f"eps{self.epsilon:g}"

    @property
    def rel(self) -> Path:
        return Path(self.method) / self.eps_tag / f"seed{self.seed}"

    @property
    def table_path(self) -> Path:
        return synth_dir(self.dataset) / self.rel.with_suffix(".parquet")

    @property
    def record_path(self) -> Path:
        return results_dir(self.dataset) / "synth" / self.rel.with_suffix(".json")

    @property
    def failure_path(self) -> Path:
        return results_dir(self.dataset) / "synth" / self.rel.with_suffix(".failed.json")

    def done(self) -> bool:
        return self.table_path.exists() and self.record_path.exists()

    def argv(self) -> list[str]:
        eps = "inf" if self.epsilon is None else f"{self.epsilon:g}"
        return [self.dataset, self.method, "--epsilon", eps, "--seed", str(self.seed)]


@dataclass(frozen=True, slots=True)
class Record:
    payload: dict[str, Any]

    def summary(self) -> str:
        p = self.payload
        acc = p["accounting"]
        spent = acc.get("epsilon_spent", acc.get("epsilon_requested", "inf"))
        return (
            f"{p['dataset']} {p['method']} {p['cell']['eps_tag']} seed{p['seed']}: "
            f"fit {p['fit_seconds']:.1f}s, sample {p['sample_seconds']:.1f}s on {p['device']}, "
            f"epsilon {spent}"
        )


def cells(
    datasets: Sequence[str],
    *,
    methods: Sequence[str] | None = None,
    seeds: Iterable[int] = range(3),
) -> list[Cell]:
    chosen = list(methods or registry())
    seed_list = list(seeds)
    out = []
    for ds in datasets:
        for name in chosen:
            budgets: list[float | None] = list(EPSILONS) if _is_dp(name) else [None]
            for eps in budgets:
                for seed in seed_list:
                    out.append(Cell(ds, name, eps, seed))
    return out


def _is_dp(name: str) -> bool:
    return registry()[name].dp


def run_cell(cell: Cell, *, force: bool = False) -> Record:
    if cell.done() and not force:
        return Record(json.loads(cell.record_path.read_text(encoding="utf-8")))
    built = load_built(cell.dataset)  # runs the leakage check
    method = registry()[cell.method]
    train = built.train
    fitted_on = frame_hash(train)
    check_fitted_on_train(fitted_on, built.train_hash)
    started = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    fitted = method.run(train, built.domain, seed=cell.seed, epsilon=cell.epsilon, n=len(train))
    check_fitted_on_train(frame_hash(train), built.train_hash)

    cell.table_path.parent.mkdir(parents=True, exist_ok=True)
    fitted.table.to_parquet(cell.table_path, index=False)
    payload: dict[str, Any] = {
        "facsimile": __version__,
        "dataset": cell.dataset,
        "method": cell.method,
        "library": method.library,
        "family": method.family,
        "epsilon": cell.epsilon,
        "seed": cell.seed,
        "cell": {"eps_tag": cell.eps_tag},
        "rows": len(fitted.table),
        "params": fitted.params,
        "accounting": fitted.accounting,
        "fitted_on_sha256": fitted_on,
        "train_sha256": built.train_hash,
        "table_sha256": frame_hash(fitted.table),
        "fit_seconds": round(fitted.fit_seconds, 3),
        "sample_seconds": round(fitted.sample_seconds, 3),
        "device": fitted.device,
        "hardware": hardware(),
        "started_utc": started,
        "notes": fitted.notes,
    }
    cell.record_path.parent.mkdir(parents=True, exist_ok=True)
    cell.record_path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    if cell.failure_path.exists():
        cell.failure_path.unlink()
    return Record(payload)


def load_table(cell: Cell) -> pd.DataFrame:
    return pd.read_parquet(cell.table_path)


def _run_one(cell: Cell, env: dict[str, str]) -> tuple[bool, str, float]:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "facsimile.cli", "synth", *cell.argv()],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    took = time.perf_counter() - started
    if proc.returncode == 0:
        return True, proc.stdout.strip().splitlines()[-1], took
    tail = (proc.stderr or proc.stdout).strip().splitlines()[-15:]
    cell.failure_path.parent.mkdir(parents=True, exist_ok=True)
    cell.failure_path.write_text(
        json.dumps(
            {
                "dataset": cell.dataset,
                "method": cell.method,
                "epsilon": cell.epsilon,
                "seed": cell.seed,
                "returncode": proc.returncode,
                "seconds": round(took, 1),
                "stderr_tail": tail,
                "when_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return False, f"FAILED {cell}: {tail[-1] if tail else proc.returncode}", took


def run_grid(todo: Sequence[Cell], *, keep_going: bool = True, jobs: int = 1) -> int:
    """Run every missing cell in its own process, `jobs` at a time. Failures are recorded.

    Timings from cells run in parallel share the machine, so each record's wall-clock is what it
    took under that load; the grid log says how many ran at once.
    """
    pending = [c for c in todo if not c.done()]
    # SDV's CTGAN and TVAE transform data with joblib at n_jobs=-1, which on this desktop starts
    # twelve worker processes of about 540 MB each and leaves too little memory for AIM beside
    # them (measured 2026-10-16). Two workers change nothing in the output, only the memory.
    env = {**os.environ, "LOKY_MAX_CPU_COUNT": os.environ.get("LOKY_MAX_CPU_COUNT", "2")}
    print(
        f"{len(todo) - len(pending)} of {len(todo)} cells done; running {len(pending)}, "
        f"{jobs} at a time",
        flush=True,
    )
    failures = 0
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(_run_one, cell, env): cell for cell in pending}
        for i, future in enumerate(as_completed(futures), 1):
            ok, line, took = future.result()
            print(f"[{i}/{len(pending)}] {line} ({took:.0f}s wall)", flush=True)
            if not ok:
                failures += 1
                if not keep_going:
                    for f in futures:
                        f.cancel()
                    return 1
    return 1 if failures else 0


def status(todo: Sequence[Cell]) -> str:
    done = [c for c in todo if c.done()]
    failed = [c for c in todo if c.failure_path.exists()]
    lines = [f"{len(done)} of {len(todo)} cells done, {len(failed)} failed"]
    by: dict[tuple[str, str], list[int]] = {}
    for c in todo:
        key = (c.dataset, c.method)
        by.setdefault(key, [0, 0])
        by[key][1] += 1
        if c.done():
            by[key][0] += 1
    for (ds, m), (d, t) in sorted(by.items()):
        lines.append(f"  {ds:8s} {m:11s} {d:3d}/{t}")
    return "\n".join(lines)
