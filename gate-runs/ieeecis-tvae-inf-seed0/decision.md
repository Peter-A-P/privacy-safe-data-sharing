## Gate: PASS

Spec `facsimile-ieeecis-tvae-inf-seed0` (f57911c80f117031).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tvae, no privacy, seed 0 (table sha256 798f303885fc)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 70.6% (65.5 to 75.4) | -17.4% (-22.5 to -12.3) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
