## Gate: BLOCK

Spec `facsimile-sparcs-aim-eps2-seed0` (f8c5660354b43fc2).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 2, seed 0 (table sha256 9da2e0af043a)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 68.7% (67.0 to 70.3) | -17.1% (-18.9 to -15.3) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 73.6% (72.3 to 74.8) | -14.4% (-15.7 to -13.0) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -17.1% (-18.9% to -15.3%) over 2913 items, 663 worse and 165 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -14.4% (-15.7% to -13.0%) over 4885 items, 946 worse and 245 better (p 1.000, Holm 1.000)
