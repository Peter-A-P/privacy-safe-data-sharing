"""Nearest synthetic records under the paper's mixed-type distance, with ties broken at random.

The distance is the Gower-style one Giomi et al. use: for a categorical attribute 0 if equal and
1 if not; for a numeric one the absolute difference scaled to at most 1. Numeric attributes here
are bin codes, scaled by the domain's range (size minus one), which is data-independent.

**Ties.** In a binned domain many synthetic records sit at exactly the same distance from a
target, often zero. The paper does not say which of them the attacker takes; the reference
library takes whichever its sort puts first, which is an accident of memory order. Here ties are
broken uniformly at random, seeded, because an attacker has no information that prefers one tied
record to another. `docs/attacks.md` records what this changes against the reference.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from facsimile.prep import Domain

CHUNK = 64
JITTER = 1e-9
"""Below any difference two Gower distances on this domain can have (the smallest is 1/size)."""


def _arrays(
    frame: pd.DataFrame, domain: Domain, columns: Sequence[str]
) -> tuple[NDArray[np.int16], NDArray[np.float64], NDArray[np.bool_]]:
    values = frame[list(columns)].to_numpy(dtype=np.int16)
    scale = np.array(
        [1.0 / max(domain[c].size - 1, 1) if domain[c].kind == "numeric" else 1.0 for c in columns]
    )
    numeric = np.array([domain[c].kind == "numeric" for c in columns])
    return values, scale, numeric


def distances(
    queries: pd.DataFrame, candidates: pd.DataFrame, domain: Domain, columns: Sequence[str]
) -> NDArray[np.float64]:
    """The full query-by-candidate distance matrix. For small inputs and tests."""
    return np.vstack(list(_distance_chunks(queries, candidates, domain, columns)))


def _distance_chunks(
    queries: pd.DataFrame, candidates: pd.DataFrame, domain: Domain, columns: Sequence[str]
) -> Iterator[NDArray[np.float64]]:
    # Float64 throughout: a float32 sum of thirds and elevenths differs from an equal one by more
    # than the tie-breaking jitter, which would turn a random tie-break into a rounding one.
    q, scale, numeric = _arrays(queries, domain, columns)
    c64 = _arrays(candidates, domain, columns)[0].astype(np.float64)
    for start in range(0, len(q), CHUNK):
        diff = np.abs(q[start : start + CHUNK, None, :].astype(np.float64) - c64[None, :, :])
        per_col = np.where(numeric, diff * scale, diff > 0)
        yield per_col.sum(axis=2)


def nearest(
    queries: pd.DataFrame,
    candidates: pd.DataFrame,
    domain: Domain,
    columns: Sequence[str],
    *,
    k: int,
    rng: np.random.Generator,
) -> tuple[NDArray[np.int64], NDArray[np.float64]]:
    """For each query row, the positions of its k nearest candidates and their distances."""
    k = min(k, len(candidates))
    idx_out = np.empty((len(queries), k), dtype=np.int64)
    dist_out = np.empty((len(queries), k), dtype=np.float64)
    row = 0
    for block in _distance_chunks(queries, candidates, domain, columns):
        jittered = block + rng.random(block.shape) * JITTER
        part = np.argpartition(jittered, k - 1, axis=1)[:, :k]
        order = np.take_along_axis(jittered, part, axis=1).argsort(axis=1)
        chosen = np.take_along_axis(part, order, axis=1)
        n = len(block)
        idx_out[row : row + n] = chosen
        dist_out[row : row + n] = np.take_along_axis(block, chosen, axis=1)
        row += n
    return idx_out, dist_out
