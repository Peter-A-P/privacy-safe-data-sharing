"""Seven synthesisers behind one interface (`base.Wrapped`), the grid that runs them, and the four
methods of the leakage ladder beside it (`ladder.py`, PLAN.md section 2.10)."""

from __future__ import annotations

from typing import Final

from facsimile.synth.base import Wrapped

EPSILONS: Final = (0.5, 1.0, 2.0, 4.0, 8.0)
"""PLAN.md section 2.2; the non-DP methods sit at epsilon infinity."""

GRID: Final = ("copula", "ctgan", "tvae", "tabddpm", "aim", "mst", "pate_ctgan")
"""TabDDPM, the diffusion model, added 2026-10-29 (PLAN.md section 2.11)."""
LADDER: Final = ("perturb", "smote", "kanon", "tvae_overfit")
"""The positive controls: reported beside the grid, never on its surface or in its gate."""


def methods() -> dict[str, Wrapped]:
    from facsimile.synth import aim, copula, ctgan, ladder, mst, pate_ctgan, tabddpm, tvae

    return {
        m.name: m
        for m in (
            copula.METHOD,
            ctgan.METHOD,
            tvae.METHOD,
            tabddpm.METHOD,
            aim.METHOD,
            mst.METHOD,
            pate_ctgan.METHOD,
            ladder.PERTURB_METHOD,
            ladder.SMOTE_METHOD,
            ladder.KANON_METHOD,
            ladder.TVAE_OVERFIT_METHOD,
        )
    }
