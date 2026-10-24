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

The resolution, which is to adopt the one-hot encoding and rerun or to publish the difference as
it stands, is recorded here once it is decided.
