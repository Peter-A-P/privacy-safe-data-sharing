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
| ACS PUMS, California 2018 | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed |
| IEEE-CIS card transactions | pending | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | pending | pending | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed |
| NY SPARCS discharges | pending | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed | pending | pending | none: no budget is within 0.02 AUC of the real-data ceiling on every task and seed |

**What leaked.** A risk counts when its interval at the Bonferroni level excludes zero.

| Dataset | Library and version | Configuration | Attack | Risk, % (95% CI) | Success on members vs control, % |
|---|---|---|---|---|---|
| ACS PUMS, California 2018 | smartnoise-synth 1.0.8 | AIM, epsilon 1, 20,000 rows | inference | 2.5 (0.7 to 4.4) | 23.4 vs 21.4 |

<!-- report:end -->

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
