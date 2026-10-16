"""Inference risk (Giomi et al. 2023, section 4.3): learn a secret attribute from the rest.

The attacker knows a target's auxiliary attributes and wants its secret one. For each target the
attacker finds the closest synthetic record on the auxiliary attributes and guesses its secret.
The main attack runs on the targets (fitted on), the control attack on the control records
(never seen); the baseline guesses the secret of a synthetic record drawn at random, which uses
the synthetic table's marginal and nothing about the target. A guess is right when the code
matches exactly: every secret here is a category or a bin.

Success on the control set is what the synthetic table teaches anyone about people like the
target, which is the table being useful. Only the excess on the targets is about the targets.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from facsimile.attacks.neighbours import nearest
from facsimile.attacks.risk import AttackResult, result
from facsimile.prep import Domain


def correct_guesses(
    records: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    aux: Sequence[str],
    secret: str,
    rng: np.random.Generator,
) -> np.ndarray:
    idx, _ = nearest(records, synthetic, domain, aux, k=1, rng=rng)
    guesses = synthetic[secret].to_numpy()[idx[:, 0]]
    correct: np.ndarray = guesses == records[secret].to_numpy()
    return correct


def inference(
    targets: pd.DataFrame,
    control: pd.DataFrame,
    synthetic: pd.DataFrame,
    domain: Domain,
    *,
    secret: str,
    aux: Sequence[str] | None = None,
    seed: int = 0,
) -> AttackResult:
    if len(targets) != len(control):
        raise ValueError(
            "the target and control sets must be the same size for the rates to compare"
        )
    aux = list(aux) if aux is not None else [c for c in domain.names if c != secret]
    if secret in aux:
        raise ValueError("the secret cannot be one of the attacker's auxiliary attributes")
    rng = np.random.default_rng(seed)
    n = len(targets)
    main = correct_guesses(targets, synthetic, domain, aux, secret, rng)
    ctrl = correct_guesses(control, synthetic, domain, aux, secret, rng)
    naive = synthetic[secret].to_numpy()[rng.integers(0, len(synthetic), n)]
    base = naive == targets[secret].to_numpy()
    return result(
        "inference",
        n,
        float(main.sum()),
        float(ctrl.sum()),
        float(base.sum()),
        {"secret": secret, "aux": aux, "seed": seed},
    )
