## Gate: PASS

Spec `facsimile-ieeecis-aim-eps2-seed0` (a931b2a3ff2d48eb).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 2, seed 0 (table sha256 641c5516d260)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 75.7% (70.9 to 80.2) | -12.3% (-16.8 to -7.8) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
