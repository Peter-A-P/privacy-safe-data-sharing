# Tried and rejected: distance to closest record as a privacy check

PLAN.md section 10 listed four approaches this project expected to reject. This page writes up
the one with the clearest evidence: using distance to closest record (DCR) to decide whether a
synthetic table is safe to release. DCR is the check most synthetic-data tools put in front of
their users. On these 51 configurations (three datasets, seven synthesisers, the budgets that were
run, three seeds each), it failed in both directions. It passed the one configuration an attack
broke, and it flagged eight configurations that no attack could break, seven of them carrying a
differential-privacy guarantee.

The numbers come from `results/report.json` (written by `facsimile report`) and
`results/<dataset>/dcr_null.json` (written by `facsimile dcr-null`). Both are computed from
the same tables, targets and control records the attacks use.

## What was tested

DCR is computed two ways, the two ways it is usually quoted (`facsimile/attacks/dcr.py`):

- **Closer-to-training share.** For each of 4,000 synthetic records, whether its nearest real
  record is one of the 2,000 training targets rather than one of the 2,000 control records the
  synthesiser never saw, ties split evenly. A table that knows nothing about its training rows
  scores one half. The usual check passes a table whose share is not above one half.
- **Exact-copy rate.** The share of targets with a synthetic record at distance zero, beside the
  same share for the control records.

The yardstick for the first is measured, not assumed. Real records the synthesisers never saw,
drawn from the test split, stand in for the synthetic table. They score 0.495 to 0.507 on ACS,
0.498 to 0.503 on IEEE-CIS and 0.505 to 0.512 on SPARCS (three draws each). So a share of one
half is what independence looks like on these targets and controls.

The check is read as it would be used: a configuration fails DCR when its closer-to-training
share's 95% interval lies above one half on all three seeds. It is set against the attacks'
verdict, which is the leak call of the README. That call pools the seeds and requires the risk's
interval, at the Bonferroni level, to exclude zero.

## What happened

**It passed the configuration an attack broke.** AIM at epsilon 1 on ACS (smartnoise-synth
1.0.8) is the one configuration in the grid where an attack detects a risk. The inference attack
recovers the income bracket of 23.4% of training records against 21.4% of control records, a
risk of 2.5% (0.7 to 4.4). Its closer-to-training share is 0.492, and every seed's interval
includes one half (the lowest lower bound is 0.467). Its exact-copy rates are 0.8% for targets
and 0.6% for control. By DCR it is the safest kind of table.

**It failed eight configurations no attack could break.** Each of these has a closer-to-training
share whose interval sits above one half on every seed:

| Dataset | Configuration | Closer-to-training share (lowest seed's lower bound) | Exact copies, targets vs control, % | Attacks |
|---|---|---|---|---|
| IEEE-CIS | MST, epsilon 0.5 | 0.558 (0.516) | 0.0 vs 0.1 | none detected |
| IEEE-CIS | MST, epsilon 1 | 0.542 (0.510) | 0.3 vs 0.3 | none detected |
| IEEE-CIS | MST, epsilon 2 | 0.535 (0.516) | 0.2 vs 0.3 | none detected |
| IEEE-CIS | MST, epsilon 4 | 0.538 (0.519) | 0.2 vs 0.2 | none detected |
| IEEE-CIS | MST, epsilon 8 | 0.540 (0.517) | 0.3 vs 0.4 | none detected |
| IEEE-CIS | PATE-CTGAN, epsilon 4 | 0.526 (0.508) | 0.3 vs 0.4 | none detected |
| ACS | PATE-CTGAN, epsilon 0.5 | 0.521 (0.503) | 0.0 vs 0.0 | none detected |
| SPARCS | TVAE, no privacy | 0.528 (0.505) | 0.0 vs 0.0 | none detected |

Seven of the eight are differentially private. MST at epsilon 0.5 is among the smallest budgets in
the grid, and its guarantee comes from the library's own accountant (`docs/synthesisers.md`). A
release gate built on DCR would have stopped every MST table on IEEE-CIS and passed the
configuration the attacks break.

**It passed the diffusion model too (added 2026-10-30).** TabDDPM on ACS (synthcity 0.2.12, no
privacy), added to the grid after this page was first written (PLAN.md section 2.11), is the
configuration where an attack detected a risk under the single-search singling out: 1.8% (0.7
to 2.9). Averaged over five searches (PLAN.md section 2.12, 2026-11-01) it is 0.6% (0.0 to 1.7)
and no longer detected, so it is not counted here as a configuration an attack breaks. Its
closer-to-training share is 0.504, and every seed's interval includes one half (the lowest
lower bound is 0.474). Its exact-copy rates are 6.4% for targets and 6.1% for control. DCR flags
no TabDDPM configuration on any dataset.

**The exact-copy rate separated nothing.** Across the 51 configurations the targets' exact-copy
rate never exceeds 6.4% (TabDDPM on ACS, against 6.1% for control). In every one it sits within half a percentage point of the control's, because
on binned and categorical attributes identical rows occur in the population. That holds for the
leak too (0.8% against 0.6%).

## Why

DCR measures how close synthetic records sit to training records. The risks the law names are
something else: whether a person can be isolated, linked or have an attribute inferred. The
inference that succeeds on AIM at epsilon 1 needs no synthetic record near any target. It needs
the synthetic table to keep the joint pattern between the other attributes and income a little
more faithfully for the training records than for anyone else. Nearest-neighbour distances do
not see that. In the other direction, a synthesiser that reproduces the training split's
population pattern places synthetic records slightly nearer the training split than an
independent sample of the same size would. Differential privacy permits this, because it bounds
what any one record changes, not how close the table is to the population. That would explain
why MST on IEEE-CIS fails DCR at every budget while no attack detects anything. The project did
not test this explanation further.

## Where it does work

On the leakage ladder (PLAN.md section 2.10, `docs/attacks.md`), DCR flags all nine tables of
the perturbed copy, SMOTE-NC and k-anonymity: every seed's interval sits above one half. It does
not flag the overfitted TVAE, which no attack catches on its full target sets either. So DCR
does catch copies and near-copies, which is the case it was designed for. The rejection stands
for the cases that matter here: tables that are not copies, where it flagged differentially
private ones no attack could break and passed the one that an attack broke.

## What the project does instead

DCR stays in the tables beside the attacks, labelled as what it is, so the comparison can be
checked. It is not used as a privacy measure anywhere in the recommendation rule, the leak table
or the explorer. The three criteria of Giomi et al., measured against a control set, and the
Groundhog membership inference attack are what the README calls risk.

## The other candidates

The other three candidates are in the README and `docs/results.md`.

- **Candidate 2, deep differentially private synthesis is competitive:** PATE-CTGAN against AIM
  and MST. PATE-CTGAN has the largest utility gap of the differentially private synthesisers on
  all three datasets.
- **Candidate 3, non-private synthesis is private enough:** CTGAN, TVAE and the Gaussian copula
  at epsilon infinity. The expectation did not hold at this scale: no attack detects a risk on
  them. That is reported as the null result it is.
- **Candidate 4, membership inference at small budgets:** at chance wherever measured, which is
  what the guarantee promises.
