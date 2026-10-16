# Working notes for Claude Code

This repository is Share the Data, Not the People, package `facsimile`: synthetic
versions of three public datasets of real people, generated six ways with and without
differential privacy, attacked with the three criteria regulators use to judge anonymity and
with membership inference, and measured for usefulness as train-on-synthetic, test-on-real.
The plan is in [PLAN.md](PLAN.md); the diagrams in [docs/architecture.md](docs/architecture.md).
Status: week 1 in progress (datasets built, synthesiser grid running).

## Read first

- [README.md](README.md): what this is and, once there are any, the result tables.
- [PLAN.md](PLAN.md): the design. Do not deviate from it silently; if something in it turns
  out wrong, change the plan in the same commit as the code and say why in the commit
  message.
- `docs/data.md`, `docs/synthesisers.md` and `docs/attacks.md` once it exists: the terms as
  quoted, the library versions and accountants, and the attack implementations beside their
  papers.

## Running it

- `uv sync --all-extras` (CUDA torch on Windows, CPU elsewhere; `link-mode = "copy"` because the
  working copy is in OneDrive).
- IEEE-CIS is never downloaded by this project: set `FACSIMILE_IEEE_CIS_DIR` to the extracted
  competition folder (on the build desktop, `../09-realtime-risk-platform/data/raw/ieee-fraud-detection`).
- `facsimile data fetch all`, `facsimile build all`, `facsimile grid all` (resumable; one process
  per cell; `--status` to see progress). Rows land in `data/`, records in `results/`.

## Engineering standard

- Python 3.13. Typed throughout; `mypy --strict` and `ruff` clean in CI.
- Tests that fail meaningfully: the attack sanity pair (a copied table scores maximum risk,
  an independent one scores control-level), the three-way split, the accountant check, the
  bootstrap arithmetic.
- `pyproject.toml` with pinned major versions and a comment saying why for each pin.
- Docs ship in the same commit as the change.
- Never commit credentials, Kaggle tokens, or anything from `.env`.

## Rules specific to this repository

- **Attacks stay inside the dataset.** No outside data is ever joined to a record and no
  record is ever named. Singling out, linkability and inference are measured against the
  dataset's own control set and stop there. The Census terms are quoted beside this rule.
- **No hand-rolled differential privacy.** Every epsilon comes from a library's accountant,
  named with its version in `docs/synthesisers.md`.
- **Every attack is implemented from its paper and checked against the reference library**
  on the same tables. A disagreement is resolved and recorded before a number ships.
- **Utility is train-on-synthetic, test-on-real.** Fidelity scores are reported as fidelity,
  never as utility.
- **A leak is named precisely**: library, version, configuration, measurement, as a property
  of those settings on this data. No adjectives.
- **Nothing raw is committed.** Loaders fetch and verify checksums; terms are quoted in
  `docs/data.md` before the first fetch; a dataset whose terms do not permit the use is
  dropped, not bent.
- **Every reported number carries a confidence interval**, and every timing names its
  hardware.
- **Plain punctuation** in everything written here: no em-dashes or other typographic dashes,
  straight quotes only.

## What goes in the README

The README opens with the one-liner, the results tables and the honest limitation, before any
installation instructions. The report command fills the tables; do not hand-edit them. Record
one approach that was tried and rejected, with the evidence, once the work has produced it.
