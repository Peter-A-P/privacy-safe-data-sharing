# Plan: Share the Data, Not the People

**Written:** 2026-10-16. **Status:** week 1 started 2026-10-16: all three datasets fetched and
built, the six synthesisers behind one interface; amendments made while building are marked
"Amended 2026-10-16" where they fall.
**Build:** three weeks of evenings and weekends alongside 16, starting when this plan is
approved; the weeks in section 6 are relative, not dated. **Package:** `facsimile`.
**Repository:** `privacy-safe-data-sharing`.
**Fed by:** 09 (the IEEE-CIS loader and the competition terms it recorded on 2026-09-12), 02
(bootstrap intervals and paired deltas), 03 (the gate decides whether a model trained on
synthetic data is non-inferior to one trained on the real data). **Feeds:** nothing by
contract; the attack package is reusable by anyone who publishes a synthetic table, which is
the point of it. No model vendor is called, so 04 is not on the path; the spend is CPU and a
few GPU hours.

Fifteen projects in this portfolio measure something a model does. This one measures
something a dataset does: whether a synthetic table that an organisation wants to share
still gives away the people in the real one, and what it costs in usefulness to stop that.

---

## 1. What this produces

Organisations under privacy law sit on data they cannot share, and synthetic data is sold to
them as the way out. Almost every published evaluation reports how faithful the synthetic
table is and skips the question that decides whether it can be released: can an attacker
still single out, link or infer things about the real people behind it. This project
generates synthetic versions of three public datasets of real people with six methods,
with and without differential privacy, and attacks every one of them the way a regulator
tells you to and the way a researcher would. It publishes, with intervals, the risk, the
usefulness, and the price of privacy as a curve, and names the configurations that leak.

The numbers a stranger can check:

| Number | What it shows |
|---|---|
| Singling out, linkability and inference risk per synthetic table (six synthesisers, six privacy budgets, three datasets, three seeds), each as attack success against a control set with a 95% interval, implemented from the paper that defines them | The legal test: the three criteria regulators use to decide whether data is anonymous, measured rather than asserted |
| Membership inference success (shadow-model Groundhog attack) per table, with intervals, against chance | The engineer's number: whether an attacker can tell who was in the training data |
| Utility as train-on-synthetic, test-on-real per downstream task against the real-data ceiling and the no-information floor, with paired intervals | Usefulness measured the way the buyer will use the data, not as a fidelity score |
| Query error on one-, two- and three-way marginals per table | The fidelity axis, reported but never as a stand-in for either of the above |
| The epsilon-utility-risk surface per dataset and synthesiser, with a stated recommendation of where to sit and why | The trade-off a privacy officer and a data scientist have to agree on, drawn |
| Distance-to-closest-record beside the attack results on the same tables | Whether the metric most vendors quote says "safe" while an attack succeeds (Rule C candidate 1) |
| Non-inferiority of a model trained on the recommended synthetic table against one trained on real data, through the 03 gate, delta stated | Whether "as good as the real thing" is true for the configuration recommended |
| Synthesiser wall-clock and GPU time per table, hardware stated | What privacy costs in compute, since the best DP methods are the slowest |
| Agreement between the project's attack implementations and the reference library on the same tables | That the from-the-paper implementations are the paper's, not a variant |

## 2. Design decisions

### 2.1 Real people, public terms, three domains

Attacks only mean something on records of real people, so the datasets are real microdata
with terms a stranger can accept:

- **ACS PUMS via folktables** (census respondents; public Census Bureau data; folktables MIT).
  The standard benchmark of the differential-privacy literature, so every number here can be
  set beside published ones. Tasks: ACSIncome and ACSEmployment, one state-year each.
  **Amended 2026-10-16:** one table carries both tasks, because the grid is fitted once per
  dataset. The table is ACSEmployment's population (age 17 to 89) and the income task applies
  ACSIncome's own filter in the coded domain, so it is ACSIncome exactly but for the 90-and-over;
  the employment task keeps ten of its sixteen features (the six dropped keep AIM tractable), so
  it compares with published numbers loosely, not exactly. California 2018.
- **IEEE-CIS Fraud Detection** (card transactions; Kaggle competition terms, non-commercial,
  read and recorded by 09 on 2026-09-12 and reused here unchanged). The fintech set; the
  downstream task is fraud classification.
- **New York SPARCS de-identified inpatient discharges** (real hospital stays; public use file
  with no application), **if the state's own terms, read on day one, permit the use**.
  **Amended 2026-10-16:** read on day one; the Department of Health's Data Use Policy Statement
  places no controls on end use and asks for attribution, the access date and a disclaimer, so
  the set is in (`docs/data.md` quotes it). The 2024 file, the latest published. The
  health set; tasks are length of stay and a charge band. If the terms do not permit it, the
  project runs on two datasets and the README says why; the MIMIC-IV demo (100 patients) is
  too small for an attack to mean anything and is not a substitute.

One rule on top of the terms, recorded because the Census terms state it: attacks are
measured against the dataset's own records, with no external data joined, and nothing is
ever done to put a name to a record. Singling out means isolating a row in a public-use
file, which is the risk the law names; it is never carried past the dataset.

### 2.2 Six synthesisers, one interface, one accountant per method

| Arm | Method | Why |
|---|---|---|
| Non-DP, statistical | Gaussian copula (SDV) | The baseline every vendor starts from |
| Non-DP, deep | CTGAN and TVAE (SDV) | The methods most "synthetic data" products ship |
| DP, marginal | AIM and MST (SmartNoise, Private-PGM) | The state of the art in the 2025 benchmark of DP tabular synthesis; AIM leads on utility at every budget and is the slowest |
| DP, deep | PATE-CTGAN (SmartNoise) | The deep DP arm the same benchmark expects to lose; Rule C candidate 2 |

Every method is wrapped in one interface: fit on the training split with a seed, a privacy
budget where it applies, and the preprocessing the benchmark recommends (uniform binning,
rare-category merging at a fixed threshold, recorded). **Amended 2026-10-16:** the domain spends
no budget. Bin edges are fixed from public bounds in each dataset's spec; category sets come from
the test split, which no synthesiser sees, at a half-percent threshold; SmartNoise is handed a
transformer already fitted to that domain, because its default reads the category set off the
training data without charging for it (`docs/synthesisers.md`). Budgets: epsilon 0.5, 1, 2, 4 and 8,
delta 1e-5, with the non-DP methods reported at epsilon infinity; three seeds per cell. The
accountant each library uses is named in `docs/synthesisers.md` with the version, because a
wrong epsilon is worse than none and the plan does not roll its own.
**Amended 2026-10-18:** AIM's epsilon 8 grid cells are dropped (Peter; final 2026-10-28, below).
On the rented 32-vCPU, 128 GB machine AIM at epsilon 8 on ACS grew to 25 GB in under five hours
while every other cell stayed under 8 GB, and two such cells exhausted the machine; none of the
nine had finished when they were stopped. The report shows the cell as not run, with that
measurement, rather than leaving it blank. AIM's Groundhog fits at epsilon 8 (1,000 rows) stay.
**Amended 2026-10-27:** AIM's epsilon 4 grid cells are not run (Peter). On the same machine each
table ran more than 28 hours without finishing and used up to 53 GB, so the nine tables were
estimated at CA$60 to 150 of rented time against about CA$15 left in the budget, and one seed per
dataset at CA$25 to 45. Neither could change the recommendation: at epsilon 2 AIM is 0.10 to 0.17
AUC short of the 0.02 bar on every task, and no doubling of its budget gained more than 0.03.
The report shows the cell as not run, with that measurement.
**Amended 2026-10-28:** the epsilon 8 cells are not revisited either (Peter). Running both
budgets on every seed was estimated at CA$310 to 800 of rented time (epsilon 8 on a 256 GB
machine, since no table had finished), and one seed per dataset of each at CA$110 to 260,
against the same CA$15 left; for the same reason as epsilon 4, neither could change the
recommendation.

### 2.3 The attacks are implemented from the papers and checked against the libraries

The headline attacks are the three of Giomi et al. (PoPETs 2023): singling out (univariate
and multivariate predicates that isolate one real record), linkability (joining two
attribute halves of a record through the synthetic table's nearest neighbours), and inference
(predicting a secret attribute from quasi-identifiers through the synthetic table). Each is
written in `facsimile/attacks/` from the paper, with the paper's three-way design: the main
attack against records that were in the training data, the same attack against a control set
of real records that were not, and a random baseline. Risk is the main attack's success over
the control's, which is what separates leakage from the synthetic table simply being useful.
Beside them, the membership inference attack of Stadler et al. (USENIX 2022) in its Groundhog
form: shadow synthetic datasets, a feature map of naive statistics, histograms and
correlations, a random forest that says whether a target was in. **Amended 2026-10-16
(Peter's decision):** at AIM's measured 29 minutes per 20,000-row table, shadow training at the
grid's size cannot finish, so the Groundhog attack runs at about 1,000 rows, the scale Stadler et
al. used: shadow and attacked tables of that size, a small fixed set of targets per dataset, all
six synthesisers at three budgets (epsilon 1, 8 and infinity). It is reported as membership
inference at that scale, not as a property of the 20,000-row grid tables. And distance to closest
record, the metric vendors quote, computed on the same tables so the comparison is paired.

The project's implementations are run beside the reference libraries, Anonymeter (Clear BSD;
its authors hold a patent application, recorded in `docs/attacks.md`) and TAPAS (MIT), on the
same tables, and the agreement is published. **Amended 2026-10-16:** Anonymeter 1.1 pins numpy
below 1.27, which has no Python 3.13 wheel, so `pyproject.toml` overrides the pin (it runs on
numpy 2, checked on a copied table); TAPAS requires Python below 3.11 and pandas 1.x, so it runs
in its own Python 3.10 environment on tables exported to disk. If they disagree, the plan says which is wrong
and why before any number ships. Implementing them is what shows understanding; agreeing with
the authors is what shows the implementation is theirs.

### 2.4 Utility is train-on-synthetic, test-on-real

A synthetic table is useful if a model trained on it works on real data. Each dataset has one
or two downstream tasks; a LightGBM model is trained on the synthetic table and scored on a
held-out real test set, against the same model trained on the real training split (the
ceiling) and a majority-class or mean predictor (the floor). Paired bootstrap intervals over
the test set. Marginal query error is reported as fidelity and never as utility. The 03 gate
runs the non-inferiority test for the recommended configuration on each dataset.
**Amended 2026-10-27 (Peter's decision):** the rule recommends no configuration, so the gate
runs on the nearest ones instead, fixed by rule before it ran: per dataset, the configuration
nearest the ceiling on its worst task over all synthesisers and over the differentially private
ones, each on its three seeds. An item is a disjoint pair of one positive and one negative test
record, correct when the model ranks them right, so the gate's accuracy is an AUC estimate and
its margin is the rule's 0.02 (`docs/gate.md`). The files live in `gate-runs/`, as in 06, and
the code in `facsimile/gate.py`.

### 2.5 Splits that make the attack arithmetic honest

Each dataset is split once: a training split the synthesisers see, a control split of real
records they never see (the attacks' control set), and a test split for utility. Targets for
the attacks are drawn from the training split; the control set is the same size. A leakage
check on every build confirms the three are disjoint and that no synthesiser was fit on a
control or test record. The splits and the attack target ids are published so the attacks are
reproducible exactly. **Amended 2026-10-16:** except for IEEE-CIS, whose competition rules (7.B)
make a list of TransactionIDs a row-level reference that may not be published; its manifest
carries counts and SHA-256 hashes, and the split is reproducible exactly from the files and the
seed. Sizes for all three: train 20,000, control 2,000, attack targets 2,000 drawn from train,
test 10,000.

### 2.6 The surface and the recommendation

For each dataset and synthesiser, utility and each risk are plotted against epsilon with
intervals: the epsilon-utility-risk surface. The recommendation is a rule, not a taste: the
smallest epsilon at which utility is within a stated delta of the real-data ceiling and every
risk is within its interval of the control, or the statement that no such point exists for
that synthesiser. The rule, its delta and the result per dataset are in the README.
**Specified 2026-10-16** (`facsimile/surface.py`, before any table was scored on purpose):
utility passes when every task's 95% interval of AUC(synthetic) minus AUC(real ceiling) lies
above -0.02 on every seed; risk passes when, with successes pooled over the three seeds, every
attack's risk interval at 1 - 0.05/(number of attacks) includes zero; epsilon infinity is a
budget like any other.

### 2.7 Naming a leak

Where a configuration leaks, the README names the library, the version, the configuration
and the measurement, and frames it as a property of those settings on this data. No claim
about a product, no adjectives. Precision is what makes it credible.

### 2.8 The demo shows the surface

privacy.peterparker.ca is a static page on Azure Static Web Apps: pick a dataset and a
synthesiser, see utility and the three risks move with epsilon, with intervals, and the
recommended point marked; the leak table beside it. Precomputed JSON, nothing modelled in the
browser, no uploads. The pattern of 01, 08 and 16.

### 2.9 Out of scope, on purpose

- Text, images, time series. Tabular only; it is where the law and the vendors are.
- Hand-rolled differential privacy. Accountants come from the libraries and are named.
- Defending against the attacks (post-processing, rejection sampling). Measurement first.
- A general synthetic-data product. The deliverable is the attack package and the surface.
- Federated or multi-party settings.

### 2.10 The leakage ladder and the exposed records (added 2026-10-27, Peter's decision)

Written before any ladder table was made or any exposed-records number computed. The grid's
attacks detected one risk in 48 configurations. That alone cannot say whether the tables are
safe or the attacks are weak. The membership attack has a positive control (the copy); the three
regulators' attacks do not. So four methods that people use as "synthetic" or "anonymised" data,
and that are expected to leak, are run through exactly the same pipeline: the same splits,
targets, control, attacks, seeds, utility and Groundhog scale. They are reported beside the grid
as a ladder, never mixed into its surface, its recommendation or its gate candidates.

| Rung | Method, as people use it | Settings, fixed here | Expected |
|---|---|---|---|
| 1 | **Perturbed copy**: the training records themselves, numbers jittered and values swapped, the classic statistical-disclosure-control release | Every training record once; Gaussian noise of one bin's width on each binned numeric attribute, rounded and clipped; 10% of records swap each categorical attribute with another record | Detected by singling out, linkability and inference; utility near the ceiling |
| 2 | **SMOTE-NC** (Chawla et al. 2002) used as a synthesiser: each record interpolated between a real record and one of its five nearest real neighbours | k = 5; numeric attributes interpolated and rounded to a bin; categorical attributes the most frequent value among the five neighbours; the project's mixed-type distance | Detected by inference and linkability |
| 3 | **k-anonymity** (Mondrian, LeFevre et al. 2006): every attribute but the secret generalised until each record matches at least k-1 others, then released at the group's representative values | k = 5; numeric attributes at the group median, categorical at the group mode; the secret released as is, the usual k-anonymity release | Detected by inference (k-anonymity does not protect the secret); singling out not detected |
| 4 | **An overfitted deep model**: TVAE trained ten times longer than SDV's default | 3,000 epochs instead of 300, everything else as the grid's TVAE | The likeliest rung for membership inference at 1,000 rows; at 20,000 rows, possibly nothing |

**Exposed records.** Every grid and ladder table is also attacked on its most unusual records:
the quarter of targets, and separately the quarter of control records, farthest on average from
a fixed sample of 2,000 test-split records (the test split stands in for public knowledge, as in
the domain). Same attacks, same table, 500 targets against 500 controls per seed. Expected:
risks at least as large as on all targets, with wider intervals; a detection here that the full
target set does not show is reported as a property of the exposed records.

The ladder is reported whatever it shows. A rung that is expected to leak and does not is a
finding about the attacks' power, and is written up as one.

### 2.11 Next: a second attacker, then a diffusion synthesiser (added 2026-10-28, Peter's decision)

Two additions, in this order. Neither is in the definition of done (section 11).

**First, TabFM as a second membership attacker.** The Groundhog attack with a pretrained tabular
foundation model in place of the random forest, on the same shadow and evaluation tables, so the
two attackers are paired. The report already reads its results when they exist. TabFM's licence
forbids distributing a work that uses the model, so the results ship and the code that calls it
does not; the docs say so.

**Then, a diffusion model as a seventh synthesiser.** The grid has a GAN (CTGAN) and a VAE (TVAE)
but no diffusion model, the third family of deep generative model and the one the literature
most often finds memorising its training data. Whether it leaks more than the other two on these
tables is the question.

| Arm | Method | Settings | Expected |
|---|---|---|---|
| Non-DP, deep | TabDDPM (Kotelnikov et al. 2023), through synthcity | Library defaults, as every other arm, on the same coded domain; epsilon infinity, three seeds | Utility near CTGAN and TVAE; the deep arm most likely to be detected, on the exposed records and by Groundhog if anywhere |

- **Non-DP only.** No library packages a differentially private tabular diffusion model with its
  own accountant, and adding DP-SGD to one by hand is the hand-rolled privacy this plan rules out.
- **The same pipeline as the grid**: 9 tables, the five attacks, the exposed records, DCR, utility,
  the surface and the recommendation, and Groundhog at its 1,000-row scale (6 targets times 60
  fits per dataset, 1,080 fits). It is a grid arm, so it can become a gate candidate.
- **First step, a timing spike**: install, fit one ACS table, time one 1,000-row fit; the
  Groundhog fits decide the wall-clock.
- **Its own environment (amended 2026-10-28, before the spike).** synthcity 0.2.12 cannot be
  installed on Python 3.13: it depends on decaf-synthetic-data, which needs torchtext, which has
  no 3.13 wheel. It runs in a Python 3.12 environment with torch 2.2.2
  (`envs/synthcity-requirements.txt`), called in a subprocess by `facsimile/synth/tabddpm.py`.
  Read from its source the same day: its default `n_iter` of 1,000 counts epochs, not steps, so a
  1,000-row fit is about 20 times cheaper than a 20,000-row one, as for TVAE. And a column with
  more than 10 distinct values is diffused as a number, not a category. By the domains' sizes that
  is two to four nominal columns per dataset (ACS occupation, schooling, birthplace and
  relationship; IEEE-CIS address and the two email domains; SPARCS zip code and diagnostic
  category), whose codes have no order. The library's default is kept and the columns are named
  in each record, as PATE-CTGAN's properties are; the project rounds and clips them back into the
  domain and counts what the clipping moved.
- **Cost**: the desktop GPU, CA$0. A rented GPU only on Peter's go, within what is left of the
  budget, if the spike puts the Groundhog fits beyond three days on the desktop.
- **The spike (2026-10-29)**: 1,420 s a table at 20,000 rows, so the 9 grid tables take about
  3.5 hours, and 104 s a fit at 1,000 rows, so the 1,080 Groundhog fits take about 31 hours. Both
  on the desktop, inside the three days: no rented GPU. At 1,000 rows the defaults train for a
  twentieth of the steps and the model has not learned the marginals (`docs/synthesisers.md`);
  the Groundhog result is reported as a property of that model, as it is for every method.
- **Docs in the same commit as the code**: `docs/synthesisers.md` (version, licence, defaults,
  device), the report's seventh column, the site.
- **What it showed (2026-10-30), against what was expected:** utility better than expected, the
  nearest of all seven to the real-data ceiling on every dataset (worst-task gap -0.022 on ACS,
  -0.061 on IEEE-CIS, -0.015 on SPARCS), still outside the 0.02 rule on every dataset's worst
  seed and blocked by the 03 gate; and, as expected, the deep arm an attack detects: multivariate
  singling out on ACS, 1.8% (0.7 to 2.9), the grid's first leak without differential privacy,
  which Anonymeter puts at the edge of detection (`docs/attacks.md`); averaged over five searches
  (section 2.12) it is 0.6% (0.0 to 1.7) and no longer a leak. Not expected: Groundhog does
  not detect it on any dataset (finished 2026-11-01): 0.542 (0.448 to 0.633) on ACS, 0.483 (0.391
  to 0.576) on IEEE-CIS, 0.500 (0.407 to 0.593) on SPARCS, and the TabFM attacker on the same
  evidence agrees. At 1,000 rows the defaults give an under-trained model, so this says the attack
  could not tell on that model, not that the 20,000-row tables are safe.

### 2.12 Singling out averaged over five searches (added 2026-11-01, Peter's decision)

**Why.** TabDDPM's multivariate singling-out leak on ACS is detected by this project's
implementation, 1.8% (0.7 to 2.9) pooled with a Bonferroni lower bound of 0.35 points, and not by
Anonymeter on the same tables, 1.1% (0.0 to 2.2) with the bound at zero (`docs/attacks.md`). The
two agree on the training records (9.5% against 9.3%) and differ on the control (7.9% against
8.3%), and the seed-level differences run in opposite directions (seed 0: 1.4% here, 2.2% in
Anonymeter; seed 2: 2.7% against 0.8%). That is the noise of the predicate search: each draws its
own random combinations of attributes. Section 2.3 asks that a disagreement be resolved before a
number ships; recording it did not resolve it, and neither would keeping or dropping the row.
This reduces the cause instead. It was decided after the results were seen, so it is fixed here
before anything is rerun and applies to every table, in both directions.

**The rule.**

- Every singling-out attack, univariate and multivariate, runs five independent predicate
  searches on the same table, targets and control, with seeds s, s + 1,000, s + 2,000,
  s + 3,000 and s + 4,000, where s is the table's seed as before (so the first search is the run
  already published, and is checked to reproduce exactly).
- The successes on the targets, the control and the baseline are each the mean over the five
  searches. The number of trials stays at the number of attacks, not five times it: the five
  searches reuse the same records, so they are not independent trials, and counting them as such
  would narrow the interval without new evidence. Pooling over the three seeds, the Wilson rates,
  the residual and the Bonferroni call are unchanged.
- It applies to every attacked table: the grid, the leakage ladder and the exposed records, and to
  `facsimile evaluate`, so the package does what the report does.
- Anonymeter runs the same five searches, seeded the same way, on every grid table and every seed
  (until now: seed 0, and all seeds for TabDDPM), averaged the same way from its success counts.
  Its other attacks run on every seed too, so the agreement covers all 153 grid tables.
- Linkability and inference are not changed: they involve no search, and their disagreements
  with Anonymeter are the tie-break and scaling choices already recorded.
- **How a remaining disagreement is settled, fixed now.** The leak table reports this project's
  averaged measurement, as before, and shows beside every leak Anonymeter's averaged result pooled
  the same way. A leak Anonymeter does not detect at the Bonferroni level stays in the table,
  marked as not reproduced by the reference library, and the README says so. A risk Anonymeter
  detects and this project does not is listed in `docs/attacks.md`.
- The ACS TabDDPM row may stay, go, or be joined by others. Whatever the averaged numbers say
  is what ships.
- **What it showed (2026-11-01).** Every one of the 189 attack records reproduced its published
  first search exactly. The ACS TabDDPM row goes: 0.6% (0.0 to 1.7) here and 1.0% (0.0 to 2.1) in
  Anonymeter, neither detected. No singling-out risk is detected pooled on any configuration, by
  either. The one remaining leak, AIM at epsilon 1 on ACS (inference, unchanged at 2.5% (0.7 to
  4.4)), is not reproduced by Anonymeter at the Bonferroni level, 1.8% (0.0 to 3.7), and is marked
  so. Anonymeter detects two linkability risks with ten neighbours that this project does not
  (PATE-CTGAN at epsilon 2 on ACS, MST at epsilon 8 on SPARCS), listed in `docs/attacks.md`; all
  three differences trace to the tie-break. On the exposed records two singling-out risks leave
  (AIM at epsilon 1 and PATE-CTGAN at epsilon 2, both ACS), seven risks becoming five. On the
  ladder, SMOTE-NC on IEEE-CIS loses its multivariate singling-out detection (three of five
  attacks instead of four). The run took 7 h 40 min on the desktop CPU in six processes.

**Cost.** CA$0: the desktop CPU, an estimated 10 to 17 hours of compute before running tables in
parallel, from the recorded attack timings (this project's multivariate search 24 to 32 s a
table, Anonymeter's five attacks 55 s a table, median).

## 3. Data

| Source | Size | What it gives | Access and terms |
|---|---|---|---|
| ACS PUMS via folktables, one state-year (for example California 2018) | About 200k person records, 10 to 17 attributes per task | Census respondents; ACSIncome and ACSEmployment tasks; comparability with the DP literature | Census Bureau public data; the API terms forbid any attempt to identify a person, which section 2.1 honours by construction; folktables MIT |
| IEEE-CIS Fraud Detection | 590k transactions, 400+ attributes; a 16-attribute subset (amended 2026-10-16 from "30, chosen as 09 did": 09's features are engineered, not a raw subset, and AIM at 30 attributes would not finish the grid) | Card transactions with a fraud label; the fintech set | Kaggle competition rules section 7: non-commercial use only; 09's record of the terms reused |
| NY SPARCS de-identified inpatient discharges, 2024 | 2,196,737 discharges, 33 attributes, a 16-attribute subset (age group, sex, race, 3-digit zip, diagnosis group, severity, length of stay, charges and the rest) | Real hospital stays; the health set | Public use file, no application; the terms on health.data.ny.gov are read and quoted on day one, and the set is used only if they permit |

Nothing raw is committed; loaders fetch and verify checksums; licences are quoted in
`docs/data.md` before the first fetch. Each dataset is reduced to a documented attribute
subset so the marginal methods are tractable, and the subset is published.

## 4. Methods and architecture

See `docs/architecture.md` for the diagrams. The package:

```
facsimile/
  data/        loaders (acs.py via folktables, ieeecis.py reusing 09's terms record, sparcs.py), subset.py,
               split.py (train, control, test; attack targets; leakage check), datasheet.py
  prep.py      uniform binning, rare-category merging, the inverse maps; the benchmark's defaults, recorded
  synth/       base.py (fit(train, seed, epsilon) -> sample(n)), copula.py, ctgan.py, tvae.py (SDV),
               aim.py, mst.py, pate_ctgan.py (SmartNoise); accounting.py (what each library claims, by version)
  attacks/     singling_out.py, linkability.py, inference.py (from Giomi et al., with control and baseline),
               groundhog.py (Stadler et al.), dcr.py; reference.py (Anonymeter and TAPAS on the same tables,
               agreement report)
  utility/     tstr.py (LightGBM per task, ceiling and floor), queries.py (k-way marginal error), stats.py
               (bootstrap, paired deltas; 02's arithmetic)
  surface.py   epsilon-utility-risk per dataset and synthesiser; the recommendation rule and its delta
  gate/        eval spec and outcome files for the 03 gate: synthetic-trained against real-trained
  report/      tables, the surface charts, the leak table, the site JSON
  site/        the static explorer; built by facsimile site
  cli.py       facsimile data fetch | build | synth | attack | utility | surface | gate | report | site
tests/         attack sanity: a synthetic table that copies the real one scores maximum risk, an independent
               one scores control-level; the three-way split is disjoint on every build; bootstrap arithmetic
               against a known stream; the recommendation rule on a synthetic surface; prep round-trip
docs/          architecture.md, data.md (terms quoted, subsets), synthesisers.md (versions, accountants),
               attacks.md (the papers, the implementations, the reference agreement), rejected.md (Rule C)
```

### Tests that matter

The attack sanity pair: feed each attack a synthetic table that is a copy of the training
split and it must report near-maximum risk; feed it a table drawn independently of the
training split and it must report risk at the control level. The split test: train, control
and test disjoint, targets inside train, control the same size as targets. The accountant
test: every DP table's recorded epsilon and delta match what the library was asked for. The
recommendation rule on a hand-built surface with a known answer. The bootstrap against a
stream with a known interval.

## 5. Interfaces with the rest of the portfolio

| Project | What crosses the line |
|---|---|
| 09 | The IEEE-CIS loader and the competition-terms record, reused as written |
| 02 | Bootstrap intervals and paired deltas |
| 03 | The `outcomes_file` adapter: one spec per dataset, outcomes per test record (correct or not) for the synthetic-trained and real-trained models, delta stated |
| 04 | Not on the path: no model vendor is called. Recorded so that nobody looks for the ledger |
| 07 | Nothing by contract. Both are the privacy story; 07 redacts documents, this measures tables |

## 6. Week by week

Relative weeks of evenings and weekends, alongside 16.

| Week | Built | Done when |
|---|---|---|
| 1 | Terms quoted; loaders, subsets, splits, leakage check; preprocessing; the synthesiser interface with all six methods and their accountants recorded; the full grid of tables (three datasets, six methods, five budgets plus non-DP, three seeds) generated with timings | `docs/data.md`, `docs/synthesisers.md`; every table on disk with its seed, budget and wall-clock |
| 2 | The three legal-test attacks from the paper, with control and baseline; the Groundhog attack; DCR; the reference-library agreement report; utility (TSTR per task, ceiling and floor, marginal error) | Every risk and utility number in section 1 with its interval; the agreement report written |
| 3 | The surface and the recommendation rule; the 03 gate run; the leak table; the static explorer; README tables from `facsimile report`; `docs/rejected.md`; `v0.1.0`; repository public; privacy.peterparker.ca live; the status flip logged on peterparker.ca | Every number in section 1 in the README; the site live |
| slack | One week | |

First to drop if behind: the SPARCS dataset (if its terms were slow to confirm), then the
third seed, then TVAE (CTGAN stays as the deep non-DP arm), then the three-way marginal error.
None is in the definition of done. The three legal-test attacks with control sets, the
Groundhog attack, TSTR utility, the DP marginal methods, the surface with a recommendation and
the reference agreement are not droppable.

## 7. Cost

No model vendor is called. Compute is the cost, and most of it is CPU: AIM and MST run on
CPU (the benchmark reports no GPU speed-up) at minutes to tens of minutes per table on
20-attribute data. CTGAN, TVAE and PATE-CTGAN train on a GPU; the 4 GB desktop card runs them
at the chosen subset sizes, with a rented L4-class card as the fallback for the largest
tables. Prices as of 2026-10-16.

Amended 2026-10-17: AIM is far slower than this estimate (epsilon 2 takes 2.6 to 4.2 hours per
table on the desktop, epsilon 4 more than 10), and the Groundhog attack needs 60 AIM fits per
target. Those run on one rented 32-vCPU spot instance (`deploy/aws`) with four spend controls:
the queue powers it off when done, a 72-hour power-off armed at boot, a spot price cap and a
budget alert. The cheaper m5 and m5a spot types were tried first; AWS's spot advisor put their
interruption rate in ca-central-1 over 20 percent, and the first m5a.8xlarge was interrupted ten
minutes after launch, which a day-long AIM fit would not survive. m6a.8xlarge is under 5 percent.
The deep-synthesiser GPU line is not needed; the desktop card was enough.

| Item | Basis | US$ | CA$ |
|---|---|---:|---:|
| Deep synthesisers on rented GPU, if the desktop card is too slow | Not needed (amended 2026-10-17): the desktop card ran the whole deep grid | 0 | 0 |
| Marginal synthesisers | CPU on the desktop, about 40 hours of wall-clock across the grid | 0 | 0 |
| AIM grid cells and Groundhog AIM fits (amended 2026-10-17) | One m6a.8xlarge spot instance in ca-central-1, about 50 hours at US$0.50, capped at 72 hours and US$0.55 an hour | 25 to 40 | 34 to 54 |
| Attacks and utility | CPU | 0 | 0 |
| The diffusion arm (section 2.11, added 2026-10-28) | The desktop GPU; rented only on Peter's go | 0 | 0 |
| Singling out over five searches (section 2.12, added 2026-11-01) | The desktop CPU | 0 | 0 |
| Storage for the table grid | Local; nothing raw is committed | 0 | 0 |
| Demo site | Azure Static Web Apps free tier | 0 | 0 |
| **Total** | | **25 to 40** | **34 to 54** |

Budgeted at the project file's **CA$55**, outside the plan's lines as the alongside projects
are; the estimate was about CA$10, is CA$34 to 54 since the AIM amendment (the top of the range is
every cap binding at once), and any remainder buys, in order, a second state-year of ACS,
a fourth seed, and a longer PATE-CTGAN schedule. Actuals go to STATUS next to the estimate.

## 8. Handover and reuse

`facsimile` v0.1.0 at the end of week 3. The attack package is importable on any pair of
real and synthetic tables with a control set, which is the reusable half nobody ships. The
surface charts and the leak table feed a short public note if Rule E ever extends to a fourth
write-up; it does not now.

## 9. Risks

| Risk | Handling |
|---|---|
| SPARCS terms narrower than expected | Read and quoted on day one; the set is dropped rather than bent, and the README says so |
| An attack implementation that is not the paper's | The reference agreement report; a disagreement is resolved and recorded before any number ships |
| A wrong epsilon | No hand-rolled accounting; each library's accountant named with its version; the accountant test |
| Naming a leak reads as an accusation | Section 2.7: library, version, configuration, measurement; a property of settings on this data |
| Re-identification concerns on census data | Section 2.1: attacks stay inside the dataset, nothing is joined, no record is named; the Census terms quoted beside the rule |
| The deep synthesisers do not fit on 4 GB | Subsets sized in week 1; the rented card is the fallback and costs about CA$8 |
| Employer boundary | None. De-identification is practice at the employer, not a built system (Peter, 2026-10-16); public data only, nothing shared, no internal design reproduced |

## 10. Rule C candidates

1. **Distance to closest record is a privacy metric.** DCR beside the attacks on every table.
   Expected: tables with comfortable DCR on which inference and singling out succeed well
   above control, because DCR measures copying and the risks the law names are not copying.
2. **Deep DP synthesis is competitive with marginal DP synthesis.** PATE-CTGAN against AIM
   and MST at equal epsilon. Expected: lower utility at every budget, as the 2025 benchmark
   found, with the gap measured here on these datasets.
3. **Non-DP synthesis is private enough.** CTGAN and the copula at epsilon infinity.
   Expected: singling out and inference above control with intervals that exclude it, which
   is the finding the project exists to show.
4. **Membership inference can see through DP at epsilon of one or less.** The Groundhog
   attack on AIM and MST at small budgets. Expected: at chance, which is what the guarantee
   promises; a null result published as evidence that the guarantee held under attack.

Whichever produces the clearest evidence becomes `docs/rejected.md`.

## 11. Definition of done

- [x] Three datasets (or two, with the reason) fetched by loaders with checksums, terms quoted, subsets and splits published with the leakage check
- [x] Six synthesisers behind one interface, five budgets plus non-DP, three seeds, accountants and versions recorded, timings per table (AIM at epsilon 4 and 8 not run, section 2.2)
- [x] Singling out, linkability and inference implemented from the paper with control and baseline, risks with intervals on every table
- [x] Groundhog membership inference and DCR on every table
- [x] Reference-library agreement report
- [x] Utility as TSTR per task against ceiling and floor, with paired intervals; marginal query error
- [x] The epsilon-utility-risk surface per dataset and synthesiser with the recommendation rule applied and stated
- [x] Non-inferiority of the recommended configuration through the 03 gate (none was recommended; the nearest, `docs/gate.md`)
- [x] The leak table in the README: library, version, configuration, measurement
- [ ] privacy.peterparker.ca live with the explorer
- [x] Attack package released as reusable code with its own tests (`facsimile.attacks.evaluate`, `facsimile evaluate`, `docs/attack-package.md`)
- [x] One rejected approach documented with evidence (Rule C)
- [ ] Repository public, `v0.1.0` tagged, the status flip logged on peterparker.ca

## 12. Deferred

| Deferred | Kept so the door stays open |
|---|---|
| Defences: post-processing synthetic tables to lower a measured risk, and what it costs in utility | The attacks take any table; a defence is a step before them |
| A second state-year or a second country's census microdata | A loader and a subset file |
| Text and time-series synthesis | Out of the attack definitions' reach as written |
| AIM at epsilon 4 and 8 on the full grid (amended 2026-10-18 and 2026-10-27) | The cells are in the grid and the job file; a larger machine and budget run them unchanged |
| A write-up | Rule E names 02, 03 and 09; the leak table is a figure for the 03 post if it fits |

## 13. Name

**Chosen 2026-10-16: Share the Data, Not the People.** The promise in six words; the one-liner
carries the measurement (three datasets of real people, six methods, the attacks) and the
finding. "Privacy-Safe Data Sharing" named the subject and nothing else. The candidates as
weighed, two rounds:

1. **Fake Data, Real People: Which Synthetic Tables Leak**: the finding in the name, in the
   shape of 02 and 06.
2. **Shareable Data, Attacked Before It Is Shared**: the outcome and the method's argument.
3. **The Data You Can Share, and the Proof It Is Safe**: the buyer's question answered.
4. **Privacy-Safe Data Sharing**: keep it and let the one-liner carry everything.
5. Second round, after Peter found 2 to 4 close but not right: **Share the Data, Not the
   People** (chosen), How Much a Synthetic Table Gives Away, Released Only After It Survives
   the Attacks, The Same Patterns, None of the People, The Price of Privacy, in Data You Can
   Share.

Repository, package and slug stay as they are whichever is chosen.
