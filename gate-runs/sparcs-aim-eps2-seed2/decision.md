## Gate: BLOCK

Spec `facsimile-sparcs-aim-eps2-seed2` (f4a1e5f7b940c57a).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 2, seed 2 (table sha256 85396b252410)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 72.8% (71.2 to 74.4) | -13.0% (-14.7 to -11.2) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 74.1% (72.8 to 75.3) | -13.8% (-15.1 to -12.5) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -13.0% (-14.7% to -11.2%) over 2913 items, 530 worse and 151 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -13.8% (-15.1% to -12.5%) over 4885 items, 908 worse and 232 better (p 1.000, Holm 1.000)
