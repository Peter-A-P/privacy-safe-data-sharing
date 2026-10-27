## Gate: BLOCK

Spec `facsimile-acs-tvae-inf-seed2` (6f662fccfc8ea826).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tvae, no privacy, seed 2 (table sha256 b9027e18393c)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 86.4% (85.1 to 87.7) | -2.3% (-3.6 to -1.2) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 78.4% (77.2 to 79.6) | -5.3% (-6.4 to -4.2) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -2.3% (-3.6% to -1.2%) over 2601 items, 157 worse and 96 better (p 0.712, Holm 1.000)
- employment: cannot rule out a 2% drop: -5.3% (-6.4% to -4.2%) over 4417 items, 431 worse and 195 better (p 1.000, Holm 1.000)
