# Share the Data, Not the People

Hand a synthetic copy of a sensitive dataset to a partner, a vendor or a research team without
handing over anyone in it, with the proof attached: before the copy leaves, it is attacked the
way a regulator says and the way a researcher would, and the report says how much it gives
away, how well models trained on it work on the real data, and which settings to use. Proven on
three public datasets of real people, six synthesisers with and without differential privacy,
every number with its interval.

Organisations under privacy law sit on data they cannot share, and synthetic data is sold to
them as the way out. This project generates synthetic versions of three public datasets of
real people with six methods, with and without differential privacy, and attacks every one of
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

| Dataset | Gaussian copula | CTGAN | TVAE | MST | AIM | PATE-CTGAN |
|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |
| IEEE-CIS card transactions | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |
| NY SPARCS discharges | none: utility | none: utility | none: utility | none: utility | none: utility | none: utility |

_none: utility_ means no budget is within the margin of the ceiling on every task and seed;
_none: risk_ means every useful budget has a detected risk; _pending_ means a budget's
tables are not all attacked and scored yet.

**How close each gets.** The budget at which a synthesiser comes nearest the real-data
ceiling, and the gap on its worst task there: AUC trained on synthetic minus trained on
real, the mean over seeds (the worst seed's lower 95% bound in brackets).

| Dataset | Gaussian copula | CTGAN | TVAE | MST | AIM | PATE-CTGAN |
|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | -0.282 (-0.296) at epsilon inf | -0.062 (-0.075) at epsilon inf | -0.053 (-0.077) at epsilon inf | -0.306 (-0.346) at epsilon 4 | -0.147 (-0.239) at epsilon 1 | -0.339 (-0.409) at epsilon 8 |
| IEEE-CIS card transactions | -0.404 (-0.453) at epsilon inf | -0.129 (-0.167) at epsilon inf | -0.101 (-0.152) at epsilon inf | -0.193 (-0.228) at epsilon 8 | -0.148 (-0.209) at epsilon 2 | -0.318 (-0.429) at epsilon 2 |
| NY SPARCS discharges | -0.203 (-0.213) at epsilon inf | -0.075 (-0.087) at epsilon inf | -0.150 (-0.197) at epsilon inf | -0.288 (-0.311) at epsilon 2 | -0.144 (-0.167) at epsilon 2 | -0.346 (-0.401) at epsilon 8 |

**Through the 03 gate.** Project 03's release gate, asked whether a model trained on the
synthetic table is non-inferior to the same model trained on the real data, at a margin
of 2 AUC points, on each seed's table. The gap is synthetic minus real on the
worst task, in points, across the three seeds.

| Dataset | Candidate | Gate, three seeds | Worst-task gap, points |
|---|---|---|---|
| ACS PUMS, California 2018 | TVAE, epsilon inf | block on 3 of 3 | -6.2 to -5.1; every interval wholly below -2 |
| ACS PUMS, California 2018 | AIM, epsilon 1 | block on 3 of 3 | -22.9 to -12.5; every interval wholly below -2 |
| IEEE-CIS card transactions | TVAE, epsilon inf | not decided on 3 of 3 (too few fraud cases for the power screen) | -17.4 to -8.4; every interval wholly below -2 |
| IEEE-CIS card transactions | AIM, epsilon 2 | not decided on 3 of 3 (too few fraud cases for the power screen) | -18.9 to -12.3; every interval wholly below -2 |
| NY SPARCS discharges | CTGAN, epsilon inf | block on 3 of 3 | -7.6 to -7.0; every interval wholly below -2 |
| NY SPARCS discharges | AIM, epsilon 2 | block on 3 of 3 | -17.1 to -13.8; every interval wholly below -2 |

**What leaked.** A risk counts when its interval at the Bonferroni level excludes zero.

| Dataset | Library and version | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % |
|---|---|---|---|---|---|
| ACS PUMS, California 2018 | smartnoise-synth 1.0.8 | AIM, epsilon 1, 20,000 rows | inference | 2.5 (0.7 to 4.4) | 23.4 vs 21.4 |

<!-- report:end -->

## The honest limitation

The membership inference attack runs at about 1,000 rows with 40 shadow tables per target, the
scale its paper used, because shadow training needs a synthesiser fit per shadow table. At that
scale it has little power. Even when the attacked table is a copy of the real data, it is barely
above chance (the TAPAS comparison in [docs/results.md](docs/results.md)). Every membership result
here is at chance, and that means the attack could not tell, not that the tables are safe. The
three legal-test attacks run on the full 20,000-row tables and carry the risk numbers.

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
see, and a test set for utility. Six synthesisers produce tables at six privacy budgets and
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
