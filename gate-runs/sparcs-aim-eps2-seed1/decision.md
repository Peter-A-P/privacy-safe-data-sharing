## Gate: BLOCK

Spec `facsimile-sparcs-aim-eps2-seed1` (b93d71dabebe06d7).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 2, seed 1 (table sha256 ad1353ca9ed6)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 70.9% (69.3 to 72.5) | -14.9% (-16.5 to -13.1) | -2% | 1.000 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 72.6% (71.4 to 73.8) | -15.3% (-16.7 to -13.9) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -14.9% (-16.5% to -13.1%) over 2913 items, 596 worse and 163 better (p 1.000, Holm 1.000)
- high_charge: cannot rule out a 2% drop: -15.3% (-16.7% to -13.9%) over 4885 items, 1025 worse and 278 better (p 1.000, Holm 1.000)
