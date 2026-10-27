## Gate: BLOCK

Spec `facsimile-acs-aim-eps1-seed0` (db48f01c6d9e330f).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 1, seed 0 (table sha256 4c6cc32cf466)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 76.3% (74.7 to 77.9) | -12.5% (-14.1 to -10.8) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 71.7% (70.4 to 73.0) | -12.0% (-13.4 to -10.6) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -12.5% (-14.1% to -10.8%) over 2601 items, 424 worse and 100 better (p 1.000, Holm 1.000)
- employment: cannot rule out a 2% drop: -12.0% (-13.4% to -10.6%) over 4417 items, 783 worse and 252 better (p 1.000, Holm 1.000)
