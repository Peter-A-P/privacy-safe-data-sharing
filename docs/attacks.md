# Attacks: the papers, the implementations, the reference agreement

Every attack in `facsimile/attacks/` is written from its paper and run beside the paper authors'
own library on the same tables. Where they disagree the disagreement is resolved and recorded
here before a number ships. Attacks stay inside the dataset: the targets and control are rows of
the dataset's own public file, nothing is joined to them, and no record is ever matched to a
person (`docs/data.md`).

## The three-way design

From Giomi et al., "A Unified Framework for Quantifying Privacy Risk in Synthetic Data",
Proceedings on Privacy Enhancing Technologies 2023(2). Each attack is run three times:

- **Main**: against 2,000 targets drawn from the training split, which the synthesiser saw.
- **Control**: against 2,000 control records it never saw, the same size so the rates compare
  without a size correction.
- **Baseline**: a version of the attack that ignores the synthetic table's records.

Success rates are Wilson score estimates. The risk is the main attack's excess over the
control, normalised by the room the control leaves, `(r_main - r_control) / (1 - r_control)`,
with first-order propagated error, bounded to [0, 1] (`facsimile/attacks/risk.py`). Success on
the control set is what the table teaches about anyone, which is the table being useful; only
the excess is about the people in it. A risk is called detected when its 95% interval excludes
zero, and a 95% interval excludes zero by chance about one time in twenty, so a single detection
is read with that in mind and the grid's three seeds are what a finding rests on.

## The attacks

| Attack | Paper | Implementation | Reference |
|---|---|---|---|
| Singling out, univariate and multivariate | Giomi et al. 2023, section 4.1 | `singling_out.py` | Anonymeter 1.1.0 `SinglingOutEvaluator` |
| Linkability | Giomi et al. 2023, section 4.2 | `linkability.py` | Anonymeter 1.1.0 `LinkabilityEvaluator` |
| Inference | Giomi et al. 2023, section 4.3 | `inference.py` | Anonymeter 1.1.0 `InferenceEvaluator` |
| Membership inference (Groundhog) | Stadler, Oprisanu and Troncoso, "Synthetic Data: Anonymisation Groundhog Day", USENIX Security 2022 | `groundhog.py`, `groundhog_run.py`; at about 1,000 rows, epsilon 1, 8 and infinity (PLAN.md 2.3) | TAPAS (MIT), in its own Python 3.10 environment |
| Distance to closest record | the vendors' metric | `dcr.py` | none: it is the thing under test (Rule C candidate 1) |

Per dataset (`facsimile/attacks/config.py`, fixed before any table was attacked): the inference
secret is the income band (ACS), the transaction amount band (IEEE-CIS) and the major diagnostic
category (SPARCS); the attacker knows every other attribute. The linkability halves are
who-you-are attributes against what-happened attributes. Singling out uses 2,000 predicates of
three attributes each; linkability is reported at k = 1 and k = 10 neighbours.

## Membership inference at about 1,000 rows

The Groundhog attack (Stadler et al. 2022) trains a random forest on synthetic tables made from
shadow datasets that do or do not contain one target, then asks it about fresh tables. Here, per
dataset: shadow datasets of 1,000 rows from a pool of 50,000 population records outside every
split, 40 shadow tables and 20 evaluation tables per target (each half with the target), six
targets (the three records farthest on average from the rest, and three at random), and the
paper's three feature sets (naive statistics, one-way histograms, pairwise correlations). The
score is accuracy against 0.5 with an exact interval, per target and pooled.

The sanity pair (`tests/test_groundhog.py`): a synthesiser that copies its input must give a
planted outlier away (it does, above 90%), and one that ignores its input must score chance.
Building it showed a limit of the paper's features worth stating: a target whose oddness lies
only in a combination of individually common values was close to invisible even through a
copying synthesiser (23 of 40 on the first attempt), because the features see a table through
its marginals and pairwise correlations. Outliers by mean distance are not all outliers in a
single attribute, so a low score on such a target is a statement about the features as well as
the synthesiser.

## Choices where the paper is silent, and what the reference does

**Ties between nearest neighbours.** The attributes are bins and categories, so many synthetic
records sit at exactly the same distance from a target, often zero. The paper does not say which
of them the attacker takes. Anonymeter takes whichever `numpy.argsort` puts first, which is an
accident of memory order and, for linkability, can make both halves pick the same low-index
record and link by coincidence. Here ties are broken uniformly at random, seeded, because an
attacker has no information that prefers one tied record to another
(`facsimile/attacks/neighbours.py`). The agreement report measures what this changes.

**Duplicate rows in singling out.** Anonymeter drops duplicate rows from every table before
making or counting predicates, so a predicate matching two identical real records counts as
singling one out. This project follows the reference here, so that the two can be compared, and
records it as a choice: two identical rows are two people, and the reference's count overstates
singling out when they are.

**The singling-out denominator.** Anonymeter divides successes by the number of predicates
requested, not the number it managed to find, and it stops looking after `max_attempts`. The
rate therefore depends on the search budget: on the ACS CTGAN table (seed 0) with 100,000
attempts it found 582 predicates and scored 2.4%, while this project's implementation, given
1,000,000 attempts, found all 2,000 and scored 8.7%, with the same success per predicate (about
8%) in both. Both implementations are run with the same budget, 1,000,000 attempts, and the
number found is recorded with every result. It is a property of the metric worth knowing: the
same table can be made to look safer by searching less.

**Distance.** Categorical attributes count 1 when they differ; binned numeric attributes count
the absolute difference in bin codes divided by the number of bins minus one, which is fixed by
the domain. Anonymeter scales by the observed range across the two tables, which equals the
domain's whenever both tables use the end bins.

## Licences

Anonymeter is under the Clear BSD licence; its authors, at Statice (now Anonos), have filed a
patent application on the method, and the README of the library says so. This project
reimplements the method from the paper for measurement and publishes no product. TAPAS is MIT.

## Reference agreement

Anonymeter 1.1.0 was run beside this project's implementations on seed 0 of every configuration
attacked (48 tables), with the same targets, control, synthetic table, secret, attribute halves,
number of attacks and search budget (`facsimile attack --reference`). The table, written by
`facsimile report`, is in [results.md](results.md#reference-agreement-this-project-against-anonymeter).

**The intervals agree everywhere.** For all five attacks on all 48 tables, the two risks' 95%
intervals overlap. The mean difference between the two risks is under 0.6 percentage points
for every attack. The largest is 3.5 points, the inference risk on IEEE-CIS MST at epsilon 0.5:
0.0% (0.0 to 2.5) here and 3.5% (0.0 to 7.3) in Anonymeter. Neither detects a risk there.

**The calls differ on 8 of 240 pairs, and every one is a borderline case.** In each of them one
implementation's lower bound is above zero by at most 0.18 points and the other's touches zero.
Five are linkability with ten neighbours, two are inference and one is multivariate singling
out. None is a leak in the README's sense, which pools the three seeds and tests at the
Bonferroni level. The one leak there (AIM, epsilon 1, ACS, inference) is detected by both on this
seed: 5.1% (1.8 to 8.3) here and 4.0% (0.7 to 7.3) in Anonymeter.

**The causes are the two choices recorded above.**

- *Ties between neighbours.* For linkability with ten neighbours and for inference, this project
  breaks ties at random, seeded. Anonymeter takes `numpy.argsort` order. On binned attributes
  most targets have many synthetic records at the same distance, so the two pick different
  records and the success rates move by a few tenths of a point in either direction. The control
  rates move too: on SPARCS MST at epsilon 8 the control linkability rate is 1.1% here and 0.5%
  in Anonymeter. That is the pattern a tie-break difference produces, and it is why the five
  linkability disagreements go both ways.
- *The singling-out search.* Both search with the same budget of 1,000,000 attempts, but they
  draw candidate predicates in a different order. On some tables neither finds all 2,000
  predicates (Anonymeter reported 972 to 1,491 on three SPARCS tables), and the two then score
  different predicate sets. The one multivariate singling-out disagreement (IEEE-CIS MST at
  epsilon 0.5) comes from the control rate: 8.2% here against 10.2% in Anonymeter.

Neither difference is a defect in either implementation. Both follow the paper, which leaves
these choices open. The project keeps its own choices for the reasons given above and reports its
own numbers, with the reference agreement published beside them.

## Reference agreement for Groundhog: TAPAS

TAPAS (privacy-sdg-toolbox, MIT, pinned at commit a7069d7) needs Python below 3.11, so it runs
in its own environment (`reference/tapas-requirements.txt`). `facsimile groundhog-reference`
rebuilds every shadow and evaluation table of a Groundhog run from its plan and seed. Each rebuilt
table reproduced the run's saved feature vector exactly. The command writes the tables to disk,
and `reference/tapas_groundhog.py` scores them with TAPAS's own Groundhog set classifier. The
table is in [results.md](results.md#reference-agreement-groundhog-against-tapas).

**The two feature maps differ in one respect.** TAPAS one-hot encodes categorical attributes
before it takes the naive features (mean, median, variance) and the correlations. This project
takes them on the category codes, which have no order. The histogram features are the same in
both.

**What that changes.** On the Gaussian copula tables both are at chance on all three datasets.
On the positive control, where the attacked table is the real dataset, the two differ:

| | Correct, of 360 evaluation trials | Accuracy |
|---|---|---|
| This project | 180 | 0.500 |
| TAPAS | 204 | 0.567 (0.514 to 0.618) |

So TAPAS's encoding is the stronger of the two, and this project's departs from the paper's.

Both are weak at this scale. Even on a copy of the training data neither is far above chance,
with 1,000 rows and 40 shadow tables per target. A Groundhog result at chance here therefore
means the attack could not tell, not that the table is safe. The README says so.

**Resolved 2026-10-24 (Peter's decision): adopt the encoding and rerun everything.** The feature
map now one-hot encodes categorical attributes for the naive and correlation sets, as TAPAS
does. Binned numeric attributes keep their bin code. Every Groundhog run, all six synthesisers
at their three budgets, was redone with it (finished 2026-10-27). The synthetic tables are now kept beside their
features, so a later change to the feature map will not need the synthesisers again. The first
runs' features are kept under `data/groundhog-v1/` and their results in the git history (up to
commit be0c360).

**A defect in TAPAS 1.0.0, found on the way.** `HistSetFeature` treats every column type that
starts with "finite" as one-hot. It reads as many encoded columns as the column has values, but a
`finite/ordered` column is encoded in a single column. Every histogram feature after the first
ordered column is therefore read from the wrong place. The first reference run described binned
numeric attributes as `finite/ordered` and was affected. They are now described as `real`, with
the bin code scaled to [0, 1], which TAPAS handles correctly. On the ACS positive control this
moved TAPAS from 72 to 77 correct of 120.

**After the rerun: the two agree.** With the new encoding, on the same tables (the table in
[results.md](results.md#reference-agreement-groundhog-against-tapas)):

| Tables, three datasets pooled | Correct, of 360 evaluation trials: this project | TAPAS |
|---|---|---|
| Copy (positive control) | 196 (0.544) | 214 (0.594) |
| Gaussian copula | 167 (0.464) | 180 (0.500) |

The gap that remains on the copy is the random forests' own noise. Both classifiers were refitted
on the copy tables with five other seeds (seed 1000 s + target, s = 0 to 4), everything else
unchanged. This project scored 195 to 218 correct (mean 207.4, 0.576) and TAPAS 199 to 215
(mean 204.6, 0.568). Each published count lies inside the other's range, and the two means are
within three trials of each other. So on these tables the feature maps are equally strong, the
departure from the paper is closed, and the disagreement is resolved. Both stay weak at this
scale: on a copy of the training data neither averages better than 0.58, which is the limitation
the README states.

## The leakage ladder: the attacks' positive controls

The grid detected one risk in 48 configurations. On its own that cannot say whether the tables
are safe or the attacks are weak. So four methods that people use as synthetic or anonymised
data, and that were expected to leak, went through exactly the same pipeline. Their settings and
expected outcomes were committed to PLAN.md section 2.10 (commit `2ee5029`) before any of them
ran. The methods are in `facsimile/synth/ladder.py`. The numbers are in
[results.md](results.md#the-leakage-ladder) and the README.

**The three regulators' attacks catch every rung they were given.** The perturbed copy, SMOTE-NC
and k-anonymity are each detected by two to four of the five attacks on every dataset. The
largest risks range from 4.9% (k-anonymity on SPARCS) to 57.6% (the perturbed copy's inference on
SPARCS), against at most 2.5% on any grid synthesiser. That is what makes a result at control
level on the grid mean something.

**Where each one leaks is where its design says it should.**

- **k-anonymity** is caught by inference and by linkability at ten neighbours, and never by
  singling out. It makes every record look like four others, which is what singling out tests.
  It leaves the secret as it was, which is what inference tests. That is the known weakness of
  k-anonymity (Machanavajjhala et al. 2007, l-diversity).
- **The perturbed copy and SMOTE-NC** are caught by inference and linkability everywhere. Both
  are also caught by multivariate singling out on ACS, and SMOTE-NC on IEEE-CIS too.
- **Univariate singling out** detects nothing anywhere, not even on the perturbed copy. In a
  binned domain with rare categories merged, almost no single value is unique to one person.
  That attack has no power on these coded tables, and its zeros on the grid say nothing.

**The leaky rungs are the useful ones.** On ACS and SPARCS, the perturbed copy and SMOTE-NC pass
the rule's usefulness test: within 0.02 AUC of the real-data model on every task and every seed.
No synthesiser in the grid reached that bar. A
release rule that looked only at usefulness would pick exactly the tables the attacks break.

**Distance to closest record flags all nine.** On these crude rungs, a share closer to training
than one half is the right warning, and every rung's interval sits above it. So the DCR check
catches copies and near-copies. What it cannot do is separate the subtle cases, and those are
the ones the grid contains ([rejected.md](rejected.md)).

**Membership inference at 1,000 rows sees none of them.** All nine are at chance. This is the
attack's weakness at this scale, already visible on the copy control. It is not evidence about
the rungs.

The fourth rung, TVAE at 3,000 epochs, is still running. It is the likeliest to show up in the
membership attack.

## The most exposed records

The grid's targets are 2,000 training records drawn at random, so most of them are ordinary.
Unusual people leak first. Each table was therefore attacked again on the quarter of its targets
that are most unusual, against the quarter of its control records that are most unusual,
measured the same way. That way the comparison stays like for like. How unusual a record is:
its mean mixed-type distance to a fixed sample of 2,000 test-split records, which no synthesiser
sees (`facsimile/attacks/exposed.py`). That gives 500 targets against 500 controls per seed,
pooled over three seeds, with the same Bonferroni level as the leak table.

**Six risks appear that the full target set does not show, all on differentially private
configurations.** By chance alone about 1.2 of the 240 tests would. The strongest are
inference on ACS:

| Configuration | Risk on all targets | Risk on the most exposed |
|---|---|---|
| AIM, epsilon 1 | 2.5% (0.7 to 4.4) | 7.2% (3.8 to 10.7) |
| AIM, epsilon 2 | 1.7% (0.0 to 3.7), not detected | 5.5% (2.0 to 9.0) |
| MST, epsilon 1 | 0.2% (0.0 to 1.7), not detected | 4.6% (1.9 to 7.4) |

Three smaller ones are at the edge of what chance could produce:
- multivariate singling out on AIM at epsilon 1;
- multivariate singling out on PATE-CTGAN at epsilon 2 on ACS;
- linkability at ten neighbours on PATE-CTGAN at epsilon 4 on SPARCS, 0.9% against 0.1%.

None of the three synthesisers without a privacy guarantee shows a risk on its exposed records.
That is not proof that they protect unusual people better, and the project did not test why. It
is reported as measured.

What this changes: a configuration that passes on randomly chosen targets can still give
unusual people away. Differential privacy's bound holds for every person, but at epsilon 1 and 2
it is loose enough for the excess on the most unusual quarter to be measurable. The leak table in
the README names the full-target leak. The exposed-records table sits beside it.
