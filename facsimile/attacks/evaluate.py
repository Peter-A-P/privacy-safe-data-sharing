"""The attacks on any real and synthetic pair: one call, raw tables in, risks with intervals out.

    from facsimile.attacks.evaluate import evaluate
    result = evaluate(targets, control, synthetic, secret="income")
    print(result.markdown())

`targets` are real records the synthesiser was trained on, `control` real records from the same
population that it never saw, the same number of each, and `synthetic` the table under test.
That is all the attacks need; nothing outside the three tables is ever used. Each attack is run
against the targets and, identically, against the control, and the risk is the excess success
on the targets (Giomi et al., PoPETs 2023), so a table that is merely useful about everyone
scores zero.

The tables can be raw. Columns are coded the way this project codes its datasets
(`facsimile/prep.py`): categories rarer than half a percent merge into OTHER, numeric columns
fall into uniform bins. With no `columns` given, a numeric column with more than 20 distinct
values is binned into 10 between the control's minimum and maximum, and every other column is
categorical. The categories and bounds are read from the control set, never from the targets,
so the coding says nothing about the people the attacks are asking about. Pass `columns`
(`prep.Categorical`, `prep.Numeric`) to fix the coding from a codebook instead.

    facsimile evaluate TARGETS CONTROL SYNTHETIC --secret COLUMN [--out result.json]

reads CSV or Parquet files and prints the same table.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from facsimile.attacks.dcr import dcr
from facsimile.attacks.inference import inference
from facsimile.attacks.linkability import linkability
from facsimile.attacks.risk import AttackResult
from facsimile.attacks.singling_out import singling_out
from facsimile.prep import Categorical, ColumnSpec, Domain, Numeric, encode, fit_domain

NUMERIC_DISTINCT = 20
NUMERIC_BINS = 10

NAMES = {
    "singling_out_univariate": "singling out, univariate",
    "singling_out_multivariate": "singling out, multivariate",
    "inference": "inference",
}


def label(name: str) -> str:
    if name.startswith("linkability_k"):
        k = int(name.removeprefix("linkability_k"))
        return f"linkability, {k} neighbour{'s' if k > 1 else ''}"
    return NAMES.get(name, name.replace("_", " "))


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Every attack's result on one synthetic table, and the coding they were run in."""

    attacks: dict[str, AttackResult]
    dcr: dict[str, Any]
    domain: Domain
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def detected(self) -> list[str]:
        return [name for name, r in self.attacks.items() if r.risk.detected]

    def as_dict(self) -> dict[str, Any]:
        return {
            "attacks": {name: r.as_dict() for name, r in self.attacks.items()},
            "dcr": self.dcr,
            "detected": self.detected,
            "params": self.params,
            "domain": self.domain.to_json(),
        }

    def markdown(self) -> str:
        rows = [
            "| Attack | Success on targets, % | Success on control, % | Risk, % (95% CI) | Detected |",
            "|---|---|---|---|---|",
        ]
        for name, r in self.attacks.items():
            risk = r.risk
            rows.append(
                f"| {label(name)} | {100 * r.main.value:.1f} | "
                f"{100 * r.control.value:.1f} | {100 * risk.value:.1f} ({100 * risk.lo:.1f} to "
                f"{100 * risk.hi:.1f}) | {'yes' if risk.detected else 'no'} |"
            )
        return "\n".join(rows)


def infer_columns(control: pd.DataFrame) -> list[ColumnSpec]:
    """A coding read from the control set alone: wide numeric columns binned, the rest categorical."""
    specs: list[ColumnSpec] = []
    for name in control.columns:
        col = control[name]
        nullable = bool(col.isna().any())
        if pd.api.types.is_numeric_dtype(col) and col.nunique() > NUMERIC_DISTINCT:
            lo, hi = float(col.min()), float(col.max())
            specs.append(Numeric(str(name), lo=lo, hi=hi, bins=NUMERIC_BINS, nullable=nullable))
        else:
            specs.append(Categorical(str(name), nullable=nullable))
    return specs


def _halves(names: Sequence[str]) -> tuple[list[str], list[str]]:
    return list(names[0::2]), list(names[1::2])


def evaluate(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    *,
    secret: str,
    columns: Sequence[ColumnSpec] | None = None,
    link_a: Sequence[str] | None = None,
    link_b: Sequence[str] | None = None,
    n_attacks: int = 2000,
    n_cols: int = 3,
    k_values: Sequence[int] = (1, 10),
    seed: int = 0,
) -> Evaluation:
    """Singling out (both modes), linkability at each k, inference of `secret`, and distance to
    closest record, all against the control set.

    `link_a` and `link_b` are the two halves of the linkability attack, the attributes an
    attacker holds in two separate sources; by default the columns other than the secret,
    alternately. The number of singling-out and inference attacks is capped at the number of
    targets."""
    if len(targets) != len(control):
        raise ValueError(
            f"targets ({len(targets)}) and control ({len(control)}) must be the same size: the "
            "risk compares their success rates"
        )
    missing = [c for c in targets.columns if c not in synthetic.columns or c not in control.columns]
    if missing:
        raise ValueError(f"columns missing from the control or synthetic table: {missing}")
    if secret not in targets.columns:
        raise ValueError(f"the secret {secret!r} is not a column")
    specs = list(columns) if columns is not None else infer_columns(control[targets.columns])
    domain = fit_domain(specs, control)
    names = domain.names
    t, c, s = (
        encode(frame[names], domain).reset_index(drop=True)
        for frame in (targets, control, synthetic)
    )
    if link_a is None or link_b is None:
        link_a, link_b = _halves([n for n in names if n != secret])
    n = min(n_attacks, len(t))
    attacks: dict[str, AttackResult] = {}
    for mode in ("univariate", "multivariate"):
        r = singling_out(t, c, s, domain, mode=mode, n_attacks=n, n_cols=n_cols, seed=seed)
        attacks[r.attack] = r
    for k in k_values:
        attacks[f"linkability_k{k}"] = linkability(
            t, c, s, domain, a=list(link_a), b=list(link_b), k=k, seed=seed
        )
    attacks["inference"] = inference(t, c, s, domain, secret=secret, seed=seed)
    params = {
        "secret": secret,
        "link_a": list(link_a),
        "link_b": list(link_b),
        "n_attacks": n,
        "n_cols": n_cols,
        "k_values": list(k_values),
        "seed": seed,
        "columns_inferred": columns is None,
    }
    return Evaluation(
        attacks, dcr(t, c, s, domain, seed=seed, sample=min(4000, len(s))), domain, params
    )
