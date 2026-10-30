## Gate: PASS

Spec `facsimile-ieeecis-tabddpm-inf-seed2` (0812d935a9aa07ca).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 2 (table sha256 a7cdc2035b09)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 82.0% (77.5 to 85.9) | -6.0% (-10.2 to -2.1) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
