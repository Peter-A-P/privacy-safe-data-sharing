## Gate: BLOCK

Spec `facsimile-acs-aim-eps1-seed1` (4698b61cfc14226d).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 1, seed 1 (table sha256 cadc95aca2a1)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 71.8% (70.1 to 73.5) | -17.0% (-18.8 to -15.2) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 73.9% (72.6 to 75.2) | -9.8% (-11.1 to -8.5) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -17.0% (-18.8% to -15.2%) over 2601 items, 554 worse and 112 better (p 1.000, Holm 1.000)
- employment: cannot rule out a 2% drop: -9.8% (-11.1% to -8.5%) over 4417 items, 695 worse and 261 better (p 1.000, Holm 1.000)
