## Gate: BLOCK

Spec `facsimile-sparcs-tabddpm-inf-seed0` (fd70d344c7b0cee4).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 0 (table sha256 979e5475f126)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 84.4% (83.1 to 85.8) | -1.3% (-2.4 to -0.3) | -2% | 0.107 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 86.7% (85.8 to 87.7) | -1.2% (-2.0 to -0.4) | -2% | 0.042 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -1.3% (-2.4% to -0.3%) over 2913 items, 136 worse and 97 better (p 0.107, Holm 0.107)
- high_charge: cannot rule out a 2% drop: -1.2% (-2.0% to -0.4%) over 4885 items, 219 worse and 160 better (p 0.021, Holm 0.042)
