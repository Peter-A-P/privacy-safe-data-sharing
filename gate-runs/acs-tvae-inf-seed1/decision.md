## Gate: BLOCK

Spec `facsimile-acs-tvae-inf-seed1` (449592eaa6825056).

Baseline `lightgbm trained on the real training split`, candidate `lightgbm trained on tvae, no privacy, seed 1 (table sha256 189afbb4ab90)`.

| Suite | Paired items | Baseline | Candidate | Difference | Margin | Holm p | Verdict |
|---|---:|---|---|---|---:|---:|---|
| income | 2601 | 88.8% (87.6 to 90.0) | 83.7% (82.3 to 85.1) | -5.1% (-6.4 to -3.8) | -2% | 1.000 | block |
| employment | 4417 | 83.7% (82.6 to 84.8) | 79.9% (78.7 to 81.1) | -3.8% (-4.8 to -2.8) | -2% | 1.000 | block |

Difference is candidate minus baseline, paired by item, with its 95% bootstrap interval. A suite passes when the whole interval sits above the margin after Holm's adjustment across the decided suites; an under-powered suite warns and is not decided.

**Reasons**

- income: cannot rule out a 2% drop: -5.1% (-6.4% to -3.8%) over 2601 items, 218 worse and 86 better (p 1.000, Holm 1.000)
- employment: cannot rule out a 2% drop: -3.8% (-4.8% to -2.8%) over 4417 items, 355 worse and 186 better (p 1.000, Holm 1.000)
