"""The reference library on the same tables: Anonymeter (Giomi et al.'s own implementation).

Run on exactly the inputs the project's implementations get: the same targets, control and
synthetic table, the same secret, halves, number of attacks and predicate width. Categorical
attributes are handed over as their labels (Anonymeter compares them for equality) and binned
numeric ones as their bin codes (it scales them by their range and takes the absolute
difference), which is the distance `neighbours.py` uses. The secret is handed over as a label so
that Anonymeter scores an exact match, as the project does.

Anonymeter's licence is the Clear BSD licence; its authors hold a patent application on the
method (`docs/attacks.md`). TAPAS, the reference for the Groundhog attack, needs Python below
3.11 and runs in its own environment.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from facsimile.attacks.config import AttackConfig
from facsimile.prep import Domain


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


def anonymeter_all(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    config: AttackConfig,
    *,
    seed: int = 0,
) -> dict[str, Any]:
    from anonymeter.evaluators import InferenceEvaluator, LinkabilityEvaluator, SinglingOutEvaluator

    labels = [config.secret]
    ori = for_anonymeter(targets, domain, labels)
    ctl = for_anonymeter(control, domain, labels)
    syn = for_anonymeter(synthetic, domain, labels)
    n = config.n_attacks
    out: dict[str, Any] = {}

    def pack(ev: Any) -> dict[str, Any]:
        res = ev.results()
        risk = res.risk()
        return {
            "main": {"value": res.attack_rate.value, "error": res.attack_rate.error},
            "control": {"value": res.control_rate.value, "error": res.control_rate.error},
            "baseline": {"value": res.baseline_rate.value, "error": res.baseline_rate.error},
            "risk": {"value": risk.value, "lo": risk.ci[0], "hi": risk.ci[1]},
        }

    for mode in ("univariate", "multivariate"):
        ev = SinglingOutEvaluator(
            ori=ori,
            syn=syn,
            control=ctl,
            n_attacks=n,
            n_cols=config.n_cols,
            max_attempts=1_000_000,
            seed=seed,
        )
        ev.evaluate(mode=mode)
        out[f"singling_out_{mode}"] = pack(ev)
    for k in config.k_values:
        lk = LinkabilityEvaluator(
            ori=ori,
            syn=syn,
            control=ctl,
            n_attacks=n,
            aux_cols=(list(config.half_a), list(config.half_b)),
            n_neighbors=k,
        )
        lk.evaluate(n_jobs=-2)
        out[f"linkability_k{k}"] = pack(lk)
    aux = [c for c in domain.names if c != config.secret]
    inf = InferenceEvaluator(
        ori=ori, syn=syn, control=ctl, aux_cols=aux, secret=config.secret, n_attacks=n
    )
    inf.evaluate(n_jobs=-2)
    out["inference"] = pack(inf)
    return out
