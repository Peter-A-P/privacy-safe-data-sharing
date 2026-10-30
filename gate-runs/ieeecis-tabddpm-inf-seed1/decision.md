## Gate: PASS

Spec `facsimile-ieeecis-tabddpm-inf-seed1` (77af6de854c92aa1).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 1 (table sha256 5b4b907ba32b)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 79.6% (75.1 to 83.8) | -8.4% (-12.6 to -4.5) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
