# Results

Written by `facsimile report` from the records in `results/`; do not edit by hand.
Risks are percentages, pooled over the seeds, with 95% intervals; **leak** marks a risk
whose interval at 1 - 0.05/5 excludes zero. Utility is AUC(synthetic) minus
AUC(real ceiling), the mean over seeds, with the worst seed's lower 95% bound; the rule
asks that bound to sit above -0.02 on every task and seed. Membership is Groundhog
accuracy at about 1,000 rows over six targets (chance is 0.5).

Library versions: sdv 2.0.0, smartnoise-synth 1.0.8, opendp 0.14.2, lightgbm 4.7.0, scikit-learn 1.9.1, anonymeter 1.1.0.

## ACS PUMS, California 2018

| Synthesiser | Epsilon | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, income | Utility, employment | 2-way marginal error | Closer to training (DCR) | Fit seconds (median) | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaussian copula | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.9) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 1.7 (0.4 to 3.0) | 0.492 (0.399 to 0.584) | -0.282 (worst seed lo -0.296) | -0.245 (worst seed lo -0.257) | 0.107 | 0.497 | 7 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.6 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.7) | 0.1 (0.0 to 2.0) | pending | -0.062 (worst seed lo -0.075) | -0.047 (worst seed lo -0.062) | 0.167 | 0.509 | 706 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.1) | 0.7 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 2.1) | pending | -0.053 (worst seed lo -0.077) | -0.043 (worst seed lo -0.052) | 0.189 | 0.505 | 185 | 3 |
| MST | 0.5 | 0.0 (0.0 to 0.0) | 1.5 (0.2 to 2.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.6) |  | -0.360 (worst seed lo -0.410) | -0.228 (worst seed lo -0.251) | 0.166 | 0.442 | 68 | 3 |
| MST | 1 | 0.0 (0.0 to 0.0) | 0.7 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.2 (0.0 to 1.7) | 0.483 (0.391 to 0.576) | -0.347 (worst seed lo -0.396) | -0.148 (worst seed lo -0.166) | 0.158 | 0.463 | 57 | 3 |
| MST | 2 | 0.0 (0.0 to 0.0) | 1.4 (0.0 to 2.7) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.3) | 0.3 (0.0 to 1.7) |  | -0.312 (worst seed lo -0.333) | -0.162 (worst seed lo -0.183) | 0.154 | 0.447 | 56 | 3 |
| MST | 4 | 0.0 (0.0 to 0.0) | 1.5 (0.2 to 2.8) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.6) | 1.4 (0.0 to 2.8) |  | -0.306 (worst seed lo -0.346) | -0.166 (worst seed lo -0.181) | 0.153 | 0.453 | 55 | 3 |
| MST | 8 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.6) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.6 (0.0 to 2.0) | 0.475 (0.383 to 0.568) | -0.315 (worst seed lo -0.341) | -0.169 (worst seed lo -0.181) | 0.152 | 0.447 | 56 | 3 |
| AIM | 0.5 | 0.0 (0.0 to 0.0) | 1.4 (0.1 to 2.6) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.2) |  | -0.157 (worst seed lo -0.263) | -0.175 (worst seed lo -0.198) | 0.124 | 0.483 | 952 | 3 |
| AIM | 1 | 0.0 (0.0 to 0.0) | 1.0 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 2.5 (0.7 to 4.4) **leak** | 0.517 (0.424 to 0.609) | -0.132 (worst seed lo -0.180) | -0.147 (worst seed lo -0.239) | 0.090 | 0.492 | 2,390 | 3 |
| AIM | 2 | 0.0 (0.0 to 0.0) | 0.7 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.6) | 1.7 (0.0 to 3.7) |  | -0.102 (worst seed lo -0.140) | -0.171 (worst seed lo -0.234) | 0.070 | 0.490 | 9,533 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.5) |  | -0.373 (worst seed lo -0.425) | -0.326 (worst seed lo -0.347) | 0.592 | 0.521 | 13 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 1.2) | pending | -0.377 (worst seed lo -0.425) | -0.313 (worst seed lo -0.356) | 0.556 | 0.515 | 25 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 0.7) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.4 (0.0 to 1.7) |  | -0.402 (worst seed lo -0.476) | -0.316 (worst seed lo -0.350) | 0.427 | 0.510 | 68 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.7) |  | -0.417 (worst seed lo -0.477) | -0.336 (worst seed lo -0.402) | 0.239 | 0.508 | 256 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 1.4) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.9) | pending | -0.339 (worst seed lo -0.409) | -0.306 (worst seed lo -0.378) | 0.341 | 0.490 | 993 | 3 |

## IEEE-CIS card transactions

| Synthesiser | Epsilon | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, fraud | 2-way marginal error | Closer to training (DCR) | Fit seconds (median) | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaussian copula | inf | pending | pending | pending | pending | pending | 0.417 (0.327 to 0.510) | pending |  |  | 9 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.8) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.8) | pending | -0.129 (worst seed lo -0.167) | 0.173 | 0.492 | 843 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.9) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.9) | pending | -0.101 (worst seed lo -0.152) | 0.306 | 0.513 | 185 | 3 |
| MST | 0.5 | pending | pending | pending | pending | pending |  | pending |  |  | 88 | 3 |
| MST | 1 | pending | pending | pending | pending | pending | 0.517 (0.424 to 0.609) | pending |  |  | 79 | 3 |
| MST | 2 | pending | pending | pending | pending | pending |  | pending |  |  | 98 | 3 |
| MST | 4 | pending | pending | pending | pending | pending |  | pending |  |  | 88 | 3 |
| MST | 8 | pending | pending | pending | pending | pending | 0.542 (0.448 to 0.633) | pending |  |  | 90 | 3 |
| AIM | 0.5 | pending | pending | pending | pending | pending |  | pending |  |  | 1,097 | 3 |
| AIM | 1 | pending | pending | pending | pending | pending | 0.492 (0.399 to 0.584) | -0.166 (worst seed lo -0.207) | 0.100 |  | 3,532 | 3 |
| AIM | 2 | pending | pending | pending | pending | pending |  | pending |  |  | 33,549 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.3) |  | -0.392 (worst seed lo -0.477) | 0.675 | 0.484 | 11 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.5) | pending | -0.378 (worst seed lo -0.439) | 0.632 | 0.497 | 22 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.4) | 0.0 (0.0 to 0.9) |  | -0.318 (worst seed lo -0.429) | 0.466 | 0.493 | 63 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.1 (0.0 to 2.0) |  | -0.341 (worst seed lo -0.436) | 0.186 | 0.526 | 227 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 1.1) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.7) | pending | -0.387 (worst seed lo -0.484) | 0.189 | 0.512 | 1,020 | 3 |

## NY SPARCS discharges

| Synthesiser | Epsilon | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, long_stay | Utility, high_charge | 2-way marginal error | Closer to training (DCR) | Fit seconds (median) | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaussian copula | inf | pending | pending | pending | pending | pending | 0.458 (0.367 to 0.552) | -0.186 (worst seed lo -0.197) | -0.203 (worst seed lo -0.213) | 0.103 |  | 9 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 0.8) | 0.0 (0.0 to 0.5) | pending | -0.075 (worst seed lo -0.087) | -0.061 (worst seed lo -0.071) | 0.160 | 0.503 | 1,013 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.4) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.3) | 0.8 (0.0 to 2.7) | pending | -0.150 (worst seed lo -0.197) | -0.123 (worst seed lo -0.162) | 0.389 | 0.528 | 188 | 3 |
| MST | 0.5 | pending | pending | pending | pending | pending |  | pending | pending |  |  | 69 | 3 |
| MST | 1 | pending | pending | pending | pending | pending | 0.517 (0.424 to 0.609) | pending | pending |  |  | 62 | 3 |
| MST | 2 | pending | pending | pending | pending | pending |  | pending | pending |  |  | 59 | 3 |
| MST | 4 | pending | pending | pending | pending | pending |  | pending | pending |  |  | 57 | 3 |
| MST | 8 | pending | pending | pending | pending | pending | 0.508 (0.416 to 0.601) | pending | pending |  |  | 52 | 3 |
| AIM | 0.5 | pending | pending | pending | pending | pending |  | pending | pending |  |  | 1,694 | 3 |
| AIM | 1 | pending | pending | pending | pending | pending | 0.442 (0.351 to 0.535) | pending | pending |  |  | 9,736 | 3 |
| AIM | 2 | pending | pending | pending | pending | pending |  | pending | pending |  |  | 15,603 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.8 (0.0 to 1.6) |  | -0.378 (worst seed lo -0.434) | -0.350 (worst seed lo -0.392) | 0.548 | 0.502 | 13 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.9 (0.1 to 1.8) | pending | -0.389 (worst seed lo -0.442) | -0.361 (worst seed lo -0.400) | 0.502 | 0.499 | 26 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.1) |  | -0.375 (worst seed lo -0.408) | -0.337 (worst seed lo -0.362) | 0.368 | 0.493 | 77 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.8 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.6) | 0.0 (0.0 to 0.4) |  | -0.337 (worst seed lo -0.377) | -0.357 (worst seed lo -0.391) | 0.191 | 0.482 | 321 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.8) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.9) | pending | -0.346 (worst seed lo -0.401) | -0.291 (worst seed lo -0.316) | 0.331 | 0.476 | 1,004 | 3 |

## Hardware

Fit times were measured on:

- AWS m6a.8xlarge (AMD EPYC, 32 vCPU, 128 GB)
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz with NVIDIA GeForce GTX 1650
