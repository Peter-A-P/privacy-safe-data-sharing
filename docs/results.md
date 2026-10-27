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
| Gaussian copula | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.9) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 1.7 (0.4 to 3.0) | 0.425 (0.335 to 0.519) | -0.282 (worst seed lo -0.296) | -0.245 (worst seed lo -0.257) | 0.107 | 0.497 | 7 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.6 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.7) | 0.1 (0.0 to 2.0) | 0.417 (0.327 to 0.510) | -0.062 (worst seed lo -0.075) | -0.047 (worst seed lo -0.062) | 0.167 | 0.509 | 706 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.1) | 0.7 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 2.1) | 0.450 (0.359 to 0.543) | -0.053 (worst seed lo -0.077) | -0.043 (worst seed lo -0.052) | 0.189 | 0.505 | 185 | 3 |
| MST | 0.5 | 0.0 (0.0 to 0.0) | 1.5 (0.2 to 2.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.6) |  | -0.360 (worst seed lo -0.410) | -0.228 (worst seed lo -0.251) | 0.166 | 0.442 | 68 | 3 |
| MST | 1 | 0.0 (0.0 to 0.0) | 0.7 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.2 (0.0 to 1.7) | 0.508 (0.416 to 0.601) | -0.347 (worst seed lo -0.396) | -0.148 (worst seed lo -0.166) | 0.158 | 0.463 | 57 | 3 |
| MST | 2 | 0.0 (0.0 to 0.0) | 1.4 (0.0 to 2.7) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.3) | 0.3 (0.0 to 1.7) |  | -0.312 (worst seed lo -0.333) | -0.162 (worst seed lo -0.183) | 0.154 | 0.447 | 56 | 3 |
| MST | 4 | 0.0 (0.0 to 0.0) | 1.5 (0.2 to 2.8) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.6) | 1.4 (0.0 to 2.8) |  | -0.306 (worst seed lo -0.346) | -0.166 (worst seed lo -0.181) | 0.153 | 0.453 | 55 | 3 |
| MST | 8 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.6) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.6 (0.0 to 2.0) | 0.458 (0.367 to 0.552) | -0.315 (worst seed lo -0.341) | -0.169 (worst seed lo -0.181) | 0.152 | 0.447 | 56 | 3 |
| AIM | 0.5 | 0.0 (0.0 to 0.0) | 1.4 (0.1 to 2.6) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.2) |  | -0.157 (worst seed lo -0.263) | -0.175 (worst seed lo -0.198) | 0.124 | 0.483 | 952 | 3 |
| AIM | 1 | 0.0 (0.0 to 0.0) | 1.0 (0.0 to 2.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 2.5 (0.7 to 4.4) **leak** | 0.533 (0.440 to 0.625) | -0.132 (worst seed lo -0.180) | -0.147 (worst seed lo -0.239) | 0.090 | 0.492 | 2,390 | 3 |
| AIM | 2 | 0.0 (0.0 to 0.0) | 0.7 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.6) | 1.7 (0.0 to 3.7) |  | -0.102 (worst seed lo -0.140) | -0.171 (worst seed lo -0.234) | 0.070 | 0.490 | 9,533 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  | 0.550 (0.457 to 0.641) |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.5) |  | -0.373 (worst seed lo -0.425) | -0.326 (worst seed lo -0.347) | 0.592 | 0.521 | 13 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 1.2) | 0.542 (0.448 to 0.633) | -0.377 (worst seed lo -0.425) | -0.313 (worst seed lo -0.356) | 0.556 | 0.515 | 25 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 0.7) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.4 (0.0 to 1.7) |  | -0.402 (worst seed lo -0.476) | -0.316 (worst seed lo -0.350) | 0.427 | 0.510 | 68 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.7) |  | -0.417 (worst seed lo -0.477) | -0.336 (worst seed lo -0.402) | 0.239 | 0.508 | 256 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 1.4) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.9) | 0.508 (0.416 to 0.601) | -0.339 (worst seed lo -0.409) | -0.306 (worst seed lo -0.378) | 0.341 | 0.490 | 993 | 3 |

## IEEE-CIS card transactions

| Synthesiser | Epsilon | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, fraud | 2-way marginal error | Closer to training (DCR) | Fit seconds (median) | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaussian copula | inf | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.2) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.4) | 0.425 (0.335 to 0.519) | -0.404 (worst seed lo -0.453) | 0.079 | 0.507 | 9 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.8) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.8) | 0.525 (0.432 to 0.617) | -0.129 (worst seed lo -0.167) | 0.173 | 0.492 | 843 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.9) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.9) | 0.500 (0.407 to 0.593) | -0.101 (worst seed lo -0.152) | 0.306 | 0.513 | 185 | 3 |
| MST | 0.5 | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.4) |  | -0.258 (worst seed lo -0.317) | 0.131 | 0.558 | 88 | 3 |
| MST | 1 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.0) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.7) | 0.0 (0.0 to 2.2) | 0.492 (0.399 to 0.584) | -0.311 (worst seed lo -0.354) | 0.121 | 0.542 | 79 | 3 |
| MST | 2 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.4) | 0.1 (0.0 to 2.4) |  | -0.227 (worst seed lo -0.318) | 0.120 | 0.535 | 98 | 3 |
| MST | 4 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 0.0) |  | -0.193 (worst seed lo -0.232) | 0.119 | 0.538 | 88 | 3 |
| MST | 8 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.3) | 0.558 (0.465 to 0.649) | -0.193 (worst seed lo -0.228) | 0.118 | 0.540 | 90 | 3 |
| AIM | 0.5 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.5) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 0.7) | 0.0 (0.0 to 1.9) |  | -0.262 (worst seed lo -0.451) | 0.117 | 0.519 | 1,097 | 3 |
| AIM | 1 | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 1.5) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 1.4) | 0.433 (0.343 to 0.527) | -0.166 (worst seed lo -0.207) | 0.100 | 0.522 | 3,532 | 3 |
| AIM | 2 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 1.8) |  | -0.148 (worst seed lo -0.209) | 0.061 | 0.507 | 33,549 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  | 0.458 (0.367 to 0.552) |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.3) |  | -0.392 (worst seed lo -0.477) | 0.675 | 0.484 | 11 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.5) | 0.458 (0.367 to 0.552) | -0.378 (worst seed lo -0.439) | 0.632 | 0.497 | 22 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.4) | 0.0 (0.0 to 0.9) |  | -0.318 (worst seed lo -0.429) | 0.466 | 0.493 | 63 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.1 (0.0 to 2.0) |  | -0.341 (worst seed lo -0.436) | 0.186 | 0.526 | 227 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 1.1) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.7) | 0.533 (0.440 to 0.625) | -0.387 (worst seed lo -0.484) | 0.189 | 0.512 | 1,020 | 3 |

## NY SPARCS discharges

| Synthesiser | Epsilon | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, long_stay | Utility, high_charge | 2-way marginal error | Closer to training (DCR) | Fit seconds (median) | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gaussian copula | inf | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.8) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.5) | 0.3 (0.0 to 1.4) | 0.542 (0.448 to 0.633) | -0.186 (worst seed lo -0.197) | -0.203 (worst seed lo -0.213) | 0.103 | 0.499 | 9 | 3 |
| CTGAN | inf | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 0.8) | 0.0 (0.0 to 0.5) | 0.475 (0.383 to 0.568) | -0.075 (worst seed lo -0.087) | -0.061 (worst seed lo -0.071) | 0.160 | 0.503 | 1,013 | 3 |
| TVAE | inf | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.4) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.3) | 0.8 (0.0 to 2.7) | 0.483 (0.391 to 0.576) | -0.150 (worst seed lo -0.197) | -0.123 (worst seed lo -0.162) | 0.389 | 0.528 | 188 | 3 |
| MST | 0.5 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.4) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.4) | 0.0 (0.0 to 0.0) |  | -0.263 (worst seed lo -0.294) | -0.358 (worst seed lo -0.389) | 0.159 | 0.475 | 69 | 3 |
| MST | 1 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.8) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.4) | 0.0 (0.0 to 0.8) | 0.508 (0.416 to 0.601) | -0.242 (worst seed lo -0.264) | -0.305 (worst seed lo -0.334) | 0.149 | 0.490 | 62 | 3 |
| MST | 2 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.5) | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 0.6) | 0.0 (0.0 to 0.0) |  | -0.237 (worst seed lo -0.251) | -0.288 (worst seed lo -0.311) | 0.145 | 0.508 | 59 | 3 |
| MST | 4 | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 1.7) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 0.8) |  | -0.236 (worst seed lo -0.254) | -0.292 (worst seed lo -0.308) | 0.144 | 0.490 | 57 | 3 |
| MST | 8 | 0.0 (0.0 to 0.0) | 0.9 (0.0 to 2.3) | 0.0 (0.0 to 0.1) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 0.4) | 0.500 (0.407 to 0.593) | -0.245 (worst seed lo -0.264) | -0.289 (worst seed lo -0.304) | 0.144 | 0.492 | 52 | 3 |
| AIM | 0.5 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.7) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.5) |  | -0.203 (worst seed lo -0.246) | -0.206 (worst seed lo -0.296) | 0.119 | 0.500 | 1,694 | 3 |
| AIM | 1 | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.2) | 0.0 (0.0 to 0.1) | 0.2 (0.0 to 0.5) | 0.9 (0.0 to 2.8) | 0.442 (0.351 to 0.535) | -0.124 (worst seed lo -0.155) | -0.175 (worst seed lo -0.284) | 0.097 | 0.508 | 9,736 | 3 |
| AIM | 2 | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.6) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.5) | 0.4 (0.0 to 2.3) |  | -0.144 (worst seed lo -0.167) | -0.144 (worst seed lo -0.162) | 0.074 | 0.503 | 15,603 | 3 |
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; deferred (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  | 0.450 (0.359 to 0.543) |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.8 (0.0 to 1.6) |  | -0.378 (worst seed lo -0.434) | -0.350 (worst seed lo -0.392) | 0.548 | 0.502 | 13 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.9 (0.1 to 1.8) | 0.508 (0.416 to 0.601) | -0.389 (worst seed lo -0.442) | -0.361 (worst seed lo -0.400) | 0.502 | 0.499 | 26 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.1) |  | -0.375 (worst seed lo -0.408) | -0.337 (worst seed lo -0.362) | 0.368 | 0.493 | 77 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.8 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.6) | 0.0 (0.0 to 0.4) |  | -0.337 (worst seed lo -0.377) | -0.357 (worst seed lo -0.391) | 0.191 | 0.482 | 321 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.8) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.9) | 0.550 (0.457 to 0.641) | -0.346 (worst seed lo -0.401) | -0.291 (worst seed lo -0.316) | 0.331 | 0.476 | 1,004 | 3 |

## Reference agreement: this project against Anonymeter

48 tables attacked by both, on the same targets, control and synthetic table.
A pair agrees on the call when both or neither detect a risk at 95%; the intervals
overlap when the two risks' 95% intervals share any point. Differences are in risk
percentage points.

| Attack | Pairs | Same call | Intervals overlap | Mean difference | Largest difference |
|---|---|---|---|---|---|
| singling out, univariate | 48 | 100.0% | 100.0% | 0.0 | 0.0 |
| singling out, multivariate | 48 | 97.9% | 100.0% | 0.5 | 1.7 |
| linkability, 1 neighbour | 48 | 100.0% | 100.0% | 0.0 | 0.1 |
| linkability, 10 neighbours | 48 | 89.6% | 100.0% | 0.1 | 0.6 |
| inference | 48 | 95.8% | 100.0% | 0.4 | 3.5 |

Disagreements (8): a different call, or intervals that do not overlap.

| Table | Attack | This project, risk % | Anonymeter, risk % | Success on targets, this project vs Anonymeter, % | Control, % |
|---|---|---|---|---|---|
| acs pate_ctgan epsilon 2 seed 0 | linkability, 10 neighbours | 0.5 (0.0 to 1.0) | 0.5 (0.1 to 0.9) | 1.0 vs 0.7 | 0.5 vs 0.2 |
| acs pate_ctgan epsilon 2 seed 0 | inference | 1.7 (0.0 to 3.8) | 2.3 (0.2 to 4.4) | 11.4 vs 11.7 | 9.8 vs 9.6 |
| ieeecis mst epsilon 0.5 seed 0 | singling out, multivariate | 2.1 (0.1 to 4.0) | 0.7 (0.0 to 2.8) | 10.1 vs 10.8 | 8.2 vs 10.2 |
| ieeecis pate_ctgan epsilon 1 seed 0 | linkability, 10 neighbours | 0.3 (0.0 to 0.6) | 0.4 (0.0 to 0.8) | 0.5 vs 0.6 | 0.2 vs 0.2 |
| sparcs mst epsilon 8 seed 0 | linkability, 10 neighbours | 0.0 (0.0 to 0.6) | 0.6 (0.0 to 1.1) | 1.1 vs 1.1 | 1.1 vs 0.5 |
| sparcs pate_ctgan epsilon 2 seed 0 | inference | 1.8 (0.2 to 3.4) | 1.3 (0.0 to 2.9) | 7.5 vs 7.2 | 5.8 vs 6.0 |
| sparcs pate_ctgan epsilon 4 seed 0 | linkability, 10 neighbours | 0.6 (0.1 to 1.0) | 0.0 (0.0 to 0.4) | 0.8 vs 0.5 | 0.3 vs 0.5 |
| sparcs pate_ctgan epsilon 8 seed 0 | linkability, 10 neighbours | 0.2 (0.0 to 0.7) | 0.5 (0.0 to 1.0) | 0.7 vs 0.9 | 0.5 vs 0.4 |

The causes, where the two implementations differ by design, are in `docs/attacks.md`.

## Reference agreement: Groundhog against TAPAS

The same shadow and evaluation tables, scored by this project's feature map and
classifier and by TAPAS's (tapas 1.0.0 at a7069d7 (privacy-sdg-toolbox)). Accuracy over six targets
and 20 evaluation tables each, with exact 95% intervals; chance is 0.5. *Copy* is the
positive control: the attacked table is the real dataset itself.

| Dataset | Tables | This project | TAPAS |
|---|---|---|---|
| ACS PUMS, California 2018 | Gaussian copula, epsilon inf | 0.425 (0.335 to 0.519) | 0.492 (0.399 to 0.584) |
| ACS PUMS, California 2018 | copy (control), epsilon inf | 0.558 (0.465 to 0.649) | 0.642 (0.549 to 0.727) |
| IEEE-CIS card transactions | Gaussian copula, epsilon inf | 0.425 (0.335 to 0.519) | 0.517 (0.424 to 0.609) |
| IEEE-CIS card transactions | copy (control), epsilon inf | 0.550 (0.457 to 0.641) | 0.617 (0.524 to 0.704) |
| NY SPARCS discharges | Gaussian copula, epsilon inf | 0.542 (0.448 to 0.633) | 0.492 (0.399 to 0.584) |
| NY SPARCS discharges | copy (control), epsilon inf | 0.525 (0.432 to 0.617) | 0.525 (0.432 to 0.617) |

What the difference means is in `docs/attacks.md`.

## Hardware

Fit times were measured on:

- AWS m6a.8xlarge (AMD EPYC, 32 vCPU, 128 GB)
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz with NVIDIA GeForce GTX 1650
