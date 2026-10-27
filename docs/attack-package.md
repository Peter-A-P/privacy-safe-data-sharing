# The attacks on your own tables

The attacks in `facsimile/attacks` are the ones every number in this repository comes from. They
need no part of the rest of the project: no dataset loader, no synthesiser, no grid.
`facsimile.attacks.evaluate` runs all of them on any real and synthetic pair in one call.

## What you need

Three tables with the same columns:

- **targets:** real records the synthesiser was trained on. These are the people whose
  privacy is being measured.
- **control:** as many real records from the same population, held out from training.
- **synthetic:** the table under test.

Hold the control set out *before* fitting the synthesiser, or there is nothing to compare against.
The targets can be the whole training set or a sample of it. The control must be the same size,
because the risk compares two success rates over the same number of attacks.

## What it runs

```python
from facsimile.attacks.evaluate import evaluate

result = evaluate(targets, control, synthetic, secret="income")
```

| Attack | Question | Paper |
|---|---|---|
| Singling out, univariate and multivariate | Can a predicate learned from the synthetic table isolate exactly one real person? | Giomi et al., PoPETs 2023 |
| Linkability, at k neighbours | Given two halves of a person's attributes held in separate places, does the synthetic table join them? | Giomi et al. |
| Inference | Given everything about a person but one attribute, does the synthetic table give that attribute away? | Giomi et al. |
| Distance to closest record | Is a synthetic record nearer the targets than the control? Reported, never used as risk ([rejected.md](rejected.md)) | |

Each attack runs against the targets and, identically, against the control. The risk is the
excess success on the targets, `(targets - control) / (1 - control)`, with a 95% Wilson interval
propagated from both rates. A synthetic table that has learned the population, which is its job,
helps the attacker on everyone equally and scores zero. Only what it learned about the people in
its training data counts. `detected` lists the attacks whose interval excludes zero.

Options:
- `secret`: the column the inference attack guesses.
- `link_a`, `link_b`: the two halves for linkability. By default these are the other columns,
  alternately.
- `n_attacks` (2,000, capped at the number of targets), `n_cols` (3 attributes per multivariate
  predicate), `k_values` ((1, 10)) and `seed`.
- `columns`: a fixed coding.

The membership inference attack (`groundhog.py`) is not in the one-call path. It needs the
synthesiser itself, refitted about 60 times per target, not one table.

## Raw tables and the coding

Every attack works on coded columns, as every synthesiser here does (`facsimile/prep.py`):
- categories rarer than half a percent merge into `OTHER`;
- numeric columns fall into uniform bins;
- missing values get their own code.

With no `columns` given:
- a numeric column with more than 20 distinct values is binned into 10 between the control's
  minimum and maximum;
- every other column is categorical, with its categories read from the control.

Nothing about the coding is read from the targets, so the coding cannot reveal anything about
the people the attacks ask about. To use a codebook instead, pass `columns` as a list of
`prep.Categorical(name, values=...)` and `prep.Numeric(name, lo, hi, bins)`.

## From the command line

```bash
facsimile evaluate targets.csv control.csv synthetic.parquet --secret income --out result.json
```

This prints a table and writes every rate, interval and parameter to `result.json`. Here is the
table for the independent table of the tests, which knows nothing about its targets:

| Attack | Success on targets, % | Success on control, % | Risk, % (95% CI) | Detected |
|---|---|---|---|---|
| singling out, univariate | 0.5 | 0.3 | 0.2 (0.0 to 0.7) | no |
| singling out, multivariate | 12.9 | 14.6 | 0.0 (0.0 to 2.6) | no |
| linkability, 1 neighbour | 0.3 | 0.3 | 0.0 (0.0 to 0.5) | no |
| linkability, 10 neighbours | 3.6 | 3.0 | 0.7 (0.0 to 2.7) | no |
| inference | 46.5 | 44.4 | 3.9 (0.0 to 13.8) | no |

Inference succeeds on 46.5% of the targets, far above chance, and that is not a leak. The table
is useful: it predicts the secret just as well for the control, 44.4%. The excess is what
counts, and its interval includes zero.

## What a result means

- **A detected risk** is a measurement, not a verdict on the method. It is a property of that
  synthesiser, version, configuration and table, on that data. This project names it that way
  in its leak table.
- **No detected risk** means these attacks, at this many attempts, could not tell the targets from
  the control. It is not a proof of safety. A stronger attack, or more attempts, might.
- **Every interval matters.** A 95% interval excludes zero by chance about one time in twenty,
  so across many attacks and tables expect a few chance detections. The project's leak table
  pools seeds and uses a Bonferroni level across the five attacks for that reason
  ([attacks.md](attacks.md)).

## Checked

- `tests/test_evaluate.py` runs the sanity pair through this entry point on raw tables. A copy
  of the training data must be caught, by inference and linkability. A table independent of the
  targets must score at control level on every attack.
- `tests/test_attack_sanity.py` runs the same pair on the attacks directly.
- On this project's 48 configurations, the implementations agree with Anonymeter, the reference
  library: every interval overlaps ([attacks.md](attacks.md)).
