## Gate: BLOCK

Spec `facsimile-acs-aim-eps1-seed2` (15a7031a72d878e3).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 1, seed 2 (table sha256 b5e46920f62b)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 79.7% (78.2 to 81.3) | -9.0% (-10.6 to -7.4) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 60.8% (59.3 to 62.2) | -22.9% (-24.5 to -21.3) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -9.0% (-10.6% to -7.4%) over 2601 items, 356 worse and 121 better (p 1.000, Holm 1.000)
- employment: cannot rule out a 2% drop: -22.9% (-24.5% to -21.3%) over 4417 items, 1323 worse and 310 better (p 1.000, Holm 1.000)
