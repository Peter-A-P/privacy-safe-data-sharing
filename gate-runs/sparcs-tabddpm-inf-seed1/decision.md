## Gate: BLOCK

Spec `facsimile-sparcs-tabddpm-inf-seed1` (081ffe60ee17e306).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 1 (table sha256 a2ba71a6d72d)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| long_stay | 2913 | 85.8% (84.6 to 87.0) | 83.5% (82.2 to 84.9) | -2.3% (-3.4 to -1.2) | -2% | 0.684 | block |
| high_charge | 4885 | 87.9% (87.0 to 88.8) | 86.8% (85.8 to 87.7) | -1.1% (-1.9 to -0.4) | -2% | 0.034 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- long_stay: cannot rule out a 2% drop: -2.3% (-3.4% to -1.2%) over 2913 items, 166 worse and 100 better (p 0.684, Holm 0.684)
- high_charge: cannot rule out a 2% drop: -1.1% (-1.9% to -0.4%) over 4885 items, 211 worse and 155 better (p 0.017, Holm 0.034)
