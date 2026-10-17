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

Written by `facsimile report` once the grid is attacked: for every table attacked by both, the
two risks and their intervals side by side, the share of tables where the two agree on whether a
risk is detected, and every disagreement with its explanation.
