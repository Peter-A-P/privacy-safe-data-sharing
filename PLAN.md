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

- [ ] Three datasets (or two, with the reason) fetched by loaders with checksums, terms quoted, subsets and splits published with the leakage check
- [ ] Six synthesisers behind one interface, five budgets plus non-DP, three seeds, accountants and versions recorded, timings per table
- [ ] Singling out, linkability and inference implemented from the paper with control and baseline, risks with intervals on every table
- [ ] Groundhog membership inference and DCR on every table
- [ ] Reference-library agreement report
- [ ] Utility as TSTR per task against ceiling and floor, with paired intervals; marginal query error
- [ ] The epsilon-utility-risk surface per dataset and synthesiser with the recommendation rule applied and stated
- [ ] Non-inferiority of the recommended configuration through the 03 gate
- [ ] The leak table in the README: library, version, configuration, measurement
- [ ] privacy.peterparker.ca live with the explorer
- [ ] Attack package released as reusable code with its own tests
- [ ] One rejected approach documented with evidence (Rule C)
- [ ] Repository public, `v0.1.0` tagged, the status flip logged on peterparker.ca

## 12. Deferred

| Deferred | Kept so the door stays open |
|---|---|
| Defences: post-processing synthetic tables to lower a measured risk, and what it costs in utility | The attacks take any table; a defence is a step before them |
| A second state-year or a second country's census microdata | A loader and a subset file |
| Text and time-series synthesis | Out of the attack definitions' reach as written |
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
