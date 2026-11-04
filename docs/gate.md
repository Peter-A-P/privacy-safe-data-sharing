# Through the 03 gate

PLAN.md section 1 asks whether "as good as the real thing" holds for the configuration the
recommendation rule picks. The rule picked none: no synthesiser at any budget comes within 0.02
AUC of the real-data ceiling on every task. So the gate was run on the nearest configurations
instead, chosen by a rule written down before it ran (`facsimile/gate.py`):

- per dataset, the configuration nearest the ceiling on its worst task, over all the grid's
  synthesisers;
- per dataset, the same over the differentially private configurations only;
- each on all three seeds of its table.

The candidates were TVAE (ACS, IEEE-CIS) and CTGAN (SPARCS) without privacy, and AIM at epsilon 1
(ACS) and epsilon 2 (IEEE-CIS, SPARCS). TabDDPM joined the grid on 2026-10-29 (PLAN.md section
2.11) and is now the nearest without privacy on all three datasets; it was put through the gate
the same day, and the earlier candidates are kept beside it. The ACS pick at epsilon 1 is the configuration where the
inference attack detects a risk; the gate is about usefulness and does not see that.

## What the gate is asked

Project 03's release gate decides whether a candidate is non-inferior to a baseline: a paired
bootstrap over items, a margin, Holm's adjustment across suites, and a power screen
(`docs/gate-statistics.md` in 03). It grades nothing. This project writes one side file per side
through 03's `outcomes_file` adapter, and the gate decides on them.

- **Baseline:** LightGBM trained on the real training split, the ceiling of the utility tables.
- **Candidate:** the same model, the same parameters and seed, trained on the synthetic table.
- **Suites:** the dataset's tasks (income and employment on ACS, fraud on IEEE-CIS, long stay
  and high charge on SPARCS).
- **Margin:** 2 points, the recommendation rule's 0.02 AUC.

**The item.** The gate counts correct items, and utility here is ROC AUC: the probability that a
model scores a random positive record above a random negative one. So an item is a pair of real
test records, one positive and one negative, and it is correct when the model scores the positive
higher. The share of items correct is then an unbiased estimate of the AUC. The pairs are
disjoint, with no record in two of them, so the items are independent and the gate's bootstrap
over items is valid. There are as many pairs as the smaller class has records, in an order fixed
by a seed. A pair a model scores level is ungradeable for that side, and the gate drops it from
both. An item is named by its index alone, never by a record.

## What it decided

| Dataset | Candidate | Gate, three seeds | Worst-task gap, AUC points |
|---|---|---|---|
| ACS | TabDDPM, no privacy | block, 3 of 3 | -2.7 to -1.3 |
| ACS | TVAE, no privacy | block, 3 of 3 | -6.2 to -5.1 |
| ACS | AIM, epsilon 1 | block, 3 of 3 | -22.9 to -12.5 |
| IEEE-CIS | TabDDPM, no privacy | not decided, 3 of 3 | -8.4 to -6.0 |
| IEEE-CIS | TVAE, no privacy | not decided, 3 of 3 | -17.4 to -8.4 |
| IEEE-CIS | AIM, epsilon 2 | not decided, 3 of 3 | -18.9 to -12.3 |
| SPARCS | TabDDPM, no privacy | block, 3 of 3 | -2.3 to -1.1 |
| SPARCS | CTGAN, no privacy | block, 3 of 3 | -7.6 to -7.0 |
| SPARCS | AIM, epsilon 2 | block, 3 of 3 | -17.1 to -13.8 |

Every task, seed and interval is in [results.md](results.md#through-the-03-gate-synthetic-trained-against-real-trained).
The README table is filled from the same file by `facsimile report`.

**On ACS and SPARCS the gate blocks every candidate on every seed.** TVAE and CTGAN leave a model
5 to 8 AUC points worse than one trained on the real data, and the best differentially private
table 13 to 23 points worse; on every seed the worst task's whole interval lies below minus 2
points. TabDDPM comes closest: 1.1 to 2.7 points worse, with lower bounds from -1.9 to -3.8 and upper
bounds from -0.1 to -1.6. On every seed at least one task's interval reaches below -2 points, so
non-inferiority is not shown and the gate blocks it too. Two intervals clear the margin, both
SPARCS high charge (seeds 0 and 1, lower bounds -1.97 and -1.92), and the other task on the same
seed does not.

**On IEEE-CIS the gate declines to decide.** The test split holds 333 fraud cases, so there are
333 pairs. Project 03's power screen asks for at least 370 items to see a two-point drop at 80%
power, so it warns instead of deciding, and its decision line reads "pass: 0 of 1 suites
decided". This project reports that as *not decided*, never as a pass. The intervals themselves,
from -24.0 to -13.5 at the lowest to -10.2 to -2.1 at the highest (TabDDPM, seed 2), lie wholly below the margin. A gate that
reasoned from the interval alone would block. 03 makes the power screen a rule because a suite
too small to see the margin can also pass by chance, and that rule holds here too.

So the gate agrees with the recommendation rule, on a different statistic and with its own test:
no synthetic table here is as good as the real data for training these models.

## At other margins: the sweep

Added 2026-11-03, after the results, for the site's margin slider and the README's 5-point
column. The same side files, unchanged, were decided again by the same gate at every whole-point
margin from 1 to 20: 540 decisions, one ledger per margin under `gate-runs/sweep/`. Only the
spec's margin and name change, so each verdict carries the gate's own Holm adjustment and power
screen at that margin. The 2-point sweep reproduces all 27 decisions above exactly.

At 5 points the gate passes TabDDPM without privacy on ACS and on SPARCS, on all three seeds, and
blocks the other seven candidates on every seed. The card data is decided at 5 points, because a
wider margin needs fewer pairs, and every card candidate is blocked. Nothing with a privacy
guarantee passes on any seed below 15 points. These are what-ifs; the 2-point decisions stay the result.

## A defect in the gate, found on the way

McNemar's exact test, which the gate computes beside its verdict, divided by `float(2**n)`. That
overflows once more than 1,023 items are discordant, and the AIM candidates have 1,035 to 1,633
(ACS employment, SPARCS high charge).
The comparison stopped with an `OverflowError`. It was fixed in 03 (commit `a3c8691`, with a test)
by dividing the integers directly, and every decision here was made with the fixed gate: version
0.1.0 at that commit.

## Running it again

```bash
facsimile gate export   # the spec and both side files per run, under gate-runs/
facsimile gate run      # project 03's gate on each, then results/gate.json from the ledger
facsimile gate sweep    # the same runs at 1 to 20 points (or name the margins), resumable
facsimile report
```

`gate run` calls `uv run --no-sync gate compare` in a checkout of 03, by default
`../03-ai-release-gate` or wherever `FACSIMILE_GATE_DIR` points. Each decision goes to this
repository's own ledger, `gate-runs/ledger.jsonl`, which names both side files by their SHA-256.
The gate exits 1 on a block and on a crash alike, so a run counts only when it appended its
record.
