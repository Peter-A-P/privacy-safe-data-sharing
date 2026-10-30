## Gate: BLOCK

Spec `facsimile-acs-tabddpm-inf-seed2` (3657ea6ba098c295).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 2 (table sha256 4a2cd82c5d86)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 86.0% (84.7 to 87.4) | -2.7% (-3.8 to -1.6) | -2% | 0.900 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 82.0% (80.9 to 83.2) | -1.7% (-2.5 to -0.8) | -2% | 0.456 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -2.7% (-3.8% to -1.6%) over 2601 items, 145 worse and 74 better (p 0.900, Holm 0.900)
- employment: cannot rule out a 2% drop: -1.7% (-2.5% to -0.8%) over 4417 items, 231 worse and 157 better (p 0.228, Holm 0.456)
