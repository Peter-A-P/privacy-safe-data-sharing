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
METHODS = ("copula", "ctgan", "tvae", "tabddpm", "mst", "aim", "pate_ctgan")
LADDER = ("perturb", "smote", "kanon", "tvae_overfit")
"""The leakage ladder (PLAN.md section 2.10): reported beside the grid, never in its surface,
its leak table or its gate candidates."""
METHOD_NAMES = {
    "copula": "Gaussian copula",
    "ctgan": "CTGAN",
    "tvae": "TVAE",
    "tabddpm": "TabDDPM",
    "mst": "MST",
    "aim": "AIM",
    "pate_ctgan": "PATE-CTGAN",
    "perturb": "Perturbed copy",
    "smote": "SMOTE-NC",
    "kanon": "k-anonymity, k = 5",
    "tvae_overfit": "TVAE, 3,000 epochs",
}
LIBRARY = {
    "copula": "sdv",
    "ctgan": "sdv",
    "tvae": "sdv",
    "tabddpm": "synthcity",
    "mst": "smartnoise-synth",
    "aim": "smartnoise-synth",
    "pate_ctgan": "smartnoise-synth",
    "perturb": "facsimile",
    "smote": "facsimile",
    "kanon": "facsimile",
    "tvae_overfit": "sdv",
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
        "(SPARCS, seed 1) on a 32-vCPU, 128 GB machine; left out to stay in budget (PLAN.md section 2.2)"
    ),
    ("aim", 8.0): (
        "not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine "
        "tables finished on a 32-vCPU, 128 GB machine; left out to stay in budget (PLAN.md section 2.2)"
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
    exposed: dict[int, dict[str, Any]] = field(default_factory=dict)
    groundhog: dict[str, Any] | None = None
    groundhog_fm: dict[str, Any] | None = None


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
        for kind, attr in (
            ("synth", "synth"),
            ("attacks", "attacks"),
            ("utility", "utility"),
            ("attacks_exposed", "exposed"),
        ):
            for path in sorted((root / ds / kind).glob("*/*/seed*.json")):
                record = _load(path)
                c = cell(ds, record["method"], _epsilon_of(record))
                getattr(c, attr)[int(record["seed"])] = record
        for path in sorted((root / ds / "groundhog").glob("*/*.json")):
            record = _load(path)
            cell(ds, record["method"], _epsilon_of(record)).groundhog = record
        for path in sorted((root / ds / "groundhog_tabfm").glob("*/*.json")):
            record = _load(path)
            if record["method"] != "copy" and record.get("pooled"):
                cell(ds, record["method"], _epsilon_of(record)).groundhog_fm = record
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


def _risks(seeds: list[dict[str, Any]]) -> dict[str, Any]:
    """Each attack's risk pooled over the seeds, shown at 95% and called at the Bonferroni level."""
    bonferroni = 1.0 - ALPHA / len(ATTACKS)
    out: dict[str, Any] = {}
    for a in ATTACKS:
        per_seed = [s["attacks"][a] for s in seeds]
        shown = pooled_risk(per_seed, 0.95)
        call = pooled_risk(per_seed, bonferroni)
        shown["detected"] = call["lo"] > 0.0
        shown["lo_bonferroni"] = call["lo"]
        out[a] = shown
    return out


def _membership_fm(record: dict[str, Any], forest: dict[str, Any] | None) -> dict[str, Any]:
    """TabFM as the membership attacker beside the forest, on the same evaluation tables."""
    pool = record["pooled"]
    fm = pool["tabfm"]["accuracy"]
    narrow = pool["forest_selected"]["accuracy"]
    detected = bool(pool["detected"])
    return {
        "accuracy": fm["point"],
        "lo": fm["lo"],
        "hi": fm["hi"],
        "forest_selected": {k: narrow[k] for k in ("point", "lo", "hi")},
        "delta": pool["delta"]["point"],
        "delta_lo": pool["delta"]["lo"],
        "delta_hi": pool["delta"]["hi"],
        "detected": detected,
        # A verdict that flips: no membership risk under the forest, a detected one under TabFM.
        "flips": detected and not (forest or {}).get("detected", False),
        "targets": record["targets_complete"],
        "tabfm": record["tabfm"],
        "device": record["device"],
        "seconds_median": record["tabfm_seconds_median"],
    }


def membership_fm_controls(root: Path = RESULTS) -> list[dict[str, Any]]:
    """The copy control under both attackers: the attacked table is the real dataset itself."""
    rows = []
    for ds in DATASETS:
        path = root / ds / "groundhog_tabfm" / "copy" / "inf.json"
        if path.exists():
            rec = _load(path)
            if rec.get("pooled"):
                forest = rec["pooled"]["forest"]["accuracy"]
                rows.append(
                    {
                        "dataset": ds,
                        "forest": {k: forest[k] for k in ("point", "lo", "hi")},
                        **_membership_fm(rec, {"detected": forest["lo"] > 0.5}),
                    }
                )
    return rows


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
        out["risk"] = _risks(seeds)
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
    if c.exposed:
        out["risk_exposed"] = _risks([c.exposed[s] for s in sorted(c.exposed)])
        out["seeds_exposed"] = sorted(c.exposed)
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
    if c.groundhog_fm:
        out["membership_tabfm"] = _membership_fm(c.groundhog_fm, out.get("membership"))
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


def versions(root: Path = RESULTS) -> dict[str, str]:
    out = {}
    for pkg in ("sdv", "smartnoise-synth", "opendp", "lightgbm", "scikit-learn", "anonymeter"):
        try:
            out[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            continue
    # synthcity lives in its own environment (docs/synthesisers.md), so its version is the one
    # the TabDDPM tables recorded, not one installed here.
    for record in sorted(root.glob("*/synth/tabddpm/*/seed*.json")):
        params = json.loads(record.read_text(encoding="utf-8"))["params"]
        out["synthcity"] = params["library_version"]
        break
    return out


def agreement(cells: dict[tuple[str, str, float | None], Cell]) -> dict[str, Any]:
    """Every table attacked by both this project and Anonymeter, attack by attack: the two risks
    with their 95% intervals, whether each detects a risk, and the attack-success rates."""
    rows = []
    for c in cells.values():
        for seed, rec in sorted(c.attacks.items()):
            ref = rec.get("reference", {}).get("anonymeter")
            if not ref:
                continue
            for a in ATTACKS:
                ours, theirs = rec["attacks"][a], ref[a]
                rows.append(
                    {
                        "dataset": c.dataset,
                        "method": c.method,
                        "epsilon": c.epsilon,
                        "seed": seed,
                        "attack": a,
                        "ours": {k: ours["risk"][k] for k in ("value", "lo", "hi")},
                        "anonymeter": {k: float(theirs["risk"][k]) for k in ("value", "lo", "hi")},
                        "ours_detected": ours["risk"]["lo"] > 0.0,
                        "anonymeter_detected": float(theirs["risk"]["lo"]) > 0.0,
                        "ours_main": ours["main"]["value"],
                        "anonymeter_main": float(theirs["main"]["value"]),
                        "ours_control": ours["control"]["value"],
                        "anonymeter_control": float(theirs["control"]["value"]),
                        "predicates_found": ours.get("params", {}).get("predicates_found"),
                    }
                )
    if not rows:
        return {"tables": 0, "rows": []}
    by_attack: dict[str, dict[str, float]] = {}
    for a in ATTACKS:
        sub = [r for r in rows if r["attack"] == a]
        diffs = [abs(r["ours"]["value"] - r["anonymeter"]["value"]) for r in sub]
        overlap = [
            r["ours"]["lo"] <= r["anonymeter"]["hi"] and r["anonymeter"]["lo"] <= r["ours"]["hi"]
            for r in sub
        ]
        by_attack[a] = {
            "pairs": len(sub),
            "same_call": sum(r["ours_detected"] == r["anonymeter_detected"] for r in sub)
            / len(sub),
            "intervals_overlap": sum(overlap) / len(sub),
            "mean_abs_diff": _mean(diffs),
            "max_abs_diff": max(diffs),
        }
    return {
        "tables": len({(r["dataset"], r["method"], r["epsilon"], r["seed"]) for r in rows}),
        "by_attack": by_attack,
        "disagreements": [
            r
            for r in rows
            if r["ours_detected"] != r["anonymeter_detected"]
            or not (
                r["ours"]["lo"] <= r["anonymeter"]["hi"]
                and r["anonymeter"]["lo"] <= r["ours"]["hi"]
            )
        ],
    }


def groundhog_reference(root: Path = RESULTS) -> list[dict[str, Any]]:
    """The Groundhog runs scored by both this project and TAPAS on the same tables."""
    from facsimile.utility.stats import clopper_pearson

    rows = []
    for ds in DATASETS:
        for path in sorted((root / ds / "groundhog_reference").glob("*.json")):
            rec = _load(path)
            if not rec.get("tapas"):
                continue
            ours_c = sum(t["ours"]["correct"] for t in rec["ours"]["targets"])
            ours_n = sum(t["ours"]["trials"] for t in rec["ours"]["targets"])
            rows.append(
                {
                    "dataset": ds,
                    "method": rec["method"],
                    "epsilon": rec["epsilon"],
                    "ours": clopper_pearson(ours_c, ours_n).as_dict(),
                    "tapas": clopper_pearson(
                        rec["tapas"]["correct"], rec["tapas"]["trials"]
                    ).as_dict(),
                    "tapas_version": rec["tapas"]["version"],
                }
            )
    return rows


def gate_runs(root: Path = RESULTS) -> dict[str, Any]:
    """Project 03's decisions on synthetic-trained against real-trained (`facsimile/gate.py`)."""
    path = root / "gate.json"
    if not path.exists():
        return {}
    payload = _load(path)
    for run in payload["runs"]:
        verdicts = {s["verdict"] for s in run["suites"]}
        run["outcome"] = (
            "block" if "block" in verdicts else "not decided" if verdicts == {"warn"} else "pass"
        )
    return payload


def leaks_of(
    rows: list[dict[str, Any]], vs: dict[str, str], key: str = "risk"
) -> list[dict[str, Any]]:
    """Every detected risk in these rows, named by library, version, configuration and attack.
    `key` is "risk" for the attacks on all targets, "risk_exposed" for the exposed records; the
    membership leaks come with the first."""
    leaks: list[dict[str, Any]] = []
    seeds_key = "seeds_exposed" if key == "risk_exposed" else "seeds_attacked"
    for r in rows:
        named = {
            "dataset": r["dataset"],
            "library": LIBRARY[r["method"]],
            "version": vs.get(LIBRARY[r["method"]], "unknown"),
            "method": r["method"],
            "epsilon": r["epsilon"],
        }
        for a, risk in r.get(key, {}).items():
            if risk["detected"]:
                leaks.append(
                    {
                        **named,
                        "attack": a,
                        "risk": risk["value"],
                        "lo": risk["lo"],
                        "hi": risk["hi"],
                        "lo_bonferroni": risk["lo_bonferroni"],
                        "main_rate": risk["main_rate"],
                        "control_rate": risk["control_rate"],
                        "seeds": len(r[seeds_key]),
                    }
                )
        for attack in ("membership", "membership_tabfm"):
            mem = r.get(attack)
            if key == "risk" and mem and mem["detected"]:
                leaks.append(
                    {
                        **named,
                        "attack": attack,
                        "risk": mem["accuracy"],
                        "lo": mem["lo"],
                        "hi": mem["hi"],
                    }
                )
    return leaks


def build(root: Path = RESULTS) -> dict[str, Any]:
    from facsimile.synth import EPSILONS

    cells = load_cells(root)
    for ds in DATASETS:
        for m in METHODS:
            if m in ("copula", "ctgan", "tvae", "tabddpm"):
                continue
            for eps in EPSILONS:
                cells.setdefault((ds, m, eps), Cell(ds, m, eps))
    order = METHODS + LADDER

    def ranked(group: tuple[str, ...]) -> list[dict[str, Any]]:
        chosen = [c for c in cells.values() if c.method in group]
        chosen.sort(
            key=lambda c: (DATASETS.index(c.dataset), order.index(c.method), _eps_key(c.epsilon))
        )
        return [summarise(c) for c in chosen]

    rows = ranked(METHODS)
    ladder = ranked(LADDER)
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
    vs = versions(root)
    vs["facsimile"] = __version__
    return {
        "facsimile": __version__,
        "rule": {"delta_auc": DELTA, "alpha": ALPHA, "attacks": list(ATTACKS)},
        "versions": vs,
        "cells": rows,
        "surface": surface,
        "leaks": leaks_of(rows, vs),
        "ladder": ladder,
        "ladder_leaks": leaks_of(ladder, vs),
        "exposed_leaks": leaks_of(rows, vs, "risk_exposed") + leaks_of(ladder, vs, "risk_exposed"),
        "agreement": agreement(cells),
        "groundhog_reference": groundhog_reference(root),
        "membership_tabfm_controls": membership_fm_controls(root),
        "gate": gate_runs(root),
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
    out += render_ladder(report.get("ladder", []))
    out += render_exposed(report["cells"] + report.get("ladder", []))
    out += render_agreement(report.get("agreement", {}))
    out += render_groundhog_reference(report.get("groundhog_reference", []))
    out += render_membership_fm(report)
    out += render_gate(report.get("gate", {}))
    hardware = sorted({h for r in report["cells"] for h in r.get("hardware", [])})
    out += [
        "## Data",
        "",
        "SPARCS: source New York State Department of Health, Hospital Inpatient Discharges",
        "(SPARCS De-Identified): 2024, Health Data NY dataset `sf4k-39ay`, published 2025-10-10,",
        "accessed 2026-10-16. The New York State Department of Health makes no representation,",
        "warranty or guarantee relating to the data or analyses derived from these data. The terms",
        "of all three sets are in `docs/data.md`.",
        "",
    ]
    out += ["## Hardware", "", "Fit times were measured on:", ""]
    out += [f"- {h}" for h in hardware]
    out.append("")
    return "\n".join(out)


def render_agreement(ag: dict[str, Any]) -> list[str]:
    out = ["## Reference agreement: this project against Anonymeter", ""]
    if not ag.get("tables"):
        return [*out, "No table has been attacked by both yet.", ""]
    out += [
        f"{ag['tables']} tables attacked by both, on the same targets, control and synthetic table.",
        "A pair agrees on the call when both or neither detect a risk at 95%; the intervals",
        "overlap when the two risks' 95% intervals share any point. Differences are in risk",
        "percentage points.",
        "",
        "| Attack | Pairs | Same call | Intervals overlap | Mean difference | Largest difference |",
        "|---|---|---|---|---|---|",
    ]
    for a, s in ag["by_attack"].items():
        out.append(
            f"| {ATTACK_NAMES[a]} | {s['pairs']} | {_pct(s['same_call'])}% | "
            f"{_pct(s['intervals_overlap'])}% | {_pct(s['mean_abs_diff'])} | {_pct(s['max_abs_diff'])} |"
        )
    dis = ag["disagreements"]
    out += [
        "",
        f"Disagreements ({len(dis)}): a different call, or intervals that do not overlap.",
        "",
    ]
    if dis:
        out += [
            "| Table | Attack | This project, risk % | Anonymeter, risk % | Success on targets, this project vs Anonymeter, % | Control, % |",
            "|---|---|---|---|---|---|",
        ]
        for r in dis:
            o, t = r["ours"], r["anonymeter"]
            out.append(
                f"| {r['dataset']} {r['method']} epsilon {_eps_label(r['epsilon'])} seed {r['seed']} | "
                f"{ATTACK_NAMES[r['attack']]} | {_pct(o['value'])} ({_pct(o['lo'])} to {_pct(o['hi'])}) | "
                f"{_pct(t['value'])} ({_pct(t['lo'])} to {_pct(t['hi'])}) | "
                f"{_pct(r['ours_main'])} vs {_pct(r['anonymeter_main'])} | "
                f"{_pct(r['ours_control'])} vs {_pct(r['anonymeter_control'])} |"
            )
    out += [
        "",
        "The causes, where the two implementations differ by design, are in `docs/attacks.md`.",
        "",
    ]
    return out


def render_groundhog_reference(rows: list[dict[str, Any]]) -> list[str]:
    out = ["## Reference agreement: Groundhog against TAPAS", ""]
    if not rows:
        return [*out, "No Groundhog run has been scored by TAPAS yet.", ""]
    out += [
        "The same shadow and evaluation tables, scored by this project's feature map and",
        f"classifier and by TAPAS's ({rows[0]['tapas_version']}). Accuracy over six targets",
        "and 20 evaluation tables each, with exact 95% intervals; chance is 0.5. *Copy* is the",
        "positive control: the attacked table is the real dataset itself.",
        "",
        "| Dataset | Tables | This project | TAPAS |",
        "|---|---|---|---|",
    ]
    for r in rows:
        name = (
            "copy (control)"
            if r["method"] == "copy"
            else METHOD_NAMES.get(r["method"], r["method"])
        )
        cells = [
            f"{r[k]['point']:.3f} ({r[k]['lo']:.3f} to {r[k]['hi']:.3f})" for k in ("ours", "tapas")
        ]
        out.append(
            f"| {DATASET_NAMES[r['dataset']]} | {name}, epsilon {_eps_label(r['epsilon'])} | "
            + " | ".join(cells)
            + " |"
        )
    return [*out, "", "What the difference means is in `docs/attacks.md`.", ""]


def _acc(a: dict[str, Any], point: str = "point") -> str:
    return f"{a[point]:.3f} ({a['lo']:.3f} to {a['hi']:.3f})"


def _fm_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in report["cells"] + report.get("ladder", []) if "membership_tabfm" in r]


def render_membership_fm(report: dict[str, Any]) -> list[str]:
    out = ["## Membership inference with a foundation-model attacker", ""]
    rows = _fm_rows(report)
    controls = report.get("membership_tabfm_controls", [])
    if not rows and not controls:
        return [*out, "No Groundhog run has been classified by TabFM yet.", ""]
    first = (rows or controls)[0]
    tabfm = first["membership_tabfm"]["tabfm"] if rows else first["tabfm"]
    out += [
        f"The Groundhog evidence, the same shadow and evaluation tables, classified by TabFM {tabfm}",
        "in place of the random forest (the code is not published; docs/attacks.md says why), on the 500 features",
        "that best separate in from out on the shadow tables. *Forest, 500* is the forest on those",
        "same 500, which separates the classifier's effect from the selection's. Accuracy over six",
        "targets and 20 evaluation tables each, exact 95% intervals; chance is 0.5. The difference",
        "is TabFM's accuracy minus the forest's on the same tables, paired, 95% bootstrap interval.",
        "",
        "| Dataset | Tables | Forest | Forest, 500 | TabFM | TabFM minus forest | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in controls:
        out.append(
            f"| {DATASET_NAMES[r['dataset']]} | copy (control) | {_acc(r['forest'])} | "
            f"{_acc(r['forest_selected'])} | {_acc(r, 'accuracy')} | "
            f"{r['delta']:+.3f} ({r['delta_lo']:+.3f} to {r['delta_hi']:+.3f}) | "
            f"{'detected' if r['detected'] else 'not detected'} |"
        )
    for r in rows:
        m = r["membership_tabfm"]
        forest = r["membership"]
        verdict = (
            "flips to detected" if m["flips"] else ("detected" if m["detected"] else "not detected")
        )
        out.append(
            f"| {DATASET_NAMES[r['dataset']]} | {METHOD_NAMES[r['method']]}, epsilon "
            f"{_eps_label(r['epsilon'])} | {forest['accuracy']:.3f} ({forest['lo']:.3f} to "
            f"{forest['hi']:.3f}) | {_acc(m['forest_selected'])} | {_acc(m, 'accuracy')} | "
            f"{m['delta']:+.3f} ({m['delta_lo']:+.3f} to {m['delta_hi']:+.3f}) | {verdict} |"
        )
    return [*out, ""]


def render_membership_fm_summary(report: dict[str, Any]) -> list[str]:
    rows = [r for r in _fm_rows(report) if r["method"] in METHODS]
    if not rows:
        return []
    flips = [r for r in rows if r["membership_tabfm"]["flips"]]
    better = [r for r in rows if r["membership_tabfm"]["delta_lo"] > 0]
    worse = [r for r in rows if r["membership_tabfm"]["delta_hi"] < 0]
    out = [
        "**A foundation model as the membership attacker.** The same Groundhog evidence classified",
        f"by TabFM instead of the random forest, on {len(rows)} grid configurations: TabFM is",
        f"better on {len(better)}, worse on {len(worse)} and indistinguishable on",
        f"{len(rows) - len(better) - len(worse)} (paired 95% intervals), and "
        + (
            "no configuration with no membership risk under the forest has a detected one under TabFM."
            if not flips
            else f"{len(flips)} configuration{'s' if len(flips) != 1 else ''} with no membership "
            "risk under the forest "
            + ("has" if len(flips) == 1 else "have")
            + " a detected one under TabFM: "
            + "; ".join(
                f"{DATASET_NAMES[r['dataset']]}, {METHOD_NAMES[r['method']]} at epsilon "
                f"{_eps_label(r['epsilon'])}, accuracy {_acc(r['membership_tabfm'], 'accuracy')}"
                for r in flips
            )
            + f". Each verdict is a one-sided test at 2.5 percent, so over {len(rows)} configurations"
            f" about {0.025 * len(rows):.1f} would be detected by chance alone."
        ),
    ]
    controls = report.get("membership_tabfm_controls", [])
    if controls:
        out += [
            "On the copy control, TabFM scores "
            + "; ".join(
                f"{_acc(c, 'accuracy')} on {DATASET_NAMES[c['dataset']]} against the forest's "
                f"{_acc(c['forest'])}, and the forest on the same 500 features "
                f"{_acc(c['forest_selected'])}"
                for c in controls
            )
            + (
                "; most of the gain on the copies is the feature selection, not the model."
                if sum(c["forest_selected"]["point"] - c["forest"]["point"] for c in controls)
                >= sum(c["accuracy"] - c["forest_selected"]["point"] for c in controls)
                else "."
            ),
            "TabFM's weights were trained on synthetic tables drawn from structural causal models and",
            "are licensed for non-commercial, non-production use only, so the code that calls them is",
            "not published and nothing here depends on it. The table by table numbers are in",
            "[docs/results.md](docs/results.md#membership-inference-with-a-foundation-model-attacker).",
        ]
    return [*out, ""]


def _gate_config(run: dict[str, Any]) -> str:
    return f"{METHOD_NAMES[run['method']]}, epsilon {_eps_label(run['epsilon'])}"


def _points(x: float) -> str:
    return f"{100 * x:+.1f}"


def render_gate(gate: dict[str, Any]) -> list[str]:
    out = ["## Through the 03 gate: synthetic-trained against real-trained", ""]
    if not gate:
        return [*out, "The gate has not been run yet.", ""]
    out += [
        "Project 03's release gate, asked whether a model trained on the synthetic table is",
        f"non-inferior to the same model trained on the real data, at a margin of {gate['delta_points']:g}",
        "points. An item is a disjoint pair of one positive and one negative real test record,",
        "correct when the model scores the positive higher, so the share correct estimates the",
        "AUC. Difference is synthetic minus real, in points, with the gate's 95% paired bootstrap",
        "interval. The candidates, per dataset, are the configuration nearest the real-data",
        "ceiling and the nearest with a privacy budget (`facsimile/gate.py`, `docs/gate.md`).",
        "",
        "| Dataset | Candidate | Seed | Gate | Task: difference, points (95% CI), items |",
        "|---|---|---|---|---|",
    ]
    for run in gate["runs"]:
        tasks = "; ".join(
            f"{s['suite']}: {_points(s['difference'])} ({_points(s['lo'])} to {_points(s['hi'])}), "
            f"{s['paired_items']:,}"
            + (f" (power screen asks {s['items_needed']})" if s["under_powered"] else "")
            for s in run["suites"]
        )
        out.append(
            f"| {DATASET_NAMES[run['dataset']]} | {_gate_config(run)} | {run['seed']} | "
            f"{run['outcome']} | {tasks} |"
        )
    return [*out, ""]


def render_gate_summary(gate: dict[str, Any]) -> list[str]:
    if not gate:
        return []
    delta = gate["delta_points"]
    out = [
        "**Through the 03 gate.** Project 03's release gate, asked whether a model trained on the",
        "synthetic table is non-inferior to the same model trained on the real data, at a margin",
        f"of {delta:g} AUC points, on each seed's table. The gap is synthetic minus real on the",
        "worst task, in points, across the three seeds.",
        "",
        "| Dataset | Candidate | Gate, three seeds | Worst-task gap, points |",
        "|---|---|---|---|",
    ]
    groups: dict[tuple[str, str, Any], list[dict[str, Any]]] = {}
    for run in gate["runs"]:
        groups.setdefault((run["dataset"], run["method"], run["epsilon"]), []).append(run)
    for ds in DATASETS:
        keys = sorted((k for k in groups if k[0] == ds), key=lambda k: k[2] is not None)
        for key in keys:
            runs = groups[key]
            outcomes = sorted({r["outcome"] for r in runs})
            verdict = " / ".join(outcomes) + f" on {len(runs)} of {len(runs)}"
            if outcomes == ["not decided"]:
                verdict += " (too few fraud cases for the power screen)"
            worst = [min(r["suites"], key=lambda s: s["difference"]) for r in runs]
            gap = (
                f"{_points(min(s['difference'] for s in worst))} to "
                f"{_points(max(s['difference'] for s in worst))}"
            )
            if all(s["hi"] < -delta / 100 for s in worst):
                gap += f"; every interval wholly below -{delta:g}"
            out.append(f"| {DATASET_NAMES[ds]} | {_gate_config(runs[0])} | {verdict} | {gap} |")
    return [*out, ""]


def _detected(risks: dict[str, Any]) -> list[str]:
    return [ATTACK_NAMES[a] for a in ATTACKS if risks.get(a, {}).get("detected")]


def _worst_gap(r: dict[str, Any]) -> str:
    util = r.get("utility")
    if not util:
        return "pending"
    task, u = min(util.items(), key=lambda kv: kv[1]["delta"])
    return f"{u['delta']:+.3f} ({task})"


def render_ladder(rows: list[dict[str, Any]]) -> list[str]:
    out = ["## The leakage ladder", ""]
    if not rows:
        return [*out, "No ladder table has been made yet.", ""]
    out += [
        "Four methods people use as synthetic or anonymised data, expected to leak, run through the",
        "same pipeline as the grid as its positive controls (PLAN.md section 2.10). They are not on",
        "the surface, in the leak table or among the gate's candidates.",
        "",
        "| Dataset | Method | "
        + " | ".join(ATTACK_NAMES[a] for a in ATTACKS)
        + " | Membership | Utility, worst task | Seeds |",
        "|---|---|" + "---|" * (len(ATTACKS) + 3),
    ]
    for r in rows:
        risk = r.get("risk", {})
        mem = r.get("membership")
        cells = (
            [DATASET_NAMES[r["dataset"]], METHOD_NAMES[r["method"]]]
            + [_risk_cell(risk[a]) if a in risk else "pending" for a in ATTACKS]
            + [
                f"{mem['accuracy']:.3f} ({mem['lo']:.3f} to {mem['hi']:.3f})" if mem else "pending",
                _worst_gap(r),
                str(len(r.get("seeds_attacked", []))),
            ]
        )
        out.append("| " + " | ".join(cells) + " |")
    return [*out, ""]


def render_exposed(rows: list[dict[str, Any]]) -> list[str]:
    out = ["## The most exposed records", ""]
    scored = [r for r in rows if "risk_exposed" in r]
    if not scored:
        return [*out, "No table has been attacked on its exposed records yet.", ""]
    out += [
        "The same attacks on the same tables, on the quarter of the targets most unusual against",
        "the quarter of the control most unusual, ranked by mean distance to 2,000 test-split",
        "records (`facsimile/attacks/exposed.py`): 500 against 500 per seed, seeds pooled.",
        "",
        "| Dataset | Configuration | " + " | ".join(ATTACK_NAMES[a] for a in ATTACKS) + " |",
        "|---|---|" + "---|" * len(ATTACKS),
    ]
    for r in scored:
        risk = r["risk_exposed"]
        conf = f"{METHOD_NAMES[r['method']]}, epsilon {_eps_label(r['epsilon'])}"
        out.append(
            f"| {DATASET_NAMES[r['dataset']]} | {conf} | "
            + " | ".join(_risk_cell(risk[a]) for a in ATTACKS)
            + " |"
        )
    return [*out, ""]


def render_ladder_summary(report: dict[str, Any]) -> list[str]:
    rows = report.get("ladder", [])
    if not rows:
        return []
    out = [
        "**The leakage ladder.** Four methods people use as synthetic or anonymised data, expected",
        "to leak, through the same attacks as the positive controls of the grid (PLAN.md section",
        "2.10). Each cell: how many of the five attacks detect a risk at the same Bonferroni",
        "level, the largest of those risks, and the utility gap on the worst task. The attacks",
        "detected are named in [docs/results.md](docs/results.md#the-leakage-ladder).",
        "",
        "| Dataset | " + " | ".join(METHOD_NAMES[m] for m in LADDER) + " |",
        "|---|" + "---|" * len(LADDER),
    ]
    by = {(r["dataset"], r["method"]): r for r in rows}
    for ds in DATASETS:
        row = [DATASET_NAMES[ds]]
        for m in LADDER:
            r = by.get((ds, m))
            if r is None or "risk" not in r:
                row.append("pending")
                continue
            found = [a for a in ATTACKS if r["risk"][a]["detected"]]
            if not found:
                row.append(f"none detected; utility {_worst_gap(r)}")
                continue
            top = max(found, key=lambda a: r["risk"][a]["value"])
            row.append(
                f"{len(found)} of {len(ATTACKS)}, up to {_pct(r['risk'][top]['value'])}% "
                f"({ATTACK_NAMES[top]}); utility {_worst_gap(r)}"
            )
        out.append("| " + " | ".join(row) + " |")
    return [*out, ""]


def render_exposed_summary(report: dict[str, Any]) -> list[str]:
    grid = [r for r in report["cells"] if "risk_exposed" in r]
    if not grid:
        return []
    found = [lk for lk in report.get("exposed_leaks", []) if lk["method"] in METHODS]
    tests = len(grid) * len(ATTACKS)
    # At the Bonferroni level each test's interval excludes zero by chance with probability
    # ALPHA / len(ATTACKS) / 2, one-sided.
    chance = tests * ALPHA / len(ATTACKS) / 2
    out = [
        "**The most exposed records.** The same attacks on each grid table's most unusual quarter of",
        f"targets against its most unusual quarter of control records: {len(found)} detected risks",
        f"across {len(grid)} configurations, where chance alone would give about {chance:.1f} of the",
        f"{tests} tests."
        + (
            " Every one is a differentially private configuration."
            if found and all(lk["epsilon"] is not None for lk in found)
            else ""
        ),
    ]
    if found:
        out += [
            "",
            "| Dataset | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % |",
            "|---|---|---|---|---|",
        ]
        for lk in found:
            out.append(
                f"| {DATASET_NAMES[lk['dataset']]} | {METHOD_NAMES[lk['method']]}, epsilon "
                f"{_eps_label(lk['epsilon'])} | {ATTACK_NAMES[lk['attack']]} | {_pct(lk['risk'])} "
                f"({_pct(lk['lo'])} to {_pct(lk['hi'])}) | {_pct(lk['main_rate'])} vs "
                f"{_pct(lk['control_rate'])} |"
            )
    return [*out, ""]


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
        *render_gate_summary(report.get("gate", {})),
        *render_ladder_summary(report),
        *render_exposed_summary(report),
        *render_membership_fm_summary(report),
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
            if lk["attack"] in ("membership", "membership_tabfm"):
                meas = f"accuracy {lk['risk']:.3f} ({lk['lo']:.3f} to {lk['hi']:.3f})"
                who = "membership" if lk["attack"] == "membership" else "membership, TabFM"
                out.append(
                    f"| {DATASET_NAMES[lk['dataset']]} | {lk['library']} {lk['version']} | "
                    f"{conf.replace('20,000', 'about 1,000')} | {who} | {meas} | |"
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
