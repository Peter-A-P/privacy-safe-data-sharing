## Gate: BLOCK

Spec `facsimile-sparcs-ctgan-inf-seed0` (e1deff003443a48e).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on ctgan, no privacy, seed 0 (table sha256 88b396288fc8)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 78.2% (76.7 to 79.6) | -7.6% (-9.0 to -6.1) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 81.2% (80.1 to 82.3) | -6.7% (-7.7 to -5.6) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -7.6% (-9.0% to -6.1%) over 2913 items, 346 worse and 124 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -6.7% (-7.7% to -5.6%) over 4885 items, 521 worse and 195 better (p 1.000, Holm 1.000)
