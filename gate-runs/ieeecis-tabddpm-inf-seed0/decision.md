## Gate: PASS

Spec `facsimile-ieeecis-tabddpm-inf-seed0` (b74ab5689d8639d4).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tabddpm, no privacy, seed 0 (table sha256 5df1b2dd7c83)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 81.1% (76.6 to 85.3) | -6.9% (-11.4 to -2.4) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
