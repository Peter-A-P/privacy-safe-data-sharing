## Gate: BLOCK

Spec `facsimile-sparcs-ctgan-inf-seed2` (e4d13c66f4dd94d5).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on ctgan, no privacy, seed 2 (table sha256 a75f55b529f1)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 78.8% (77.3 to 80.3) | -7.0% (-8.3 to -5.5) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 82.3% (81.2 to 83.4) | -5.6% (-6.6 to -4.6) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -7.0% (-8.3% to -5.5%) over 2913 items, 338 worse and 135 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -5.6% (-6.6% to -4.6%) over 4885 items, 463 worse and 188 better (p 1.000, Holm 1.000)
