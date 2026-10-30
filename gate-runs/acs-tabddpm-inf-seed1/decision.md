## Gate: BLOCK

Spec `facsimile-acs-tabddpm-inf-seed1` (83342cd264d8932e).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 1 (table sha256 4731f4c1410d)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 87.1% (85.8 to 88.4) | -1.7% (-2.7 to -0.6) | -2% | 0.553 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 81.6% (80.5 to 82.7) | -2.1% (-2.9 to -1.2) | -2% | 0.612 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -1.7% (-2.7% to -0.6%) over 2601 items, 124 worse and 80 better (p 0.277, Holm 0.553)
- employment: cannot rule out a 2% drop: -2.1% (-2.9% to -1.2%) over 4417 items, 230 worse and 136 better (p 0.612, Holm 0.612)
