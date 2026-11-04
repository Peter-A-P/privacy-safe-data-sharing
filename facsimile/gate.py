"""The 03 gate on synthetic-trained against real-trained models (PLAN.md section 1 and 5).

Project 03's release gate decides whether a candidate is non-inferior to a baseline: a paired
bootstrap over items, a margin in points, Holm's adjustment across suites, and a power screen. It
grades nothing; a downstream project hands it one JSON side file per side, with one boolean per
item (`docs/gate-adapter.md` in 03). This module writes those files and runs the gate on them.

**The item.** The gate counts correct items, and the utility measure here is ROC AUC, which is
the probability that a model scores a random positive record above a random negative one. So an
item is one pair of real test records, one positive and one negative for the task, and it is
correct when the model scores the positive higher. The pairs are disjoint (no record is in two),
so the items are independent and the gate's bootstrap over items is valid, and the share of
items correct is an unbiased estimate of the AUC. A pair the model scores level is ungradeable
for that side, and the gate drops it from both. Items are named by their index alone, never by a
record.

**The sides.** The baseline is LightGBM trained on the real training split, the ceiling of
`facsimile/utility/tstr.py`; the candidate is the same model, same parameters and seed, trained
on a synthetic table. The suites are the dataset's tasks, and the margin is two points, the
recommendation rule's 0.02 AUC.

**The candidates**, fixed by rule before the gate ran, because the rule of PLAN.md section 2.6
recommends no configuration: per dataset, the configuration nearest the ceiling on its worst
task, over every synthesiser, and the same over the differentially private ones only. Each is
gated on all three seeds of its table.

    facsimile gate export     write spec and side files under gate-runs/
    facsimile gate run        run project 03's gate on them, then summarise the ledger
    facsimile gate sweep      the same runs at every margin from 1 to 20 points

**The sweep** (added 2026-11-03, after the results, for the site's margin slider): the same side
files, unchanged, decided again by the gate at each whole-point margin from 1 to 20. Only the
spec's margin and name change, so every position of the slider shows a verdict the gate gave, with
its own Holm adjustment and power screen, not one read off the 2-point intervals. Each margin has
its own ledger under `gate-runs/sweep/`; the 2-point decisions stay in the main ledger and are the
ones the README reports.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from facsimile import data
from facsimile.data.build import load_built
from facsimile.paths import REPO, RESULTS
from facsimile.synth.grid import Cell, load_table
from facsimile.utility.tstr import fit_score

RUNS = REPO / "gate-runs"
LEDGER = RUNS / "ledger.jsonl"
SUMMARY = RESULTS / "gate.json"
DELTA_POINTS = 2.0
PAIR_SEED = 20261017
SEEDS = (0, 1, 2)
SWEEP = RUNS / "sweep"
SWEEP_POINTS = tuple(range(1, 21))


def gate_dir() -> Path:
    return Path(os.environ.get("FACSIMILE_GATE_DIR", REPO.parent / "03-ai-release-gate"))


def pairs(y: NDArray[np.int64], seed: int = PAIR_SEED) -> NDArray[np.int64]:
    """Disjoint (positive, negative) pairs of test-record positions, as many as the smaller
    class allows, in an order fixed by the seed."""
    rng = np.random.default_rng(seed)
    pos = rng.permutation(np.flatnonzero(y == 1))
    neg = rng.permutation(np.flatnonzero(y == 0))
    n = min(len(pos), len(neg))
    return np.column_stack([pos[:n], neg[:n]])


def outcomes(scores: NDArray[np.float64], items: NDArray[np.int64]) -> tuple[dict[str, bool], int]:
    """Per item, whether the positive record scored above the negative; level pairs left out
    and counted."""
    out: dict[str, bool] = {}
    level = 0
    for k, (p, n) in enumerate(items):
        if scores[p] == scores[n]:
            level += 1
        else:
            out[f"pair-{k}"] = bool(scores[p] > scores[n])
    return out, level


def candidates(report: dict[str, Any]) -> list[tuple[str, str, float | None]]:
    """Per dataset, the configuration nearest the ceiling on its worst task, then the nearest
    with a privacy budget, from the report's pooled utility."""
    chosen: list[tuple[str, str, float | None]] = []
    for ds in sorted({c["dataset"] for c in report["cells"]}):
        scored = [c for c in report["cells"] if c["dataset"] == ds and "utility" in c]

        def worst(c: dict[str, Any]) -> float:
            return min(float(u["delta"]) for u in c["utility"].values())

        for pool in (scored, [c for c in scored if c["epsilon"] is not None]):
            best = max(pool, key=worst)
            pick = (ds, str(best["method"]), best["epsilon"])
            if pick not in chosen:
                chosen.append(pick)
    return chosen


def run_name(cell: Cell) -> str:
    return f"{cell.dataset}-{cell.method}-{cell.eps_tag}-seed{cell.seed}".replace(".", "p")


def side(label: str, run: str, suites: dict[str, tuple[dict[str, bool], int]]) -> dict[str, Any]:
    return {
        "label": label,
        "source": {"run_id": run, "directory": f"gate-runs/{run}"},
        "suites": {
            task: {
                "suite": task,
                "outcomes": got,
                "ungradeable_items": level,
                "calls": len(got) + level,
                "latency_p50_ms": 0.0,
                "cost_usd": 0.0,
                "uncosted_calls": 0,
            }
            for task, (got, level) in suites.items()
        },
    }


def export(cell: Cell) -> Path:
    """Write the spec and both side files for one table."""
    built = load_built(cell.dataset)
    tasks = data.get(cell.dataset).tasks
    table = load_table(cell)
    record = json.loads(cell.record_path.read_text(encoding="utf-8"))
    base: dict[str, tuple[dict[str, bool], int]] = {}
    cand: dict[str, tuple[dict[str, bool], int]] = {}
    for task in tasks:
        _, y = task.xy(built.test, built.domain)
        items = pairs(np.asarray(y, dtype=np.int64))
        real = fit_score(built.train, built.test, task, built.domain, 0)
        synth = fit_score(table, built.test, task, built.domain, 0)
        base[task.name] = outcomes(real.scores, items)
        cand[task.name] = outcomes(synth.scores, items)
    name = run_name(cell)
    out = RUNS / name
    out.mkdir(parents=True, exist_ok=True)
    spec = [
        "version: 1",
        f"name: facsimile-{name}",
        f"delta_points: {DELTA_POINTS}",
        "suites:",
    ]
    for task in tasks:
        spec += [
            f"  - key: {task.name}",
            f"    source: {{kind: outcomes_file, block: {task.name}}}",
        ]
    # LF on every platform, and kept byte for byte by .gitattributes: the ledger names each side
    # file by the hash of its bytes, so a checkout must reproduce them exactly.
    (out / "spec.yaml").write_text("\n".join(spec) + "\n", encoding="utf-8", newline="\n")
    eps = "no privacy" if cell.epsilon is None else f"epsilon {cell.epsilon:g}"
    files = {
        "baseline.json": side("lightgbm trained on the real training split", name, base),
        "candidate.json": side(
            f"lightgbm trained on {cell.method}, {eps}, seed {cell.seed} "
            f"(table sha256 {record['table_sha256'][:12]})",
            name,
            cand,
        ),
    }
    for fname, payload in files.items():
        text = json.dumps(payload, indent=1) + "\n"
        (out / fname).write_text(text, encoding="utf-8", newline="\n")
    return out


def compare(run: Path, points: int | None = None) -> bool:
    """Run project 03's gate on one exported run: True on a pass. The gate exits 1 on a block and
    on a crash alike, so a run counts as decided only when it appended its record. With `points`,
    the same sides are decided at that margin into the sweep's ledger for it."""
    spec, ledger, out = run / "spec.yaml", LEDGER, run / "decision.md"
    if points is not None:
        work = SWEEP / f"m{points:02d}"
        work.mkdir(parents=True, exist_ok=True)
        text = (run / "spec.yaml").read_text(encoding="utf-8")
        text = text.replace(f"delta_points: {DELTA_POINTS}", f"delta_points: {float(points)}")
        text = text.replace(
            f"name: facsimile-{run.name}", f"name: facsimile-{run.name}-m{points:02d}"
        )
        spec, ledger, out = (
            work / f"{run.name}.yaml",
            work / "ledger.jsonl",
            work / f"{run.name}.md",
        )
        spec.write_text(text, encoding="utf-8", newline="\n")
    before = _records(ledger)
    args = [
        "uv",
        "run",
        "--no-sync",
        "--project",
        str(gate_dir()),
        "gate",
        "compare",
        "--spec",
        str(spec),
        "--baseline",
        str(run / "baseline.json"),
        "--candidate",
        str(run / "candidate.json"),
        "--ledger",
        str(ledger),
        "--out",
        str(out),
    ]
    code = subprocess.run(
        args, cwd=gate_dir(), check=False, capture_output=points is not None
    ).returncode
    if code not in (0, 1) or _records(ledger) != before + 1:
        raise RuntimeError(f"{run.name}: the gate exited {code} without recording a decision")
    return code == 0


def _records(ledger: Path = LEDGER) -> int:
    if not ledger.exists():
        return 0
    return sum(1 for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip())


def sweep(points: int) -> None:
    """Decide every exported run at one margin, skipping runs its ledger already holds."""
    ledger = SWEEP / f"m{points:02d}" / "ledger.jsonl"
    done = {r["spec_name"] for r in _read(ledger)}
    for run in sorted(p for p in RUNS.iterdir() if (p / "spec.yaml").exists()):
        if f"facsimile-{run.name}-m{points:02d}" not in done:
            compare(run, points)


def _read(ledger: Path) -> list[dict[str, Any]]:
    if not ledger.exists():
        return []
    return [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines() if x.strip()]


def _outcome(suites: list[dict[str, Any]]) -> str:
    verdicts = {s["verdict"] for s in suites}
    return "block" if "block" in verdicts else "not decided" if verdicts == {"warn"} else "pass"


def _sweep_summary() -> dict[str, Any]:
    """Per run, the gate's outcome at each swept margin."""
    by_run: dict[str, dict[str, str]] = {}
    for points in SWEEP_POINTS:
        for rec in _read(SWEEP / f"m{points:02d}" / "ledger.jsonl"):
            run = rec["spec_name"].removeprefix("facsimile-").rsplit("-", 1)[0]
            by_run.setdefault(run, {})[str(points)] = _outcome(rec["suites"])
    return {"points": list(SWEEP_POINTS), "outcomes": by_run}


def summarise() -> dict[str, Any]:
    """The latest ledger record per run, in the shape the report reads."""
    latest: dict[str, dict[str, Any]] = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            latest[rec["spec_name"]] = rec
    runs = []
    for spec_name, rec in sorted(latest.items()):
        ds, method, eps_tag, seed = spec_name.removeprefix("facsimile-").rsplit("-", 3)
        runs.append(
            {
                "run": spec_name.removeprefix("facsimile-"),
                "dataset": ds,
                "method": method,
                "epsilon": None if eps_tag == "inf" else float(eps_tag[3:].replace("p", ".")),
                "seed": int(seed.removeprefix("seed")),
                "passed": rec["passed"],
                "record_id": rec["record_id"],
                "gate_version": rec["gate_version"],
                "suites": [
                    {
                        k: s[k]
                        for k in (
                            "suite",
                            "paired_items",
                            "baseline_accuracy",
                            "candidate_accuracy",
                            "difference",
                            "lo",
                            "hi",
                            "verdict",
                            "under_powered",
                            "items_needed",
                        )
                    }
                    for s in rec["suites"]
                ],
            }
        )
    payload = {"delta_points": DELTA_POINTS, "runs": runs, "sweep": _sweep_summary()}
    SUMMARY.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
