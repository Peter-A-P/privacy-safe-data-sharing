"""A job queue for the expensive work: grid cells and Groundhog fits, many processes at once.

A job is one `facsimile` command and the file it produces. `make` writes the pending jobs to a
JSON-lines file; `run` executes them `jobs` at a time, longest first (so the longest jobs are not
left for last), skipping any whose output already exists, which makes a stopped or evicted run
resume where it was. It stops starting new jobs at the deadline and can run one command when it
finishes, which on the rented machine is the call that deallocates it.

Each job runs with one BLAS, XLA and Polars thread. On the rented machine many jobs share the
cores, and a library that starts a thread per core in each of twenty processes is slower, not
faster (AIM's JAX backend started 64 such threads per process before XLA was told otherwise).

Each job also carries an estimate of its peak memory, and `run` starts the longest pending job
that fits beside the running ones in the memory budget, so short jobs fill the cores that a
long job too large to start would otherwise leave idle. AIM's memory grows as it measures more
marginals: on the rented machine 28 AIM grid cells reached 116 of 123 GB within 90 minutes. So
the dispatcher also checks what the machine actually has free before it starts anything.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import IO

from facsimile.paths import REPO

# Rough seconds per job on the build desktop (2026-10-16 and 17), used only to order the queue.
GRID_SECONDS = {
    "copula": 10, "mst": 70, "ctgan": 700, "tvae": 190, "tabddpm": 1420, "pate_ctgan": 300
}  # fmt: skip
AIM_GRID_SECONDS = {0.5: 900, 1.0: 2700, 2.0: 12_000, 4.0: 40_000, 8.0: 80_000}
FIT_SECONDS = {
    ("copula", None): 3,
    ("ctgan", None): 115,
    ("tvae", None): 19,
    # TabDDPM (2026-10-29): fit and sample at 1,000 rows, with its environment's start-up.
    ("tabddpm", None): 104,
    ("pate_ctgan", 1.0): 13,
    ("pate_ctgan", 8.0): 246,
    ("mst", 1.0): 55,
    ("mst", 8.0): 90,
    ("aim", 1.0): 279,
    ("aim", 8.0): 1822,
    # The leakage ladder (2026-10-27): the three rule-based methods take about a second; TVAE at
    # 3,000 epochs is ten times the default's 19.
    ("perturb", None): 1,
    ("smote", None): 2,
    ("kanon", None): 1,
    ("tvae_overfit", None): 190,
}

# Peak GB per job, rounded up from the build desktop and the rented machine (2026-10-17).
AIM_GRID_GB = {0.5: 4.0, 1.0: 4.0, 2.0: 4.5, 4.0: 5.0, 8.0: 6.0}
FIT_GB: dict[tuple[str, float | None], float] = {("aim", 1.0): 1.5, ("aim", 8.0): 2.0}
DEFAULT_GB = 2.0
RESERVE_GB = 8.0
"""Also start a job only while the machine has its estimate plus this much actually free: the
estimates are typical peaks, and the largest AIM fits grow past them."""


def available_gb() -> float | None:
    """MemAvailable on Linux; None elsewhere, where only the estimates gate."""
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / 2**20
    except OSError:
        pass
    return None


@dataclass(frozen=True, slots=True)
class Job:
    argv: list[str]
    output: str
    """Relative to the repository with forward slashes, so a job file written on Windows runs on
    Linux; the job is done when this file exists."""
    seconds: float
    label: str
    memory_gb: float = DEFAULT_GB

    def done(self) -> bool:
        return (REPO / self.output).exists()


def grid_jobs(datasets: Sequence[str], methods: Sequence[str] | None) -> list[Job]:
    from facsimile.synth.grid import cells

    out = []
    for cell in cells(datasets, methods=methods):
        if cell.done():
            continue
        est = (
            AIM_GRID_SECONDS[cell.epsilon]
            if cell.method == "aim" and cell.epsilon
            else GRID_SECONDS[cell.method]
        )
        out.append(
            Job(
                ["synth", *cell.argv()],
                cell.table_path.relative_to(REPO).as_posix(),
                est,
                f"grid {cell.dataset} {cell.method} {cell.eps_tag} seed{cell.seed}",
                AIM_GRID_GB[cell.epsilon] if cell.method == "aim" and cell.epsilon else DEFAULT_GB,
            )
        )
    return out


def groundhog_jobs(datasets: Sequence[str], methods: Sequence[str] | None) -> list[Job]:
    from facsimile.attacks.groundhog_run import BUDGETS, SCALE, feature_path, fit_names, tag

    out = []
    for ds in datasets:
        for method in methods or list(BUDGETS):
            for eps in BUDGETS[method]:
                for t in range(SCALE.n_outliers + SCALE.n_random):
                    for name in fit_names():
                        path = feature_path(ds, method, eps, t, name)
                        if path.exists():
                            continue
                        eps_arg = "inf" if eps is None else f"{eps:g}"
                        out.append(
                            Job(
                                ["groundhog-fit", ds, method, "--epsilon", eps_arg, str(t), name],
                                path.relative_to(REPO).as_posix(),
                                FIT_SECONDS[(method, eps)],
                                f"groundhog {ds} {method} {tag(eps)} t{t} {name}",
                                FIT_GB.get((method, eps), DEFAULT_GB),
                            )
                        )
    return out


def write_jobs(path: Path, jobs: Iterable[Job]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    items = list(jobs)
    path.write_text("".join(json.dumps(asdict(j)) + "\n" for j in items), encoding="utf-8")
    return len(items)


def read_jobs(path: Path) -> list[Job]:
    return [
        Job(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line
    ]


def next_job(
    pending: Sequence[Job],
    running_gb: float,
    budget_gb: float | None,
    free_gb: float | None = None,
) -> Job | None:
    """The first pending job (they are in longest-first order) whose memory estimate fits beside
    the running jobs. With nothing running, the first job runs whatever its size, so a job larger
    than the whole budget runs alone rather than never."""
    for job in pending:
        if running_gb == 0:
            return job
        fits_budget = budget_gb is None or running_gb + job.memory_gb <= budget_gb
        fits_machine = free_gb is None or job.memory_gb + RESERVE_GB <= free_gb
        if fits_budget and fits_machine:
            return job
    return None


def _failure(text: str) -> str:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()] or ["no output"]
    errors = [ln for ln in lines if "Error" in ln or "error:" in ln]
    return (errors or lines)[-1]


@dataclass
class _Running:
    job: Job
    proc: subprocess.Popen[bytes]
    output: IO[bytes]
    start: float


def run(
    path: Path,
    *,
    jobs: int,
    hours: float | None,
    then: str | None,
    log: Path,
    memory_gb: float | None = None,
) -> int:
    pending = sorted((j for j in read_jobs(path) if not j.done()), key=lambda j: -j.seconds)
    total = len(pending)
    deadline = time.monotonic() + hours * 3600 if hours else None
    env = {
        **os.environ,
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "LOKY_MAX_CPU_COUNT": "1",
        "POLARS_MAX_THREADS": "1",
        "XLA_FLAGS": "--xla_cpu_multi_thread_eigen=false",
        "PYTHONUTF8": "1",
    }
    log.parent.mkdir(parents=True, exist_ok=True)

    def note(line: str) -> None:
        stamp = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{stamp} {line}\n")
        print(line, flush=True)

    note(
        f"queue {path.name}: {total} pending, {jobs} at a time, memory budget "
        f"{memory_gb or 'none'} GB, deadline {hours or 'none'} h"
    )
    running: list[_Running] = []
    failures = 0
    while pending or running:
        open_ = not deadline or time.monotonic() < deadline
        while open_ and len(running) < jobs:
            job = next_job(
                pending,
                sum(r.job.memory_gb for r in running),
                memory_gb,
                available_gb() if memory_gb else None,
            )
            if job is None:
                break
            pending.remove(job)
            if job.done():
                continue
            output = tempfile.TemporaryFile()  # noqa: SIM115 - closed when the job ends
            proc = subprocess.Popen(
                [sys.executable, "-m", "facsimile.cli", *job.argv],
                cwd=REPO,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
            running.append(_Running(job, proc, output, time.perf_counter()))
        if not open_:
            pending.clear()
        for r in [r for r in running if r.proc.poll() is not None]:
            running.remove(r)
            ok = r.proc.returncode == 0 and r.job.done()
            r.output.seek(0)
            tail = "" if ok else f" | {_failure(r.output.read().decode('utf-8', 'replace'))}"
            r.output.close()
            failures += 0 if ok else 1
            took = time.perf_counter() - r.start
            note(f"{'done' if ok else 'FAILED'} {r.job.label} ({took:.0f}s){tail}")
        time.sleep(2)
    remaining = sum(1 for j in read_jobs(path) if not j.done())
    note(f"queue {path.name} stopped: {remaining} not done, {failures} failed")
    if then:
        note(f"running: {then}")
        subprocess.run(then, shell=True, check=False)
    return 1 if remaining else 0
