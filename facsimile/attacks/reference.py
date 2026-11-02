"""The reference library on the same tables: Anonymeter (Giomi et al.'s own implementation).

Run on exactly the inputs the project's implementations get: the same targets, control and
synthetic table, the same secret, halves, number of attacks and predicate width. Categorical
attributes are handed over as their labels (Anonymeter compares them for equality) and binned
numeric ones as their bin codes (it scales them by their range and takes the absolute
difference), which is the distance `neighbours.py` uses. The secret is handed over as a label so
that Anonymeter scores an exact match, as the project does.

Singling out runs the same `SEARCHES` searches with the same seeds as the project's
implementation and averages Anonymeter's success counts the same way (PLAN.md section 2.12).
Every result keeps Anonymeter's counts beside its rates, so the report pools them over the seeds
exactly as it pools the project's.

Anonymeter's licence is the Clear BSD licence; its authors hold a patent application on the
method (`docs/attacks.md`). TAPAS, the reference for the Groundhog attack, needs Python below
3.11 and runs in its own environment.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from facsimile.attacks.config import AttackConfig
from facsimile.attacks.singling_out import SEARCHES, search_seeds
from facsimile.prep import Domain

N_JOBS = 2
"""Anonymeter's neighbour search processes. Two, not all cores: it runs beside other work on the
build desktop, and the count changes nothing but the time."""


def for_anonymeter(
    frame: pd.DataFrame, domain: Domain, as_label: Sequence[str] = ()
) -> pd.DataFrame:
    out = {}
    for col in domain.columns:
        codes = frame[col.name].to_numpy()
        if col.kind == "categorical" or col.name in as_label:
            out[col.name] = pd.Series([col.labels[c] for c in codes], dtype=object).to_numpy()
        else:
            out[col.name] = codes.astype("int64")
    return pd.DataFrame(out)


def pack(res: Any) -> dict[str, Any]:
    """An Anonymeter `EvaluationResults` as a record: rates, risk and the counts behind them."""
    risk = res.risk()
    return {
        "main": {"value": res.attack_rate.value, "error": res.attack_rate.error},
        "control": {"value": res.control_rate.value, "error": res.control_rate.error},
        "baseline": {"value": res.baseline_rate.value, "error": res.baseline_rate.error},
        "risk": {"value": risk.value, "lo": risk.ci[0], "hi": risk.ci[1]},
        "counts": {
            "main": float(res.n_success),
            "control": float(res.n_control),
            "baseline": float(res.n_baseline),
            "trials": int(res.n_attacks_ori),
        },
    }


def anonymeter_singling_out(
    ori: pd.DataFrame,
    ctl: pd.DataFrame,
    syn: pd.DataFrame,
    config: AttackConfig,
    *,
    seed: int = 0,
    searches: int = SEARCHES,
) -> dict[str, Any]:
    """Anonymeter's singling out, both modes, averaged over the project's search seeds."""
    from anonymeter.evaluators import SinglingOutEvaluator
    from anonymeter.stats.confidence import EvaluationResults

    out: dict[str, Any] = {}
    for mode in ("univariate", "multivariate"):
        runs = []
        for s in search_seeds(seed, searches):
            ev = SinglingOutEvaluator(
                ori=ori,
                syn=syn,
                control=ctl,
                n_attacks=config.n_attacks,
                n_cols=config.n_cols,
                max_attempts=1_000_000,
                seed=s,
            )
            ev.evaluate(mode=mode)
            r = ev.results()
            # Anonymeter rescales the control count when deduplication leaves the target and
            # control sets different sizes, so the counts are kept as floats.
            runs.append((r.n_success, r.n_control, r.n_baseline, r.n_attacks_ori))
        n = runs[0][3]
        mean = [sum(float(x[i]) for x in runs) / len(runs) for i in range(3)]
        packed = pack(
            EvaluationResults(n_attacks=n, n_success=mean[0], n_baseline=mean[2], n_control=mean[1])
        )
        packed["searches"] = {
            "seeds": search_seeds(seed, searches),
            "main": [float(x[0]) for x in runs],
            "control": [float(x[1]) for x in runs],
            "baseline": [float(x[2]) for x in runs],
        }
        out[f"singling_out_{mode}"] = packed
    return out


def anonymeter_all(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    config: AttackConfig,
    *,
    seed: int = 0,
    searches: int = SEARCHES,
) -> dict[str, Any]:
    from anonymeter.evaluators import InferenceEvaluator, LinkabilityEvaluator

    labels = [config.secret]
    ori = for_anonymeter(targets, domain, labels)
    ctl = for_anonymeter(control, domain, labels)
    syn = for_anonymeter(synthetic, domain, labels)
    n = config.n_attacks
    out = anonymeter_singling_out(ori, ctl, syn, config, seed=seed, searches=searches)
    for k in config.k_values:
        lk = LinkabilityEvaluator(
            ori=ori,
            syn=syn,
            control=ctl,
            n_attacks=n,
            aux_cols=(list(config.half_a), list(config.half_b)),
            n_neighbors=k,
        )
        lk.evaluate(n_jobs=N_JOBS)
        out[f"linkability_k{k}"] = pack(lk.results())
    aux = [c for c in domain.names if c != config.secret]
    inf = InferenceEvaluator(
        ori=ori, syn=syn, control=ctl, aux_cols=aux, secret=config.secret, n_attacks=n
    )
    inf.evaluate(n_jobs=N_JOBS)
    out["inference"] = pack(inf.results())
    return out
