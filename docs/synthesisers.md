# Synthesisers: versions, accountants, and what each library does with a budget

Six methods behind one interface (`facsimile/synth/base.py`): fit on the training split with a
seed and, where it applies, a budget; sample as many rows as the training split has. Every table
in the grid has a record under `results/<dataset>/synth/` with the versions, the hyperparameters
as passed, what the accountant says, the hash of the frame it was fitted on, wall-clock and the
hardware. **No epsilon in this project is computed by this project**: each comes from the
library's own accountant, observed as it runs (`facsimile/synth/accounting.py`).

## The six

| Arm | Method | Library and version | Licence | Accountant | Device |
|---|---|---|---|---|---|
| Non-DP, statistical | Gaussian copula | SDV 2.0.0 | Business Source License 1.1 (below) | none; epsilon infinity | CPU |
| Non-DP, deep | CTGAN | SDV 2.0.0 (ctgan 0.12.1) | BSL 1.1 | none; epsilon infinity | GPU |
| Non-DP, deep | TVAE | SDV 2.0.0 (ctgan 0.12.1) | BSL 1.1 | none; epsilon infinity | GPU |
| DP, marginal | AIM | smartnoise-synth 1.0.8 on Private-PGM (mbi 1.1.0) | MIT, Apache 2.0 | zCDP; rho from `snsynth.utils.cdp_rho` (OpenDP 0.14.2) | CPU |
| DP, marginal | MST | smartnoise-synth 1.0.8 on Private-PGM (mbi 1.1.0) | MIT, Apache 2.0 | zCDP; rho from `snsynth.utils.cdp_rho` (OpenDP 0.14.2) | CPU |
| DP, deep | PATE-CTGAN | smartnoise-synth 1.0.8 | MIT | PATE moments accountant, data-dependent | GPU |

Budgets: epsilon 0.5, 1, 2, 4 and 8 at delta 1e-5 for the three DP methods; the non-DP methods at
epsilon infinity; three seeds per cell. Hyperparameters are the libraries' defaults throughout,
recorded per table; the only ones set here are the device and the budget.

Hardware for every timing in this project unless a record says otherwise: a Windows 11 desktop,
Intel Core i5-10400F (6 cores, 12 threads), 16 GB of memory, NVIDIA GeForce GTX 1650 with 4 GB,
torch 2.14.1 built for CUDA 12.6; each table's record names it again (`hardware`). The grid runs
as two queues at once, the GPU methods one cell at a time and the CPU methods two at a time, so a
recorded wall-clock is the time under that shared load, not on an idle machine.

First timings, ACS, seed 0, one table each (2026-10-16): Gaussian copula 6 s, MST at epsilon 1
47 s, PATE-CTGAN at epsilon 1 25 s, TVAE 171 s, CTGAN 669 s, AIM at epsilon 1 1,724 s with
4.8 GB of memory. AIM is what sets the pace of the grid, as the benchmark said it would.

## One domain, and it spends no budget

Every method works on the same discrete domain (`facsimile/prep.py`): numeric columns binned
between public bounds fixed in each dataset's spec, uniform or uniform on a log scale for money,
and categories below half a percent merged into `OTHER`. The benchmark this plan follows
recommends exactly that preprocessing. Two decisions sit on top of it:

- **Category sets come from the test split**, which no synthesiser sees, and bin edges from the
  spec. A domain read off the training data is a disclosure about the training data that no
  accountant charges for. Closed codebooks (sex, the fraud label, marital status and the other
  ACS codes with a published list) are taken from the codebook and have no `OTHER`.
- **SmartNoise is handed a transformer already fitted to the domain.** Its default, given a list
  of categorical columns, fits a label encoder to the training data it is passed, which reads
  the category set off the protected records for free. A complete transformer is used as given
  (`snsynth.base.Synthesizer._get_train_data`), so `preprocessor_eps` is 0 and the whole budget
  goes to the method. `tests/test_accounting.py` checks that the epsilon reaching each accountant
  is the epsilon requested.

The SDV methods are given metadata declaring every column categorical, so they do not fit a
continuous distribution to a category index.

## What each accountant says, and how it is checked

**AIM and MST.** Both convert the requested (epsilon, delta) to a zero-concentrated DP budget
rho with `snsynth.utils.cdp_rho`, which binary-searches OpenDP's `make_zCDP_to_approxDP`
conversion of a Gaussian mechanism, and then spend rho on measurements. The record carries the
epsilon and delta passed to that call and the rho it returned, observed from the call itself.
The accountant test recomputes rho from the request with the pinned OpenDP for every published
DP record and fails if it differs, so a library upgrade that changes the conversion is caught
before a number moves.

**PATE-CTGAN.** PATE's moments accountant: after each student step the library adds an increment
per moment order l from `privacy_utils.moments_acc`, and reads epsilon off the running sum as
min over l of (alpha_l - log delta) / l. The record carries every increment the library
computed, summed, and that formula applied to the sum once training has finished.

### Three properties of PATE-CTGAN in smartnoise-synth 1.0.8

Read from the library's source on 2026-10-16 (`snsynth/pytorch/nn/patectgan.py`,
`privacy_utils.py`). Recorded, not patched: the project measures what the library does.

1. **The accountant is data-dependent.** Each increment depends on the teachers' vote counts on
   the generated batch, so the reported epsilon is itself computed from the training data. A
   data-dependent bound is a statement about this run, and releasing the number is not covered by
   it. The PATE papers handle this with smooth sensitivity; this implementation does not.
2. **The loop tests the budget before an iteration, not after it.** `while eps < self.epsilon`
   computes eps from the moments accumulated so far, then trains a full round of teachers and
   students. The last round can therefore carry the total past the target, and the finished model
   has consumed more than was asked for. Each record reports `epsilon_spent` (what the finished
   model consumed, by the library's own formula) and `overshoot` beside the request.
3. **The discriminator reseeds torch with 0.** `Discriminator.__init__` calls
   `torch.manual_seed(0)` and `torch.cuda.manual_seed(0)`, and a discriminator is built for each
   teacher and for the student after this project has set its seed. Whether three seeds produce
   three different tables is measured from the grid's table hashes, not assumed.

Each becomes a line in the leak table if, and only if, a measurement on these tables shows it.

## SDV's licence

SDV 2.0, ctgan and rdt are under the Business Source License 1.1, which is not an open-source
licence. Its additional use grant:

> You may make use of the Licensed Work, and derivatives of the Licensed Work, provided that you
> do not use the Licensed Work, or derivatives of the Licensed Work, for a Synthetic Data
> Service.

A "Synthetic Data Service" is defined there as a commercial offering that lets third parties use
the library's features. This project is a non-commercial measurement and offers no service, so
the grant covers it; `facsimile` depends on SDV and does not redistribute it.

## Versions pinned

`pyproject.toml` pins every major with a reason and `uv.lock` pins the exact build. The ones that
decide a number: smartnoise-synth 1.0.8, mbi 1.1.0, OpenDP 0.14.2, SDV 2.0.0, ctgan 0.12.1,
torch 2.14.1. SmartNoise caps opacus below 0.15, which pulls 0.14.0; PATE-CTGAN does not call it.
