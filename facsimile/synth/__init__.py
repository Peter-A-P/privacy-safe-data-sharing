"""Six synthesisers behind one interface (`base.Wrapped`), and the grid that runs them."""

from __future__ import annotations

from typing import Final

from facsimile.synth.base import Wrapped

EPSILONS: Final = (0.5, 1.0, 2.0, 4.0, 8.0)
"""PLAN.md section 2.2; the non-DP methods sit at epsilon infinity."""


def methods() -> dict[str, Wrapped]:
    from facsimile.synth import aim, copula, ctgan, mst, pate_ctgan, tvae

    return {
        m.name: m
        for m in (
            copula.METHOD,
            ctgan.METHOD,
            tvae.METHOD,
            aim.METHOD,
            mst.METHOD,
            pate_ctgan.METHOD,
        )
    }
