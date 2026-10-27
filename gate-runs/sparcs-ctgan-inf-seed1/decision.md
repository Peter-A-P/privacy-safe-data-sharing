## Gate: BLOCK

Spec `facsimile-sparcs-ctgan-inf-seed1` (eafbd8527023dda1).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on ctgan, no privacy, seed 1 (table sha256 442b4d24c95f)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 78.4% (76.9 to 79.9) | -7.4% (-8.8 to -5.9) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 82.0% (80.9 to 83.1) | -5.9% (-6.9 to -4.8) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -7.4% (-8.8% to -5.9%) over 2913 items, 341 worse and 126 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -5.9% (-6.9% to -4.8%) over 4885 items, 477 worse and 189 better (p 1.000, Holm 1.000)
