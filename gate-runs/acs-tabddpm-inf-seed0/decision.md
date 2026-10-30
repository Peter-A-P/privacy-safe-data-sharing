## Gate: BLOCK

Spec `facsimile-acs-tabddpm-inf-seed0` (fc417a1a3413a083).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 0 (table sha256 9664ca51dda1)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 87.5% (86.2 to 88.7) | -1.3% (-2.5 to -0.2) | -2% | 0.116 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 82.4% (81.3 to 83.6) | -1.3% (-2.1 to -0.4) | -2% | 0.077 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -1.3% (-2.5% to -0.2%) over 2601 items, 130 worse and 96 better (p 0.116, Holm 0.116)
- employment: cannot rule out a 2% drop: -1.3% (-2.1% to -0.4%) over 4417 items, 197 worse and 141 better (p 0.038, Holm 0.077)
