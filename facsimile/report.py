"""From the records in `results/` to the tables: the README, `docs/results.md` and the site JSON.

Nothing here measures anything. It reads the per-table records the grid, the attacks, the
utility scoring and the Groundhog runs wrote, pools them the way PLAN.md says, applies the
recommendation rule of `facsimile.surface`, and writes three things:

- `results/report.json`: every cell, every interval, the surface and the leak table; the site
  reads this and nothing else.
- `docs/results.md`: the full tables, one row per dataset, synthesiser and budget.
- The README's result section, between the `report:start` and `report:end` markers. The README
  tables are never edited by hand (CLAUDE.md).

Pooling. An attack's risk for a cell pools the successes of its seeds (main and control
separately) and takes the paper's residual of the two Wilson rates, at 95% for display and at
1 - 0.05 / (number of attacks) for the leak call, the same Bonferroni level the recommendation
rule uses. Utility shows the mean over seeds of AUC(synthetic) - AUC(real ceiling) and the worst
seed's lower bound, because the rule asks that every seed pass.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from typing import Any

from facsimile import __version__
from facsimile.attacks.risk import residual, wilson
from facsimile.paths import DOCS, REPO, RESULTS
from facsimile.surface import ALPHA, DELTA, Point, recommend, risk_ok, utility_ok

DATASETS = ("acs", "ieeecis", "sparcs")
DATASET_NAMES = {
    "acs": "ACS PUMS, California 2018",
    "ieeecis": "IEEE-CIS card transactions",
    "sparcs": "NY SPARCS discharges",
}
METHODS = ("copula", "ctgan", "tvae", "mst", "aim", "pate_ctgan")
METHOD_NAMES = {
    "copula": "Gaussian copula",
    "ctgan": "CTGAN",
    "tvae": "TVAE",
    "mst": "MST",
    "aim": "AIM",
    "pate_ctgan": "PATE-CTGAN",
}
LIBRARY = {
    "copula": "sdv",
    "ctgan": "sdv",
    "tvae": "sdv",
    "mst": "smartnoise-synth",
    "aim": "smartnoise-synth",
    "pate_ctgan": "smartnoise-synth",
}
ATTACKS = (
    "singling_out_univariate",
    "singling_out_multivariate",
    "linkability_k1",
    "linkability_k10",
    "inference",
)
ATTACK_NAMES = {
    "singling_out_univariate": "singling out, univariate",
    "singling_out_multivariate": "singling out, multivariate",
    "linkability_k1": "linkability, 1 neighbour",
    "linkability_k10": "linkability, 10 neighbours",
    "inference": "inference",
}

NOT_RUN: dict[tuple[str, float], str] = {
    ("aim", 4.0): (
        "not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB "
        "(SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2)"
    ),
    ("aim", 8.0): (
        "not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine "
        "tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2)"
    ),
}

START = "<!-- report:start -->"
END = "<!-- report:end -->"


def _eps_key(eps: float | None) -> float:
    return math.inf if eps is None else eps


def _eps_label(eps: float | None) -> str:
    return "inf" if eps is None else f"{eps:g}"


def _load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


@dataclass
class Cell:
    dataset: str
    method: str
    epsilon: float | None
    synth: dict[int, dict[str, Any]] = field(default_factory=dict)
    attacks: dict[int, dict[str, Any]] = field(default_factory=dict)
    utility: dict[int, dict[str, Any]] = field(default_factory=dict)
    groundhog: dict[str, Any] | None = None


def _epsilon_of(record: dict[str, Any]) -> float | None:
    eps = record.get("epsilon")
    return None if eps in (None, "inf") else float(eps)


def load_cells(root: Path = RESULTS) -> dict[tuple[str, str, float | None], Cell]:
    cells: dict[tuple[str, str, float | None], Cell] = {}

    def cell(ds: str, method: str, eps: float | None) -> Cell:
        key = (ds, method, eps)
        if key not in cells:
            cells[key] = Cell(ds, method, eps)
        return cells[key]

    for ds in DATASETS:
        for kind in ("synth", "attacks", "utility"):
            for path in sorted((root / ds / kind).glob("*/*/seed*.json")):
                record = _load(path)
                c = cell(ds, record["method"], _epsilon_of(record))
                getattr(c, kind)[int(record["seed"])] = record
        for path in sorted((root / ds / "groundhog").glob("*/*.json")):
            record = _load(path)
            cell(ds, record["method"], _epsilon_of(record)).groundhog = record
    return cells


# Pooling


def pooled_risk(seeds: list[dict[str, Any]], confidence: float) -> dict[str, float]:
    main = sum(float(s["main"]["successes"]) for s in seeds)
    control = sum(float(s["control"]["successes"]) for s in seeds)
    n_main = sum(int(s["main"]["trials"]) for s in seeds)
    n_control = sum(int(s["control"]["trials"]) for s in seeds)
    r = residual(wilson(main, n_main, confidence), wilson(control, n_control, confidence))
    return {
        "value": r.value,
        "lo": r.lo,
        "hi": r.hi,
        "main_rate": main / n_main,
        "control_rate": control / n_control,
        "trials": n_main,
    }


def _point(c: Cell) -> Point | None:
    seeds = sorted(set(c.attacks) & set(c.utility))
    if not seeds:
        return None
    tasks = list(c.utility[seeds[0]]["tasks"])
    return Point(
        epsilon=c.epsilon,
        utility_lo={
            t: [float(c.utility[s]["tasks"][t]["delta_vs_ceiling"]["lo"]) for s in seeds]
            for t in tasks
        },
        attacks={
            a: [
                (
                    float(c.attacks[s]["attacks"][a]["main"]["successes"]),
                    float(c.attacks[s]["attacks"][a]["control"]["successes"]),
                    int(c.attacks[s]["attacks"][a]["main"]["trials"]),
                )
                for s in seeds
            ]
            for a in ATTACKS
        },
    )


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def summarise(c: Cell) -> dict[str, Any]:
    out: dict[str, Any] = {
        "dataset": c.dataset,
        "method": c.method,
        "epsilon": c.epsilon,
        "seeds": sorted(c.synth),
        "seeds_attacked": sorted(c.attacks),
        "seeds_scored": sorted(c.utility),
    }
    note = NOT_RUN.get((c.method, c.epsilon)) if c.epsilon is not None else None
    if note and not c.synth:
        out["not_run"] = note
    if c.synth:
        recs = [c.synth[s] for s in sorted(c.synth)]
        acc = [r.get("accounting", {}) for r in recs]
        spent = [a.get("epsilon_spent") for a in acc if a.get("epsilon_spent") is not None]
        out["epsilon_spent"] = max(float(x) for x in spent) if spent else None
        out["fit_seconds_median"] = sorted(float(r["fit_seconds"]) for r in recs)[len(recs) // 2]
        out["hardware"] = sorted({_hardware_label(r) for r in recs})
        out["device"] = sorted({str(r.get("device", "")) for r in recs})
    if c.attacks:
        seeds = [c.attacks[s] for s in sorted(c.attacks)]
        bonferroni = 1.0 - ALPHA / len(ATTACKS)
        out["risk"] = {}
        for a in ATTACKS:
            per_seed = [s["attacks"][a] for s in seeds]
            shown = pooled_risk(per_seed, 0.95)
            call = pooled_risk(per_seed, bonferroni)
            shown["detected"] = call["lo"] > 0.0
            shown["lo_bonferroni"] = call["lo"]
            out["risk"][a] = shown
        dcr = [s["dcr"] for s in seeds if "dcr" in s]
        if dcr:
            out["dcr"] = {
                "exact_copy_targets": _mean([d["exact_copy_targets"]["point"] for d in dcr]),
                "exact_copy_control": _mean([d["exact_copy_control"]["point"] for d in dcr]),
                "closer_to_training_share": _mean(
                    [d["closer_to_training_share"]["point"] for d in dcr]
                ),
                "closer_lo_min": min(d["closer_to_training_share"]["lo"] for d in dcr),
            }
    if c.utility:
        seeds = [c.utility[s] for s in sorted(c.utility)]
        out["utility"] = {
            t: {
                "auc_synthetic": _mean([s["tasks"][t]["auc_synthetic"]["point"] for s in seeds]),
                "auc_ceiling": _mean([s["tasks"][t]["auc_real_ceiling"]["point"] for s in seeds]),
                "delta": _mean([s["tasks"][t]["delta_vs_ceiling"]["point"] for s in seeds]),
                "delta_lo_worst": min(s["tasks"][t]["delta_vs_ceiling"]["lo"] for s in seeds),
                "delta_hi_best": max(s["tasks"][t]["delta_vs_ceiling"]["hi"] for s in seeds),
            }
            for t in seeds[0]["tasks"]
        }
        out["marginal_error"] = {
            k: _mean([s["marginal_error"][k]["point"] for s in seeds])
            for k in seeds[0]["marginal_error"]
        }
    if c.groundhog and c.groundhog.get("pooled"):
        acc = c.groundhog["pooled"]["all"]["accuracy"]
        out["membership"] = {
            "accuracy": acc["point"],
            "lo": acc["lo"],
            "hi": acc["hi"],
            "trials": acc["n"],
            "targets": c.groundhog["targets_complete"],
            "rows": c.groundhog["scale"]["n"],
            "detected": acc["lo"] > 0.5,
        }
    p = _point(c)
    if p is not None and len(p.utility_lo[next(iter(p.utility_lo))]) == 3:
        out["passes_utility"] = utility_ok(p)
        out["passes_risk"] = risk_ok(p)
    return out


def _hardware_label(record: dict[str, Any]) -> str:
    """The machine a fit ran on, with the GPU only when the fit used it."""
    h = record.get("hardware", {})
    cpu = str(h.get("cpu", "unknown CPU")).strip()
    if "aws" in str(h.get("os", "")):
        # The rented machine's records predate the /proc/cpuinfo probe, which said only x86_64;
        # every AWS record in this project came from the one m6a.8xlarge (deploy/aws).
        cpu = f"AWS m6a.8xlarge (AMD EPYC, {h.get('logical_cores', 32)} vCPU, 128 GB)"
    gpu = h.get("gpu") if record.get("device") == "cuda" else None
    return f"{cpu} with {gpu}" if gpu else cpu


# The report


def versions() -> dict[str, str]:
    out = {}
    for pkg in ("sdv", "smartnoise-synth", "opendp", "lightgbm", "scikit-learn", "anonymeter"):
        try:
            out[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            continue
    return out


def build(root: Path = RESULTS) -> dict[str, Any]:
    from facsimile.synth import EPSILONS

    cells = load_cells(root)
    for ds in DATASETS:
        for m in METHODS:
            if m in ("copula", "ctgan", "tvae"):
                continue
            for eps in EPSILONS:
                cells.setdefault((ds, m, eps), Cell(ds, m, eps))
    rows = [
        summarise(c)
        for c in sorted(
            cells.values(),
            key=lambda c: (DATASETS.index(c.dataset), METHODS.index(c.method), _eps_key(c.epsilon)),
        )
    ]
    surface = []
    for ds in DATASETS:
        for m in METHODS:
            points = [
                p
                for c in cells.values()
                if c.dataset == ds and c.method == m
                for p in [_point(c)]
                if p is not None and all(len(v) == 3 for v in p.utility_lo.values())
            ]
            if not points:
                continue
            rec = recommend(points)
            missing = [
                _eps_label(c.epsilon)
                for c in cells.values()
                if c.dataset == ds and c.method == m and not c.synth
            ]
            surface.append(
                {
                    "dataset": ds,
                    "method": m,
                    **rec.as_dict(),
                    "budgets_assessed": sorted(
                        (_eps_label(p.epsilon) for p in points),
                        key=lambda s: math.inf if s == "inf" else float(s),
                    ),
                    "budgets_not_run": missing,
                }
            )
    vs = versions()
    leaks = []
    for r in rows:
        for a, risk in r.get("risk", {}).items():
            if risk["detected"]:
                leaks.append(
                    {
                        "dataset": r["dataset"],
                        "library": LIBRARY[r["method"]],
                        "version": vs.get(LIBRARY[r["method"]], "unknown"),
                        "method": r["method"],
                        "epsilon": r["epsilon"],
                        "attack": a,
                        "risk": risk["value"],
                        "lo": risk["lo"],
                        "hi": risk["hi"],
                        "lo_bonferroni": risk["lo_bonferroni"],
                        "main_rate": risk["main_rate"],
                        "control_rate": risk["control_rate"],
                        "seeds": len(r["seeds_attacked"]),
                    }
                )
        mem = r.get("membership")
        if mem and mem["detected"]:
            leaks.append(
                {
                    "dataset": r["dataset"],
                    "library": LIBRARY[r["method"]],
                    "version": vs.get(LIBRARY[r["method"]], "unknown"),
                    "method": r["method"],
                    "epsilon": r["epsilon"],
                    "attack": "membership",
                    "risk": mem["accuracy"],
                    "lo": mem["lo"],
                    "hi": mem["hi"],
                }
            )
    return {
        "facsimile": __version__,
        "rule": {"delta_auc": DELTA, "alpha": ALPHA, "attacks": list(ATTACKS)},
        "versions": vs,
        "cells": rows,
        "surface": surface,
        "leaks": leaks,
    }


# Rendering


def _pct(x: float) -> str:
    return f"{100 * x:.1f}"


def _risk_cell(r: dict[str, Any]) -> str:
    mark = " **leak**" if r["detected"] else ""
    return f"{_pct(r['value'])} ({_pct(r['lo'])} to {_pct(r['hi'])}){mark}"


def _utility_cell(u: dict[str, Any]) -> str:
    return f"{u['delta']:+.3f} (worst seed lo {u['delta_lo_worst']:+.3f})"


def _eps_cell(r: dict[str, Any]) -> str:
    label = _eps_label(r["epsilon"])
    spent = r.get("epsilon_spent")
    if spent is not None and r["epsilon"] is not None and abs(spent - r["epsilon"]) > 1e-6:
        return f"{label} (spent {spent:.2f})"
    return label


def render_results_md(report: dict[str, Any]) -> str:
    out = [
        "# Results",
        "",
        "Written by `facsimile report` from the records in `results/`; do not edit by hand.",
        "Risks are percentages, pooled over the seeds, with 95% intervals; **leak** marks a risk",
        f"whose interval at 1 - {ALPHA}/{len(ATTACKS)} excludes zero. Utility is AUC(synthetic) minus",
        "AUC(real ceiling), the mean over seeds, with the worst seed's lower 95% bound; the rule",
        f"asks that bound to sit above -{DELTA} on every task and seed. Membership is Groundhog",
        "accuracy at about 1,000 rows over six targets (chance is 0.5).",
        "",
        "Library versions: " + ", ".join(f"{k} {v}" for k, v in report["versions"].items()) + ".",
        "",
    ]
    by_ds: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in report["cells"]:
        by_ds[r["dataset"]].append(r)
    for ds in DATASETS:
        out += [f"## {DATASET_NAMES[ds]}", ""]
        rows = by_ds.get(ds, [])
        tasks = next((list(r["utility"]) for r in rows if "utility" in r), [])
        head = (
            ["Synthesiser", "Epsilon"]
            + [ATTACK_NAMES[a] for a in ATTACKS]
            + ["Membership"]
            + [f"Utility, {t}" for t in tasks]
            + ["2-way marginal error", "Closer to training (DCR)", "Fit seconds (median)", "Seeds"]
        )
        out += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        for r in rows:
            name = METHOD_NAMES[r["method"]]
            if "not_run" in r:
                mem = r.get("membership")
                shown = f"{mem['accuracy']:.3f} ({mem['lo']:.3f} to {mem['hi']:.3f})" if mem else ""
                cells = [name, _eps_cell(r), r["not_run"]] + [""] * (len(ATTACKS) - 1) + [shown]
                cells += [""] * (len(head) - len(cells))
                out.append("| " + " | ".join(cells) + " |")
                continue
            risk = r.get("risk", {})
            mem = r.get("membership")
            util = r.get("utility", {})
            dcr = r.get("dcr")
            cells = (
                [name, _eps_cell(r)]
                + [_risk_cell(risk[a]) if a in risk else "pending" for a in ATTACKS]
                + [
                    f"{mem['accuracy']:.3f} ({mem['lo']:.3f} to {mem['hi']:.3f})"
                    if mem
                    else ("pending" if r["epsilon"] in (None, 1.0, 8.0) else "")
                ]
                + [_utility_cell(util[t]) if t in util else "pending" for t in tasks]
                + [
                    f"{r['marginal_error']['2way']:.3f}" if "marginal_error" in r else "",
                    f"{dcr['closer_to_training_share']:.3f}" if dcr else "",
                    f"{r['fit_seconds_median']:,.0f}" if "fit_seconds_median" in r else "",
                    str(len(r["seeds"])),
                ]
            )
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
    hardware = sorted({h for r in report["cells"] for h in r.get("hardware", [])})
    out += ["## Hardware", "", "Fit times were measured on:", ""]
    out += [f"- {h}" for h in hardware]
    out.append("")
    return "\n".join(out)


def render_readme_section(report: dict[str, Any]) -> str:
    out = [
        START,
        "",
        "_Filled by `facsimile report`; the full tables, one row per dataset, synthesiser and budget,",
        "are in [docs/results.md](docs/results.md)._",
        "",
        "**Where to sit.** The rule (PLAN.md section 2.6, fixed before any table was scored): the",
        f"smallest epsilon at which every task is within {DELTA} AUC of the real-data ceiling on",
        "every seed and no attack's risk is detected.",
        "",
        "| Dataset | " + " | ".join(METHOD_NAMES[m] for m in METHODS) + " |",
        "|---|" + "---|" * len(METHODS),
    ]
    surf = {(s["dataset"], s["method"]): s for s in report["surface"]}
    for ds in DATASETS:
        row = [DATASET_NAMES[ds]]
        for m in METHODS:
            s = surf.get((ds, m))
            if s is None:
                row.append("pending")
            elif s["exists"]:
                row.append(f"epsilon {_eps_label(s['epsilon'])}")
            else:
                row.append("none: " + _short_reason(s["reason"]))
        out.append("| " + " | ".join(row) + " |")
    out += [
        "",
        "_none: utility_ means no budget is within the margin of the ceiling on every task and seed;",
        "_none: risk_ means every useful budget has a detected risk; _pending_ means a budget's",
        "tables are not all attacked and scored yet.",
        "",
        "**How close each gets.** The budget at which a synthesiser comes nearest the real-data",
        "ceiling, and the gap on its worst task there: AUC trained on synthetic minus trained on",
        "real, the mean over seeds (the worst seed's lower 95% bound in brackets).",
        "",
        "| Dataset | " + " | ".join(METHOD_NAMES[m] for m in METHODS) + " |",
        "|---|" + "---|" * len(METHODS),
    ]
    for ds in DATASETS:
        row = [DATASET_NAMES[ds]]
        for m in METHODS:
            scored = [
                c
                for c in report["cells"]
                if c["dataset"] == ds and c["method"] == m and "utility" in c
            ]
            if not scored:
                row.append("pending")
                continue
            best = max(scored, key=lambda c: min(u["delta"] for u in c["utility"].values()))
            worst = min(best["utility"].values(), key=lambda u: u["delta"])
            row.append(
                f"{worst['delta']:+.3f} ({worst['delta_lo_worst']:+.3f}) "
                f"at epsilon {_eps_label(best['epsilon'])}"
            )
        out.append("| " + " | ".join(row) + " |")
    out += [
        "",
        "**What leaked.** A risk counts when its interval at the Bonferroni level excludes zero.",
        "",
    ]
    leaks = report["leaks"]
    if not leaks:
        out.append("No attack detected a risk on any table measured so far.")
    else:
        out += [
            "| Dataset | Library and version | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % |",
            "|---|---|---|---|---|---|",
        ]
        for lk in leaks:
            conf = f"{METHOD_NAMES[lk['method']]}, epsilon {_eps_label(lk['epsilon'])}, 20,000 rows"
            if lk["attack"] == "membership":
                meas = f"accuracy {lk['risk']:.3f} ({lk['lo']:.3f} to {lk['hi']:.3f})"
                out.append(
                    f"| {DATASET_NAMES[lk['dataset']]} | {lk['library']} {lk['version']} | "
                    f"{conf.replace('20,000', 'about 1,000')} | membership | {meas} | |"
                )
                continue
            out.append(
                f"| {DATASET_NAMES[lk['dataset']]} | {lk['library']} {lk['version']} | {conf} | "
                f"{ATTACK_NAMES[lk['attack']]} | {_pct(lk['risk'])} ({_pct(lk['lo'])} to "
                f"{_pct(lk['hi'])}) | {_pct(lk['main_rate'])} vs {_pct(lk['control_rate'])} |"
            )
    out += ["", END]
    return "\n".join(out)


def _short_reason(reason: str) -> str:
    if "within" in reason:
        return "utility"
    if "every budget has" in reason:
        return "risk"
    return "useful budgets leak"


def write(report: dict[str, Any], *, readme: Path | None = None) -> list[Path]:
    readme = readme or REPO / "README.md"
    written = []
    path = RESULTS / "report.json"
    path.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    written.append(path)
    md = DOCS / "results.md"
    md.write_text(render_results_md(report), encoding="utf-8")
    written.append(md)
    text = readme.read_text(encoding="utf-8")
    section = render_readme_section(report)
    if START in text and END in text:
        text = re.sub(
            re.escape(START) + r".*?" + re.escape(END), lambda _: section, text, flags=re.S
        )
    else:
        raise ValueError(f"README has no {START} ... {END} markers to fill")
    readme.write_text(text, encoding="utf-8")
    written.append(readme)
    return written
