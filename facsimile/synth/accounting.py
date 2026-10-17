"""What each library's accountant claims was spent, by version. Nothing here computes privacy.

CLAUDE.md: no hand-rolled differential privacy; every epsilon comes from a library's accountant.
This module only **observes** the libraries: it wraps the function each one calls to turn a
budget into noise, records the arguments and the result, and puts them in the table's record.
The accountant test (`tests/test_accounting.py`) then checks the record against the request.

- **AIM and MST** (smartnoise-synth): zero-concentrated DP. Each converts the requested
  (epsilon, delta) to a zCDP budget rho with `snsynth.utils.cdp_rho`, which binary-searches
  OpenDP's `make_zCDP_to_approxDP` conversion of a Gaussian mechanism, and then spends rho.
  Recorded: the rho the library computed, from the call itself.
- **PATE-CTGAN** (smartnoise-synth): PATE's moments accountant, written to depend on the
  teachers' votes; at the default noise_multiplier its clamp always binds, so in these runs it
  does not (docs/synthesisers.md). `snsynth.pytorch.nn.privacy_utils.moments_acc`, accumulated over training, with epsilon read
  off as min over orders l of (alpha_l - log delta) / l. Recorded: every increment the library
  computed, summed, and that formula applied to the sum. That formula is the library's own line
  (`patectgan.py`, the training loop's stopping test), applied once more after the loop ends,
  because the loop tests the budget before an iteration rather than after it: the epsilon the
  finished model consumed is the one after the last iteration, not the last one the loop saw.
"""

from __future__ import annotations

import contextlib
import importlib
import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any


def versions() -> dict[str, str]:
    out = {}
    for dist in ("smartnoise-synth", "opendp", "mbi", "sdv", "torch"):
        try:
            out[dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            out[dist] = "absent"
    return out


@dataclass
class Calls:
    """Every call a wrapped library function received, with what it returned."""

    args: list[tuple[Any, ...]] = field(default_factory=list)
    kwargs: list[dict[str, Any]] = field(default_factory=list)
    results: list[Any] = field(default_factory=list)


@contextlib.contextmanager
def observe(module_name: str, attr: str) -> Iterator[Calls]:
    """Wrap `module.attr` for the duration, recording calls; restore it afterwards."""
    module = importlib.import_module(module_name)
    original: Callable[..., Any] = getattr(module, attr)
    calls = Calls()

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        calls.args.append(args)
        calls.kwargs.append(kwargs)
        calls.results.append(result)
        return result

    setattr(module, attr, wrapper)
    try:
        yield calls
    finally:
        setattr(module, attr, original)


def zcdp_record(calls: Calls, *, epsilon: float, delta: float, method: str) -> dict[str, Any]:
    if len(calls.results) != 1:
        raise AssertionError(f"{method}: expected one cdp_rho call, saw {len(calls.results)}")
    (eps_arg, delta_arg), rho = calls.args[0][:2], float(calls.results[0])
    return {
        "dp": True,
        "accountant": "zCDP; rho from snsynth.utils.cdp_rho (OpenDP make_zCDP_to_approxDP, binary search)",
        "epsilon_requested": epsilon,
        "delta": delta,
        "epsilon_passed_to_accountant": float(eps_arg),
        "delta_passed_to_accountant": float(delta_arg),
        "rho": rho,
        "versions": versions(),
    }


def pate_epsilon(alphas: list[float], delta: float) -> float:
    """The library's stopping formula, min_l (alpha_l - log delta) / l, on the summed moments."""
    return min((a - math.log(delta)) / (i + 1) for i, a in enumerate(alphas))


def pate_record(
    calls: Calls, *, epsilon: float, delta: float, moments_order: int
) -> dict[str, Any]:
    if not calls.results:
        raise AssertionError("PATE-CTGAN: the moments accountant was never called")
    total = [0.0] * moments_order
    for increment in calls.results:
        values = [float(v) for v in increment.detach().cpu().tolist()]
        total = [t + v for t, v in zip(total, values, strict=True)]
    spent = pate_epsilon(total, delta)
    return {
        "dp": True,
        "accountant": "PATE moments accountant, data-dependent (snsynth.pytorch.nn.privacy_utils.moments_acc)",
        "epsilon_requested": epsilon,
        "delta": delta,
        "epsilon_spent": spent,
        "overshoot": spent - epsilon,
        "accountant_calls": len(calls.results),
        "moments_order": moments_order,
        "versions": versions(),
    }
