# Share the Data, Not the People

Hand a synthetic copy of a sensitive dataset to a partner, a vendor or a research team without
handing over anyone in it, with the proof attached: before the copy leaves, it is attacked the
way a regulator says and the way a researcher would, and the report says how much it gives
away, how well models trained on it work on the real data, and which settings to use. Proven on
three public datasets of real people, seven synthesisers with and without differential privacy,
every number with its interval.

Organisations under privacy law sit on data they cannot share, and synthetic data is sold to
them as the way out. This project generates synthetic versions of three public datasets of
real people with seven methods, with and without differential privacy, and attacks every one of
them the way a regulator tells you to (singling out, linkability, inference) and the way a
researcher would (membership inference). It publishes, with intervals, how much each table
leaks, how useful it still is for the models people will train on it, the price of privacy as
a curve, and the configurations that leak.

## Result

<!-- report:start -->

_Filled by `facsimile report`; the full tables, one row per dataset, synthesiser and budget,
are in [docs/results.md](docs/results.md)._

**Where to sit.** The rule (PLAN.md section 2.6, fixed before any table was scored): the
smallest epsilon at which every task is within 0.02 AUC of the real-data ceiling on
every seed and no attack's risk is detected.

| Dataset | Gaussian copula | CTGAN | TVAE | TabDDPM | MST | AIM | PATE-CTGAN |
|---|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |
| IEEE-CIS card transactions | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |
| NY SPARCS discharges | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |

_none: utility_ means no budget is within the margin of the ceiling on every task and seed;
_none: risk_ means every useful budget has a detected risk; _pending_ means a budget's
tables are not all attacked and scored yet.

**At a looser margin.** The same rule at 0.05 AUC in place of 0.02, for a
reader who accepts more loss. A sensitivity line, added after the results were seen; the
rule above stays the recommendation (PLAN.md section 2.6).

| Dataset | Gaussian copula | CTGAN | TVAE | TabDDPM | MST | AIM | PATE-CTGAN |
|---|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | none: utility | none: utility | none: utility | epsilon inf | none: utility | none: utility | none: utility |
| IEEE-CIS card transactions | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |
| NY SPARCS discharges | none: utility | none: utility | none: utility | epsilon inf | none: utility | none: utility | none: utility |

**How close each gets.** The budget at which a synthesiser comes nearest the real-data
ceiling, and the gap on its worst task there: AUC trained on synthetic minus trained on
real, the mean over seeds (the worst seed's lower 95% bound in brackets).

| Dataset | Gaussian copula | CTGAN | TVAE | TabDDPM | MST | AIM | PATE-CTGAN |
|---|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | -0.282 (-0.296) at epsilon inf | -0.062 (-0.075) at epsilon inf | -0.053 (-0.077) at epsilon inf | -0.022 (-0.029) at epsilon inf | -0.306 (-0.346) at epsilon 4 | -0.147 (-0.239) at epsilon 1 | -0.339 (-0.409) at epsilon 8 |
| IEEE-CIS card transactions | -0.404 (-0.453) at epsilon inf | -0.129 (-0.167) at epsilon inf | -0.101 (-0.152) at epsilon inf | -0.061 (-0.105) at epsilon inf | -0.193 (-0.228) at epsilon 8 | -0.148 (-0.209) at epsilon 2 | -0.318 (-0.429) at epsilon 2 |
| NY SPARCS discharges | -0.203 (-0.213) at epsilon inf | -0.075 (-0.087) at epsilon inf | -0.150 (-0.197) at epsilon inf | -0.015 (-0.022) at epsilon inf | -0.288 (-0.311) at epsilon 2 | -0.144 (-0.167) at epsilon 2 | -0.346 (-0.401) at epsilon 8 |

**Through the 03 gate.** Project 03's release gate, asked whether a model trained on the
synthetic table is non-inferior to the same model trained on the real data, at a margin
of 2 AUC points, on each seed's table. The gap is synthetic minus real on the
worst task, in points, across the three seeds.

| Dataset | Candidate | Gate, three seeds | Worst-task gap, points |
|---|---|---|---|
| ACS PUMS, California 2018 | TabDDPM, epsilon inf | block on 3 of 3 | -2.7 to -1.3 |
| ACS PUMS, California 2018 | TVAE, epsilon inf | block on 3 of 3 | -6.2 to -5.1; every interval wholly below -2 |
| ACS PUMS, California 2018 | AIM, epsilon 1 | block on 3 of 3 | -22.9 to -12.5; every interval wholly below -2 |
| IEEE-CIS card transactions | TabDDPM, epsilon inf | not decided on 3 of 3 (too few fraud cases for the power screen) | -8.4 to -6.0; every interval wholly below -2 |
| IEEE-CIS card transactions | TVAE, epsilon inf | not decided on 3 of 3 (too few fraud cases for the power screen) | -17.4 to -8.4; every interval wholly below -2 |
| IEEE-CIS card transactions | AIM, epsilon 2 | not decided on 3 of 3 (too few fraud cases for the power screen) | -18.9 to -12.3; every interval wholly below -2 |
| NY SPARCS discharges | CTGAN, epsilon inf | block on 3 of 3 | -7.6 to -7.0; every interval wholly below -2 |
| NY SPARCS discharges | TabDDPM, epsilon inf | block on 3 of 3 | -2.3 to -1.3 |
| NY SPARCS discharges | AIM, epsilon 2 | block on 3 of 3 | -17.1 to -13.8; every interval wholly below -2 |

**The leakage ladder.** Four methods people use as synthetic or anonymised data, expected
to leak, through the same attacks as the positive controls of the grid (PLAN.md section
2.10). Each cell: how many of the five attacks detect a risk at the same Bonferroni
level, the largest of those risks, and the utility gap on the worst task. The attacks
detected are named in [docs/results.md](docs/results.md#the-leakage-ladder).

| Dataset | Perturbed copy | SMOTE-NC | k-anonymity, k = 5 | TVAE, 3,000 epochs |
|---|---|---|---|---|
| ACS PUMS, California 2018 | 4 of 5, up to 18.5% (linkability, 10 neighbours); utility -0.014 (employment) | 4 of 5, up to 27.8% (inference); utility -0.009 (employment) | 2 of 5, up to 9.3% (inference); utility -0.019 (employment) | none detected; utility -0.068 (employment) |
| IEEE-CIS card transactions | 3 of 5, up to 7.7% (inference); utility -0.050 (fraud) | 3 of 5, up to 38.6% (inference); utility -0.043 (fraud) | 2 of 5, up to 6.1% (inference); utility -0.082 (fraud) | none detected; utility -0.131 (fraud) |
| NY SPARCS discharges | 3 of 5, up to 57.6% (inference); utility -0.010 (high_charge) | 3 of 5, up to 32.1% (inference); utility -0.009 (high_charge) | 2 of 5, up to 4.9% (inference); utility -0.033 (long_stay) | none detected; utility -0.078 (long_stay) |

**The most exposed records.** The same attacks on each grid table's most unusual quarter of
targets against its most unusual quarter of control records: 5 detected risks
across 51 configurations, where chance alone would give about 1.3 of the
255 tests.

| Dataset | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % |
|---|---|---|---|---|
| ACS PUMS, California 2018 | TabDDPM, epsilon inf | inference | 8.5 (4.3 to 12.6) | 31.5 vs 25.2 |
| ACS PUMS, California 2018 | MST, epsilon 1 | inference | 4.6 (1.9 to 7.4) | 16.0 vs 11.9 |
| ACS PUMS, California 2018 | AIM, epsilon 1 | inference | 7.2 (3.8 to 10.7) | 24.2 vs 18.3 |
| ACS PUMS, California 2018 | AIM, epsilon 2 | inference | 5.5 (2.0 to 9.0) | 23.6 vs 19.1 |
| NY SPARCS discharges | PATE-CTGAN, epsilon 4 | linkability, 10 neighbours | 0.8 (0.2 to 1.4) | 0.9 vs 0.1 |

**A foundation model as the membership attacker.** The same Groundhog evidence classified
by TabFM instead of the random forest, on 30 grid configurations: TabFM is
better on 1, worse on 0 and indistinguishable on
29 (paired 95% intervals), and 1 configuration with no membership risk under the forest has a detected one under TabFM: ACS PUMS, California 2018, AIM at epsilon 1, accuracy 0.650 (0.558 to 0.735). Each verdict is a one-sided test at 2.5 percent, so over 30 configurations about 0.8 would be detected by chance alone.
On the copy control, TabFM scores 0.642 (0.549 to 0.727) on ACS PUMS, California 2018 against the forest's 0.558 (0.465 to 0.649), and the forest on the same 500 features 0.683 (0.592 to 0.765); 0.558 (0.465 to 0.649) on IEEE-CIS card transactions against the forest's 0.550 (0.457 to 0.641), and the forest on the same 500 features 0.533 (0.440 to 0.625); 0.783 (0.699 to 0.853) on NY SPARCS discharges against the forest's 0.525 (0.432 to 0.617), and the forest on the same 500 features 0.717 (0.627 to 0.795); most of the gain on the copies is the feature selection, not the model.
TabFM's weights were trained on synthetic tables drawn from structural causal models and
are licensed for non-commercial, non-production use only, so the code that calls them is
not published and nothing here depends on it. The table by table numbers are in
[docs/results.md](docs/results.md#membership-inference-with-a-foundation-model-attacker).

**What leaked.** A risk counts when its interval at the Bonferroni level excludes zero.
Beside each, Anonymeter on the same tables, pooled the same way (PLAN.md section 2.12);
a leak it does not detect at that level stays, marked as not reproduced.

| Dataset | Library and version | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % | Anonymeter, risk % (95% CI) |
|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | smartnoise-synth 1.0.8 | AIM, epsilon 1, 20,000 rows | inference | 2.5 (0.7 to 4.4) | 23.4 vs 21.4 | 1.8 (0.0 to 3.7), **not reproduced** |
| ACS PUMS, California 2018 | smartnoise-synth 1.0.8 | AIM, epsilon 1, about 1,000 rows | membership, TabFM | accuracy 0.650 (0.558 to 0.735) | | |

<!-- report:end -->

## The honest limitation

The membership inference attack runs at about 1,000 rows with 40 shadow tables per target, the
scale its paper used, because shadow training needs a synthesiser fit per shadow table. At that
scale it has little power. Even when the attacked table is a copy of the real data, it is barely
above chance (the TAPAS comparison in [docs/results.md](docs/results.md)). Every membership result
under the paper's random forest is at chance, and that means the attack could not tell, not that
the tables are safe: a second attacker, a tabular foundation model on the same evidence, catches
the copy on two of the three datasets where the forest misses it, and detects one grid configuration the forest called clean (AIM at
epsilon 1 on ACS, within what chance gives over 30 tests), and the forest itself catches the
copies once it is given only the 500 features that move with the target. The
three legal-test attacks run on the full 20,000-row tables and carry the risk numbers, and the
leakage ladder shows they have the power the membership attack lacks: they catch every perturbed
copy, SMOTE-NC and k-anonymity table they were given. The fourth ladder method, TVAE trained
for 3,000 epochs, escapes them on its full target sets, so an overfitted deep model at this size
is not something these attacks are shown to catch.

## Tried and rejected

Distance to closest record, the check most synthetic-data tools show their users, was tested as a
privacy measure on every table and rejected. It passed the one configuration an attack broke and
failed eight that no attack could break, seven of them differentially private. The evidence is in
[docs/rejected.md](docs/rejected.md). DCR stays in the full tables, labelled as what it is.

## Use the attacks on your own tables

The attacks are a package you can point at any synthetic table, given the real records it was
trained on and as many real records from the same population that it never saw:

```python
from facsimile.attacks.evaluate import evaluate

result = evaluate(targets, control, synthetic, secret="income")
print(result.markdown())   # singling out, linkability, inference: risk with a 95% interval
result.detected            # the attacks whose risk interval excludes zero
```

or, from files, `facsimile evaluate targets.csv control.csv synthetic.csv --secret income`. Raw
tables are fine: the coding is read from the control set, never from the targets. Nothing
outside the three tables is used. The details, and what a result does and does not mean, are in
[docs/attack-package.md](docs/attack-package.md).

## What this does not do

It does not synthesise text, images or time series, and it does not defend a table after
measuring it. It never joins outside data to a record and never puts a name to one: the
attacks measure whether a row can be isolated, linked or inferred inside a public-use file,
which is the risk privacy law names, and stop there. It does not call a model vendor.

## How it works

Three real datasets (census respondents, card transactions, hospital discharges where the
terms permit) are split into a training set the synthesisers see, a control set they never
see, and a test set for utility. Seven synthesisers produce tables at six privacy budgets and
three seeds. Three attacks implemented from the paper that defines the legal test, plus the
shadow-model membership inference attack and distance to closest record, run on every table
against the control set, and the project's implementations are checked against the reference
libraries. Utility is a model trained on synthetic data and scored on real data, against the
real-data ceiling. The result is a surface of privacy against usefulness with a stated rule
for where to sit. The design, the data terms and the week-by-week order are in
[PLAN.md](PLAN.md); the diagrams are in [docs/architecture.md](docs/architecture.md).

## Data and credits

- **ACS PUMS**, California 2018 one-year person file, US Census Bureau, through folktables. The
  Census Bureau does not endorse this project.
- **IEEE-CIS Fraud Detection**, Vesta Corporation for the IEEE Computational Intelligence
  Society, under the competition's rules. No row or row id is redistributed.
- **NY SPARCS**: source New York State Department of Health, Hospital Inpatient Discharges
  (SPARCS De-Identified): 2024, Health Data NY dataset `sf4k-39ay`, published 2025-10-10,
  accessed 2026-10-16. The New York State Department of Health makes no representation,
  warranty or guarantee relating to the data or analyses derived from these data.

The terms each set is used under are quoted in [docs/data.md](docs/data.md).

## Part of a portfolio

One of sixteen projects on [peterparker.ca](https://peterparker.ca), each of which ends in a
measured result a stranger can reproduce from its repository with one command. This one reuses
the statistics from [Model Selection at a Tenth of the Cost](https://github.com/Peter-A-P/model-selection-tenth-cost),
the release gate from [AI Release Gate](https://github.com/Peter-A-P/ai-release-gate) and the
transaction data terms recorded by the [Real-Time Fraud and Risk Decisioning Platform](https://github.com/Peter-A-P/realtime-risk-platform).

## How this was built

The design, the methodology and the judgement calls are Peter Parker's. AI coding assistants
were used for implementation. Every number in this repository is reproducible with one command,
and the plan was written before the first line of code so that the result could not be shaped
to fit.
