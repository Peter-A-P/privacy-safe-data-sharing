"""TabDDPM fitted and sampled by synthcity, one table per call (PLAN.md section 2.11).

Runs in the synthcity environment (Python 3.12, `envs/synthcity-requirements.txt`), not the
project's: synthcity cannot be installed on Python 3.13. `facsimile/synth/tabddpm.py` calls it
in a subprocess with the training codes on disk and reads back the table and a record. This
script does no more than the library does: synthcity's defaults, a seed, a device. Mapping the
output back into the domain is the caller's, so that it is typed and tested with the package.

What the library does with integer codes, read from synthcity 0.2.12 on 2026-10-28: a column
with at most 10 distinct values in the training data is categorical and gets multinomial
diffusion; every other column is quantile-transformed and gets Gaussian diffusion, and comes
back as a float. The record names the columns on each side (`discrete_columns`).

    .venv-synthcity/Scripts/python envs/synthcity_tabddpm.py TRAIN_PARQUET OUT_DIR SEED N
"""

from __future__ import annotations

import inspect
import json
import random
import sys
import time
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from synthcity.plugins import Plugins
from synthcity.plugins.core.dataloader import GenericDataLoader
from synthcity.utils.dataframe import discrete_columns


def main(train_path: str, out_dir: str, seed: int, n: int) -> None:
    train = pd.read_parquet(train_path)
    out = Path(out_dir)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if device == "cuda":
        torch.cuda.manual_seed_all(seed)
    plugin = Plugins().get(
        "ddpm", random_state=seed, device=torch.device(device), workspace=out / "workspace"
    )
    started = time.perf_counter()
    plugin.fit(GenericDataLoader(train))
    fit_seconds = time.perf_counter() - started

    torch.manual_seed(seed + 1_000_003)
    np.random.seed(seed + 1_000_003)
    started = time.perf_counter()
    table = plugin.generate(count=n).dataframe()
    sample_seconds = time.perf_counter() - started

    table.to_parquet(out / "table.parquet", index=False)
    record = {
        "library_version": metadata.version("synthcity"),
        "torch": metadata.version("torch"),
        "python": sys.version.split()[0],
        "plugin": "ddpm",
        # The defaults as the plugin's signature declares them; only seed, device and workspace
        # are passed.
        "params": {
            name: p.default
            for name, p in inspect.signature(type(plugin).__init__).parameters.items()
            if isinstance(p.default, (int, float, str, bool))
        },
        "discrete_columns": discrete_columns(train),
        "fit_seconds": fit_seconds,
        "sample_seconds": sample_seconds,
        "device": device,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
