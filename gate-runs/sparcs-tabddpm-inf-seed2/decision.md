## Gate: BLOCK

Spec `facsimile-sparcs-tabddpm-inf-seed2` (ba298bb7291c6f1f).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 2 (table sha256 6cb37d79679c)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 84.7% (83.4 to 86.0) | -1.1% (-2.2 to -0.1) | -2% | 0.102 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 86.6% (85.6 to 87.5) | -1.4% (-2.1 to -0.6) | -2% | 0.102 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -1.1% (-2.2% to -0.1%) over 2913 items, 141 worse and 108 better (p 0.051, Holm 0.102)
- high_charge: cannot rule out a 2% drop: -1.4% (-2.1% to -0.6%) over 4885 items, 219 worse and 153 better (p 0.051, Holm 0.102)
