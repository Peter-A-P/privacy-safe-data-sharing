## Gate: PASS

Spec `facsimile-ieeecis-aim-eps2-seed1` (ef5cb18d55f11466).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on aim, epsilon 2, seed 1 (table sha256 e8829e363552)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| fraud | 333 | 88.0% (84.1 to 91.3) | 69.1% (64.0 to 74.2) | -18.9% (-24.0 to -13.5) | -2% | not decided | warn |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- pass: 0 of 1 suites decided, none inferior
- under-powered, not decided: fraud
