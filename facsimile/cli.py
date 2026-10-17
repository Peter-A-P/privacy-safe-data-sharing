"""facsimile data fetch | build | synth | grid | attack | utility.

The pipeline's commands. Each prints what it did and where it wrote; none prints a row.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence


def _datasets(names: Sequence[str]) -> list[str]:
    from facsimile import data

    known = sorted(data.registry())
    return known if list(names) == ["all"] else [data.get(n).name for n in names]


def cmd_fetch(args: argparse.Namespace) -> int:
    from facsimile import data

    for name in _datasets(args.datasets):
        print(f"== {name}")
        data.get(name).fetch()
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    from facsimile import data
    from facsimile.data.build import build

    for name in _datasets(args.datasets):
        built = build(data.get(name))
        print(
            f"{name}: train {len(built.train):,}, control {len(built.control):,}, "
            f"test {len(built.test):,}, targets {len(built.targets):,}; "
            f"{len(built.domain.columns)} columns, {built.domain.cells():.3g} cells; "
            "leakage check passed"
        )
    return 0


def cmd_synth(args: argparse.Namespace) -> int:
    from facsimile.synth.grid import Cell, run_cell

    eps = None if args.epsilon in (None, "inf") else float(args.epsilon)
    record = run_cell(Cell(args.dataset, args.method, eps, args.seed), force=args.force)
    print(record.summary())
    return 0


def cmd_grid(args: argparse.Namespace) -> int:
    from facsimile.synth.grid import cells, run_grid, status

    todo = cells(
        _datasets(args.datasets),
        methods=args.methods,
        seeds=range(args.seeds),
    )
    if args.status:
        print(status(todo))
        return 0
    return run_grid(todo, keep_going=not args.stop_on_error, jobs=args.jobs)


def _done_cells(args: argparse.Namespace):  # type: ignore[no-untyped-def]
    from facsimile.synth.grid import cells

    todo = cells(_datasets(args.datasets), methods=args.methods, seeds=range(args.seeds))
    return [c for c in todo if c.done()]


def cmd_attack(args: argparse.Namespace) -> int:
    from facsimile.attacks.run import run_attacks

    ready = _done_cells(args)
    print(f"attacking {len(ready)} tables")
    for i, cell in enumerate(ready, 1):
        payload = run_attacks(cell, reference=args.reference, force=args.force)
        risks = ", ".join(f"{k} {a['risk']['value']:.3f}" for k, a in payload["attacks"].items())
        print(
            f"[{i}/{len(ready)}] {cell.dataset} {cell.method} {cell.eps_tag} seed{cell.seed}: {risks}",
            flush=True,
        )
    return 0


def cmd_utility(args: argparse.Namespace) -> int:
    from facsimile.utility.run import run_utility

    ready = _done_cells(args)
    print(f"scoring {len(ready)} tables")
    for i, cell in enumerate(ready, 1):
        payload = run_utility(cell, force=args.force)
        aucs = ", ".join(
            f"{t} {v['auc_synthetic']['point']:.3f} (ceiling {v['auc_real_ceiling']['point']:.3f})"
            for t, v in payload["tasks"].items()
        )
        print(
            f"[{i}/{len(ready)}] {cell.dataset} {cell.method} {cell.eps_tag} seed{cell.seed}: {aucs}",
            flush=True,
        )
    return 0


def cmd_groundhog(args: argparse.Namespace) -> int:
    from facsimile.attacks.groundhog_run import BUDGETS, run_groundhog

    for name in _datasets(args.datasets):
        for method in args.methods or list(BUDGETS):
            for eps in BUDGETS[method]:
                tag = "inf" if eps is None else f"{eps:g}"
                print(f"== {name} {method} epsilon {tag}", flush=True)
                payload = run_groundhog(name, method, eps)
                acc = payload["pooled"]["all"]["accuracy"]
                print(
                    f"   accuracy {acc['point']:.3f} ({acc['lo']:.3f} to {acc['hi']:.3f}) "
                    f"over {acc['n']} trials",
                    flush=True,
                )
    return 0


def _eps(text: str | None) -> float | None:
    return None if text is None or text == "inf" else float(text)


def cmd_groundhog_prepare(args: argparse.Namespace) -> int:
    from facsimile.attacks.groundhog_run import load_pools, prepare

    for name in _datasets(args.datasets):
        prepare(name)
        pools = load_pools(name)
        print(
            f"{name}: shadow {len(pools.shadow):,}, evaluation {len(pools.evaluation):,}, targets {pools.kinds}"
        )
    return 0


def cmd_groundhog_fit(args: argparse.Namespace) -> int:
    from facsimile.attacks.groundhog_run import fit_one

    path = fit_one(args.dataset, args.method, _eps(args.epsilon), args.target, args.name)
    print(f"wrote {path.name}")
    return 0


def cmd_groundhog_assemble(args: argparse.Namespace) -> int:
    from facsimile.attacks.groundhog_run import BUDGETS, assemble, tag

    for name in _datasets(args.datasets):
        for method in args.methods or list(BUDGETS):
            for eps in BUDGETS[method]:
                p = assemble(name, method, eps)
                acc = p["pooled"].get("all", {}).get("accuracy")
                shown = (
                    f"{acc['point']:.3f} ({acc['lo']:.3f} to {acc['hi']:.3f})"
                    if acc
                    else "no target complete"
                )
                print(
                    f"{name} {method} {tag(eps)}: {p['targets_complete']} targets, {p['fits_missing']} fits missing, accuracy {shown}"
                )
    return 0


def cmd_queue(args: argparse.Namespace) -> int:
    from pathlib import Path

    from facsimile import queue

    path = Path(args.file)
    if args.queue_command == "make":
        jobs: list[queue.Job] = []
        if args.grid:
            jobs += queue.grid_jobs(_datasets(args.datasets), args.grid_methods)
        if args.groundhog:
            jobs += queue.groundhog_jobs(_datasets(args.datasets), args.groundhog_methods)
        n = queue.write_jobs(path, jobs)
        hours = sum(j.seconds for j in jobs) / 3600
        print(
            f"{n} jobs written to {path}, about {hours:,.0f} process-hours by the desktop's timings"
        )
        return 0
    return queue.run(
        path,
        jobs=args.jobs,
        hours=args.hours,
        then=args.then,
        log=Path(args.log),
        memory_gb=args.memory_gb,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="facsimile", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    data_p = sub.add_parser("data", help="fetch and verify raw data")
    data_sub = data_p.add_subparsers(dest="data_command", required=True)
    fetch_p = data_sub.add_parser("fetch", help="fetch (or verify) a dataset's raw files")
    fetch_p.add_argument("datasets", nargs="+", help="dataset keys, or 'all'")
    fetch_p.set_defaults(func=cmd_fetch)

    build_p = sub.add_parser("build", help="subset, split, encode; run the leakage check")
    build_p.add_argument("datasets", nargs="+")
    build_p.set_defaults(func=cmd_build)

    synth_p = sub.add_parser("synth", help="fit one synthesiser on one dataset and sample")
    synth_p.add_argument("dataset")
    synth_p.add_argument("method")
    synth_p.add_argument("--epsilon", default=None, help="a budget, or 'inf' for non-DP")
    synth_p.add_argument("--seed", type=int, default=0)
    synth_p.add_argument("--force", action="store_true", help="refit even if the table exists")
    synth_p.set_defaults(func=cmd_synth)

    grid_p = sub.add_parser("grid", help="the full synthesiser grid, resumable")
    grid_p.add_argument("datasets", nargs="+")
    grid_p.add_argument("--methods", nargs="*", default=None)
    grid_p.add_argument("--seeds", type=int, default=3)
    grid_p.add_argument("--status", action="store_true", help="report what exists, fit nothing")
    grid_p.add_argument("--stop-on-error", action="store_true")
    grid_p.add_argument("--jobs", type=int, default=1, help="cells run at once, one process each")
    grid_p.set_defaults(func=cmd_grid)

    for name, func, helptext in (
        ("attack", cmd_attack, "the three criteria and DCR on every finished table"),
        ("utility", cmd_utility, "TSTR and marginal error on every finished table"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("datasets", nargs="+")
        p.add_argument("--methods", nargs="*", default=None)
        p.add_argument("--seeds", type=int, default=3)
        p.add_argument("--force", action="store_true")
        if name == "attack":
            p.add_argument("--reference", action="store_true", help="also run Anonymeter")
        p.set_defaults(func=func)

    gh = sub.add_parser("groundhog", help="membership inference at about 1,000 rows, resumable")
    gh.add_argument("datasets", nargs="+")
    gh.add_argument("--methods", nargs="*", default=None)
    gh.set_defaults(func=cmd_groundhog)

    ghp = sub.add_parser("groundhog-prepare", help="draw and save the Groundhog pools and targets")
    ghp.add_argument("datasets", nargs="+")
    ghp.set_defaults(func=cmd_groundhog_prepare)

    ghf = sub.add_parser("groundhog-fit", help="one shadow or evaluation fit, to its feature file")
    ghf.add_argument("dataset")
    ghf.add_argument("method")
    ghf.add_argument("--epsilon", default=None)
    ghf.add_argument("target", type=int)
    ghf.add_argument("name")
    ghf.set_defaults(func=cmd_groundhog_fit)

    gha = sub.add_parser("groundhog-assemble", help="train and score the classifier per target")
    gha.add_argument("datasets", nargs="+")
    gha.add_argument("--methods", nargs="*", default=None)
    gha.set_defaults(func=cmd_groundhog_assemble)

    qp = sub.add_parser("queue", help="the job queue for the rented machine")
    qsub = qp.add_subparsers(dest="queue_command", required=True)
    qm = qsub.add_parser("make")
    qm.add_argument("file")
    qm.add_argument("datasets", nargs="+")
    qm.add_argument("--grid", action="store_true")
    qm.add_argument("--grid-methods", nargs="*", default=None)
    qm.add_argument("--groundhog", action="store_true")
    qm.add_argument("--groundhog-methods", nargs="*", default=None)
    qm.set_defaults(func=cmd_queue)
    qr = qsub.add_parser("run")
    qr.add_argument("file")
    qr.add_argument("--jobs", type=int, default=2)
    qr.add_argument("--hours", type=float, default=None, help="start no job after this many hours")
    qr.add_argument("--then", default=None, help="a shell command to run when the queue stops")
    qr.add_argument("--log", default="data/runs/queue.log")
    qr.add_argument(
        "--memory-gb", type=float, default=None, help="start a job only while estimates fit this"
    )
    qr.set_defaults(func=cmd_queue)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
