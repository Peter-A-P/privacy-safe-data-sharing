"""The leakage ladder (PLAN.md section 2.10): four ways people make "synthetic" or "anonymised"
data that are expected to leak, run through the same pipeline as the grid as its positive controls.

None of them is a recommendation. They are here so that the attacks can be seen to catch what they
should, which is what makes a result at control level on the grid mean something. Their settings
are fixed in PLAN.md and were written down before any of them was run.

- `perturb`: the training records themselves, with noise on the binned numeric attributes and
  values swapped between records on the categorical ones, the classic perturbative release of
  statistical disclosure control.
- `smote`: SMOTE-NC (Chawla et al., JAIR 2002, section 6.1) used as a generator. Each record is
  interpolated between a real record and one of its k nearest real neighbours.
- `kanon`: k-anonymity by Mondrian partitioning (LeFevre, DeWitt and Ramakrishnan, ICDE 2006),
  every attribute but the secret generalised, the secret released as is.
- `tvae_overfit`: the grid's TVAE, trained ten times longer than SDV's default.

The first three are implemented here, from their papers, because no maintained library does
exactly this in the coded domain. None of them involves differential privacy, so the rule against
hand-rolled privacy mechanisms is not touched.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.attacks.config import CONFIGS
from facsimile.attacks.neighbours import nearest
from facsimile.prep import Domain
from facsimile.synth.base import Fitted, Timer, Wrapped
from facsimile.synth.sdv_common import fit_sample

PERTURB = {"numeric_noise_sd_bins": 1.0, "categorical_swap_share": 0.10}
SMOTE = {"k": 5}
KANON = {"k": 5}
TVAE_OVERFIT: dict[str, Any] = {"epochs": 3000, "batch_size": 500, "enable_gpu": True}


def _fitted(table: pd.DataFrame, params: dict[str, Any], seconds: float) -> Fitted:
    return Fitted(
        table=table,
        params={"library": "facsimile", **params},
        accounting={"dp": False, "epsilon": "inf"},
        fit_seconds=seconds,
        sample_seconds=0.0,
        device="cpu",
    )


def secret_of(domain: Domain) -> str:
    """The attribute the inference attack guesses, which k-anonymity releases as is. Found from
    the attack configuration of the dataset whose columns these are."""
    names = set(domain.names)
    for cfg in CONFIGS.values():
        if cfg.secret in names and set(cfg.half_a) | set(cfg.half_b) <= names:
            return cfg.secret
    raise ValueError("no attack configuration matches this domain's columns")


# ------------------------------------------------------------------ 1. the perturbed copy


def perturb(
    train: pd.DataFrame, domain: Domain, seed: int, n: int, *, noise_sd: float, swap: float
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = rng.permutation(len(train))
    if n > len(train):
        rows = np.concatenate([rows, rng.choice(len(train), n - len(train))])
    out = train.iloc[rows[:n]].reset_index(drop=True).copy()
    for col in domain.columns:
        values = out[col.name].to_numpy(dtype=np.int64)
        if col.kind == "numeric":
            noisy = np.rint(values + rng.normal(0.0, noise_sd, len(values))).astype(np.int64)
            out[col.name] = np.clip(noisy, 0, col.size - 1)
        else:
            chosen = np.flatnonzero(rng.random(len(values)) < swap)
            partners = rng.permutation(chosen)
            swapped = values.copy()
            swapped[chosen] = values[partners]
            out[col.name] = swapped
    return out


def _perturb(train: pd.DataFrame, domain: Domain, seed: int, eps: float | None, n: int) -> Fitted:
    with Timer() as t:
        table = perturb(
            train,
            domain,
            seed,
            n,
            noise_sd=PERTURB["numeric_noise_sd_bins"],
            swap=PERTURB["categorical_swap_share"],
        )
    return _fitted(table, PERTURB, t.seconds)


# ------------------------------------------------------------------ 2. SMOTE-NC


def smote(train: pd.DataFrame, domain: Domain, seed: int, n: int, *, k: int) -> pd.DataFrame:
    """SMOTE-NC as a generator. For each new record: a real record drawn at random, one of its k
    nearest real neighbours drawn at random; numeric attributes at a uniform point between the
    two, rounded to a bin; each categorical attribute the most frequent value among the k
    neighbours, ties broken at random. Distance is the project's mixed-type one
    (`attacks/neighbours.py`) rather than the paper's Euclidean distance with a median-variance
    penalty, so that the generator and the attacks see the same geometry."""
    rng = np.random.default_rng(seed)
    real = train.reset_index(drop=True)
    idx, _ = nearest(real, real, domain, domain.names, k=k + 1, rng=rng)
    # Drop each record itself; where duplicates hid it, drop the farthest instead.
    own = np.arange(len(real))[:, None]
    keep = idx != own
    first = np.where(keep.all(axis=1), k, keep.argmin(axis=1))
    mask = np.ones_like(idx, dtype=bool)
    mask[np.arange(len(real)), first] = False
    neighbours = idx[mask].reshape(len(real), k)

    base = rng.integers(0, len(real), n)
    partner = neighbours[base, rng.integers(0, k, n)]
    codes = real[domain.names].to_numpy(dtype=np.int64)
    out = np.empty((n, len(domain.names)), dtype=np.int64)
    gap = rng.random(n)
    for j, col in enumerate(domain.columns):
        if col.kind == "numeric":
            a, b = codes[base, j], codes[partner, j]
            out[:, j] = np.clip(np.rint(a + gap * (b - a)), 0, col.size - 1)
        else:
            votes = codes[neighbours[base], j]  # n x k
            counts = np.stack([(votes == v).sum(axis=1) for v in range(col.size)], axis=1)
            counts = counts + rng.random(counts.shape) * 0.5  # random tie-break
            out[:, j] = counts.argmax(axis=1)
    return pd.DataFrame(out, columns=domain.names)


def _smote(train: pd.DataFrame, domain: Domain, seed: int, eps: float | None, n: int) -> Fitted:
    with Timer() as t:
        table = smote(train, domain, seed, n, k=SMOTE["k"])
    return _fitted(table, {**SMOTE, "distance": "mixed-type (Gower), as the attacks"}, t.seconds)


# ------------------------------------------------------------------ 3. k-anonymity


def _spread(values: NDArray[np.int64], size: int, numeric: bool) -> float:
    """How wide a partition is on one attribute, on a common scale: the range over the domain's
    range for a binned attribute, the distinct values over the domain's for a categorical one."""
    if numeric:
        return float(values.max() - values.min()) / max(size - 1, 1)
    return float(len(np.unique(values)) - 1) / max(size - 1, 1)


def mondrian(
    codes: NDArray[np.int64], numeric: list[bool], sizes: list[int], k: int
) -> list[NDArray[np.int64]]:
    """Strict Mondrian: split the widest attribute at its median while both halves keep at least
    k records, until no attribute can be split. Categorical codes are split in code order, the
    form of Mondrian that needs no generalisation hierarchy. Returns the partitions' row indices."""
    done: list[NDArray[np.int64]] = []
    todo = [np.arange(len(codes))]
    while todo:
        part = todo.pop()
        sub = codes[part]
        order = sorted(
            range(codes.shape[1]),
            key=lambda j: -_spread(sub[:, j], sizes[j], numeric[j]),
        )
        for j in order:
            col = sub[:, j]
            median = np.median(col)
            left = col < median if (col < median).sum() >= k else col <= median
            if left.sum() >= k and (~left).sum() >= k:
                todo += [part[left], part[~left]]
                break
        else:
            done.append(part)
    return done


def kanon(
    train: pd.DataFrame, domain: Domain, seed: int, n: int, *, k: int, secret: str | None = None
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    secret = secret or secret_of(domain)
    quasi = [c for c in domain.columns if c.name != secret]
    real = train.reset_index(drop=True)
    codes = real[[c.name for c in quasi]].to_numpy(dtype=np.int64)
    numeric = [c.kind == "numeric" for c in quasi]
    recoded = codes.copy()
    for part in mondrian(codes, numeric, [c.size for c in quasi], k):
        for j, col in enumerate(quasi):
            values = codes[part, j]
            if numeric[j]:
                recoded[part, j] = int(np.floor(np.median(values)))
            else:
                counts = np.bincount(values, minlength=col.size)
                recoded[part, j] = int(rng.choice(np.flatnonzero(counts == counts.max())))
    out = real.copy()
    for j, col in enumerate(quasi):
        out[col.name] = recoded[:, j]
    rows = rng.permutation(len(out))
    if n > len(out):
        rows = np.concatenate([rows, rng.choice(len(out), n - len(out))])
    return out.iloc[rows[:n]].reset_index(drop=True)


def _kanon(train: pd.DataFrame, domain: Domain, seed: int, eps: float | None, n: int) -> Fitted:
    with Timer() as t:
        table = kanon(train, domain, seed, n, k=KANON["k"])
    params = {
        **KANON,
        "quasi_identifiers": "every attribute but the secret",
        "secret": secret_of(domain),
    }
    return _fitted(table, params, t.seconds)


# ------------------------------------------------------------------ 4. the overfitted TVAE


def _tvae_overfit(
    train: pd.DataFrame, domain: Domain, seed: int, eps: float | None, n: int
) -> Fitted:
    from sdv.single_table import TVAESynthesizer

    return fit_sample(
        lambda md: TVAESynthesizer(md, **TVAE_OVERFIT), TVAE_OVERFIT, train, domain, seed, n
    )


PERTURB_METHOD = Wrapped("perturb", "facsimile", "non-dp perturbation", _perturb)
SMOTE_METHOD = Wrapped("smote", "facsimile", "non-dp interpolation", _smote)
KANON_METHOD = Wrapped("kanon", "facsimile", "non-dp generalisation", _kanon)
TVAE_OVERFIT_METHOD = Wrapped("tvae_overfit", "sdv", "non-dp deep", _tvae_overfit)
