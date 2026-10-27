## Gate: BLOCK

Spec `facsimile-acs-tvae-inf-seed0` (38767274ab4a3d39).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tvae, no privacy, seed 0 (table sha256 876539f03f91)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 82.6% (81.2 to 84.0) | -6.2% (-7.6 to -4.7) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 79.2% (78.0 to 80.4) | -4.5% (-5.5 to -3.3) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -6.2% (-7.6% to -4.7%) over 2601 items, 268 worse and 108 better (p 1.000, Holm 1.000)
- employment: cannot rule out a 2% drop: -4.5% (-5.5% to -3.3%) over 4417 items, 416 worse and 218 better (p 1.000, Holm 1.000)
