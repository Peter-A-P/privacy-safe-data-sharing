# Results

Written by `facsimile report` from the records in `results/`; do not edit by hand.
Risks are percentages, pooled over the seeds, with 95% intervals; **leak** marks a risk
whose interval at 1 - 0.05/5 excludes zero. Utility is AUC(synthetic) minus
AUC(real ceiling), the mean over seeds, with the worst seed's lower 95% bound; the rule
asks that bound to sit above -0.02 on every task and seed. Membership is Groundhog
accuracy at about 1,000 rows over six targets (chance is 0.5).

Library versions: sdv 2.0.0, smartnoise-synth 1.0.8, opendp 0.14.2, lightgbm 4.7.0, scikit-learn 1.9.1, anonymeter 1.1.0, facsimile 0.0.1.

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
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; left out to stay in budget (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
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
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; left out to stay in budget (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |
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
| AIM | 4 | not run: AIM at epsilon 4 needed more than 28 hours per table and up to 53 GB (SPARCS, seed 1) on a 32-vCPU, 128 GB machine; left out to stay in budget (PLAN.md section 2.2) |  |  |  |  |  |  |  |  |  |  |  |
| AIM | 8 | not run: AIM at epsilon 8 grew to 25 GB in under five hours on ACS and none of nine tables finished on a 32-vCPU, 128 GB machine; dropped for now (PLAN.md section 2.2) |  |  |  |  | 0.450 (0.359 to 0.543) |  |  |  |  |  |  |
| PATE-CTGAN | 0.5 (spent 0.69) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.1) | 0.0 (0.0 to 0.0) | 0.1 (0.0 to 0.4) | 0.8 (0.0 to 1.6) |  | -0.378 (worst seed lo -0.434) | -0.350 (worst seed lo -0.392) | 0.548 | 0.502 | 13 | 3 |
| PATE-CTGAN | 1 (spent 1.10) | 0.0 (0.0 to 0.0) | 0.5 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.9 (0.1 to 1.8) | 0.508 (0.416 to 0.601) | -0.389 (worst seed lo -0.442) | -0.361 (worst seed lo -0.400) | 0.502 | 0.499 | 26 | 3 |
| PATE-CTGAN | 2 (spent 2.06) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.0) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.1) |  | -0.375 (worst seed lo -0.408) | -0.337 (worst seed lo -0.362) | 0.368 | 0.493 | 77 | 3 |
| PATE-CTGAN | 4 (spent 4.02) | 0.0 (0.0 to 0.0) | 0.8 (0.0 to 1.7) | 0.0 (0.0 to 0.1) | 0.3 (0.0 to 0.6) | 0.0 (0.0 to 0.4) |  | -0.337 (worst seed lo -0.377) | -0.357 (worst seed lo -0.391) | 0.191 | 0.482 | 321 | 3 |
| PATE-CTGAN | 8 (spent 8.02) | 0.0 (0.0 to 0.0) | 0.4 (0.0 to 1.8) | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.9) | 0.550 (0.457 to 0.641) | -0.346 (worst seed lo -0.401) | -0.291 (worst seed lo -0.316) | 0.331 | 0.476 | 1,004 | 3 |

## The leakage ladder

Four methods people use as synthetic or anonymised data, expected to leak, run through the
same pipeline as the grid as its positive controls (PLAN.md section 2.10). They are not on
the surface, in the leak table or among the gate's candidates.

| Dataset | Method | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference | Membership | Utility, worst task | Seeds |
|---|---|---|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | Perturbed copy | 0.0 (0.0 to 0.0) | 1.7 (0.7 to 2.7) **leak** | 3.2 (2.8 to 3.7) **leak** | 18.5 (17.5 to 19.6) **leak** | 18.5 (16.6 to 20.3) **leak** | 0.575 (0.481 to 0.665) | -0.014 (employment) | 3 |
| ACS PUMS, California 2018 | SMOTE-NC | 0.0 (0.0 to 0.0) | 5.6 (3.7 to 7.4) **leak** | 0.6 (0.4 to 0.9) **leak** | 10.4 (9.5 to 11.3) **leak** | 27.8 (25.7 to 29.8) **leak** | 0.558 (0.465 to 0.649) | -0.009 (employment) | 3 |
| ACS PUMS, California 2018 | k-anonymity, k = 5 | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.3) | 0.1 (0.0 to 0.1) | 2.7 (2.0 to 3.4) **leak** | 9.3 (7.3 to 11.3) **leak** | 0.508 (0.416 to 0.601) | -0.019 (employment) | 3 |
| ACS PUMS, California 2018 | TVAE, 3,000 epochs | 0.0 (0.0 to 0.0) | 1.5 (0.2 to 2.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 1.6) | 0.500 (0.407 to 0.593) | -0.068 (employment) | 3 |
| IEEE-CIS card transactions | Perturbed copy | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.5) | 0.3 (0.2 to 0.5) **leak** | 5.6 (4.8 to 6.3) **leak** | 7.7 (5.7 to 9.8) **leak** | 0.508 (0.416 to 0.601) | -0.050 (fraud) | 3 |
| IEEE-CIS card transactions | SMOTE-NC | 0.0 (0.0 to 0.0) | 1.9 (0.7 to 3.1) **leak** | 0.9 (0.6 to 1.1) **leak** | 12.5 (11.5 to 13.6) **leak** | 38.6 (36.4 to 40.8) **leak** | 0.475 (0.383 to 0.568) | -0.043 (fraud) | 3 |
| IEEE-CIS card transactions | k-anonymity, k = 5 | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 0.8) | 0.1 (0.0 to 0.2) | 4.0 (3.3 to 4.7) **leak** | 6.1 (3.8 to 8.5) **leak** | 0.458 (0.367 to 0.552) | -0.082 (fraud) | 3 |
| IEEE-CIS card transactions | TVAE, 3,000 epochs | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.1) | 1.4 (0.0 to 3.8) | 0.492 (0.399 to 0.584) | -0.131 (fraud) | 3 |
| NY SPARCS discharges | Perturbed copy | 0.0 (0.0 to 0.0) | 0.3 (0.0 to 1.3) | 3.9 (3.4 to 4.4) **leak** | 27.5 (26.3 to 28.7) **leak** | 57.6 (55.8 to 59.4) **leak** | 0.500 (0.407 to 0.593) | -0.010 (high_charge) | 3 |
| NY SPARCS discharges | SMOTE-NC | 0.0 (0.0 to 0.1) | 2.1 (0.4 to 3.8) | 1.2 (0.9 to 1.5) **leak** | 14.7 (13.7 to 15.8) **leak** | 32.1 (29.8 to 34.5) **leak** | 0.433 (0.343 to 0.527) | -0.009 (high_charge) | 3 |
| NY SPARCS discharges | k-anonymity, k = 5 | 0.0 (0.0 to 0.0) | 0.2 (0.0 to 1.7) | 0.2 (0.0 to 0.3) | 4.6 (3.8 to 5.3) **leak** | 4.9 (2.7 to 7.0) **leak** | 0.517 (0.424 to 0.609) | -0.033 (long_stay) | 3 |
| NY SPARCS discharges | TVAE, 3,000 epochs | 0.0 (0.0 to 0.1) | 1.0 (0.0 to 2.3) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.1) | 0.575 (0.481 to 0.665) | -0.078 (long_stay) | 3 |

## The most exposed records

The same attacks on the same tables, on the quarter of the targets most unusual against
the quarter of the control most unusual, ranked by mean distance to 2,000 test-split
records (`facsimile/attacks/exposed.py`): 500 against 500 per seed, seeds pooled.

| Dataset | Configuration | singling out, univariate | singling out, multivariate | linkability, 1 neighbour | linkability, 10 neighbours | inference |
|---|---|---|---|---|---|---|
| ACS PUMS, California 2018 | Gaussian copula, epsilon inf | 0.0 (0.0 to 0.2) | 0.4 (0.0 to 1.7) | 0.2 (0.0 to 0.5) | 0.0 (0.0 to 0.3) | 2.2 (0.0 to 5.0) |
| ACS PUMS, California 2018 | CTGAN, epsilon inf | 0.0 (0.0 to 0.2) | 1.5 (0.0 to 3.1) | 0.0 (0.0 to 0.2) | 0.7 (0.0 to 1.7) | 1.8 (0.0 to 5.7) |
| ACS PUMS, California 2018 | TVAE, epsilon inf | 0.1 (0.0 to 0.3) | 2.2 (0.1 to 4.3) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.9) | 3.9 (0.1 to 7.8) |
| ACS PUMS, California 2018 | MST, epsilon 0.5 | 0.0 (0.0 to 0.2) | 2.1 (0.1 to 4.2) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 1.5) |
| ACS PUMS, California 2018 | MST, epsilon 1 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.6) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.2) | 4.6 (1.9 to 7.4) **leak** |
| ACS PUMS, California 2018 | MST, epsilon 2 | 0.0 (0.0 to 0.2) | 1.2 (0.0 to 3.4) | 0.0 (0.0 to 0.2) | 0.3 (0.0 to 0.8) | 1.4 (0.0 to 4.2) |
| ACS PUMS, California 2018 | MST, epsilon 4 | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 2.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.4) | 3.0 (0.3 to 5.8) |
| ACS PUMS, California 2018 | MST, epsilon 8 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 2.1) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.5) | 0.8 (0.0 to 3.6) |
| ACS PUMS, California 2018 | AIM, epsilon 0.5 | 0.0 (0.0 to 0.2) | 1.8 (0.0 to 3.8) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.4) | 1.3 (0.0 to 4.6) |
| ACS PUMS, California 2018 | AIM, epsilon 1 | 0.0 (0.0 to 0.2) | 2.2 (0.5 to 3.9) **leak** | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.6) | 7.2 (3.8 to 10.7) **leak** |
| ACS PUMS, California 2018 | AIM, epsilon 2 | 0.0 (0.0 to 0.2) | 0.3 (0.0 to 1.8) | 0.1 (0.0 to 0.3) | 0.1 (0.0 to 1.1) | 5.5 (2.0 to 9.0) **leak** |
| ACS PUMS, California 2018 | PATE-CTGAN, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 1.1) |
| ACS PUMS, California 2018 | PATE-CTGAN, epsilon 1 | 0.0 (0.0 to 0.2) | 0.5 (0.0 to 1.2) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.0) |
| ACS PUMS, California 2018 | PATE-CTGAN, epsilon 2 | 0.0 (0.0 to 0.2) | 1.0 (0.3 to 1.8) **leak** | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 0.8) | 0.0 (0.0 to 2.3) |
| ACS PUMS, California 2018 | PATE-CTGAN, epsilon 4 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.3) | 0.0 (0.0 to 0.2) | 0.3 (0.0 to 0.9) | 0.0 (0.0 to 1.5) |
| ACS PUMS, California 2018 | PATE-CTGAN, epsilon 8 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 0.3) |
| IEEE-CIS card transactions | Gaussian copula, epsilon inf | 0.0 (0.0 to 0.2) | 0.7 (0.0 to 2.1) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 3.6) |
| IEEE-CIS card transactions | CTGAN, epsilon inf | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 1.4) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.6) | 0.1 (0.0 to 4.8) |
| IEEE-CIS card transactions | TVAE, epsilon inf | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 1.8) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 4.0) |
| IEEE-CIS card transactions | MST, epsilon 0.5 | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 1.9) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 1.5) | 1.2 (0.0 to 5.4) |
| IEEE-CIS card transactions | MST, epsilon 1 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.8) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.2) | 0.0 (0.0 to 3.5) |
| IEEE-CIS card transactions | MST, epsilon 2 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.1) | 0.0 (0.0 to 0.2) | 0.9 (0.0 to 2.2) | 0.0 (0.0 to 5.0) |
| IEEE-CIS card transactions | MST, epsilon 4 | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 1.0) | 0.0 (0.0 to 0.2) | 0.4 (0.0 to 1.8) | 0.0 (0.0 to 0.0) |
| IEEE-CIS card transactions | MST, epsilon 8 | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.2) | 0.3 (0.0 to 1.6) | 0.0 (0.0 to 2.8) |
| IEEE-CIS card transactions | AIM, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.5 (0.0 to 2.5) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 1.3) | 0.0 (0.0 to 2.9) |
| IEEE-CIS card transactions | AIM, epsilon 1 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.5) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.8) | 0.8 (0.0 to 5.5) |
| IEEE-CIS card transactions | AIM, epsilon 2 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.9) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.1) | 0.0 (0.0 to 3.0) |
| IEEE-CIS card transactions | PATE-CTGAN, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.3) | 0.1 (0.0 to 0.3) | 0.1 (0.0 to 0.7) | 0.0 (0.0 to 1.6) |
| IEEE-CIS card transactions | PATE-CTGAN, epsilon 1 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.1 (0.0 to 0.3) | 0.1 (0.0 to 0.5) | 0.0 (0.0 to 1.9) |
| IEEE-CIS card transactions | PATE-CTGAN, epsilon 2 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.0) |
| IEEE-CIS card transactions | PATE-CTGAN, epsilon 4 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 0.5) |
| IEEE-CIS card transactions | PATE-CTGAN, epsilon 8 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 0.5) | 0.3 (0.0 to 4.2) |
| NY SPARCS discharges | Gaussian copula, epsilon inf | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 1.1) | 0.1 (0.0 to 0.3) | 0.0 (0.0 to 0.4) | 0.0 (0.0 to 0.1) |
| NY SPARCS discharges | CTGAN, epsilon inf | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.5) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.7) | 0.0 (0.0 to 0.0) |
| NY SPARCS discharges | TVAE, epsilon inf | 0.1 (0.0 to 0.3) | 1.2 (0.0 to 3.9) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 1.0) | 0.0 (0.0 to 1.0) |
| NY SPARCS discharges | MST, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.5 (0.0 to 3.3) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.6) | 0.0 (0.0 to 0.8) |
| NY SPARCS discharges | MST, epsilon 1 | 0.0 (0.0 to 0.2) | 1.8 (0.0 to 4.4) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 0.9) | 0.0 (0.0 to 2.0) |
| NY SPARCS discharges | MST, epsilon 2 | 0.0 (0.0 to 0.2) | 0.4 (0.0 to 3.0) | 0.0 (0.0 to 0.2) | 0.8 (0.0 to 1.6) | 0.0 (0.0 to 0.0) |
| NY SPARCS discharges | MST, epsilon 4 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.3) | 0.0 (0.0 to 0.2) | 0.3 (0.0 to 1.1) | 0.0 (0.0 to 0.0) |
| NY SPARCS discharges | MST, epsilon 8 | 0.0 (0.0 to 0.2) | 0.7 (0.0 to 3.0) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 0.9) | 0.0 (0.0 to 0.0) |
| NY SPARCS discharges | AIM, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 1.7) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 0.8) |
| NY SPARCS discharges | AIM, epsilon 1 | 0.0 (0.0 to 0.2) | 1.3 (0.0 to 3.3) | 0.0 (0.0 to 0.2) | 0.2 (0.0 to 1.0) | 0.0 (0.0 to 0.9) |
| NY SPARCS discharges | AIM, epsilon 2 | 0.0 (0.0 to 0.2) | 0.4 (0.0 to 2.3) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.5) | 0.0 (0.0 to 2.9) |
| NY SPARCS discharges | PATE-CTGAN, epsilon 0.5 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.5) | 1.5 (0.0 to 3.1) |
| NY SPARCS discharges | PATE-CTGAN, epsilon 1 | 0.0 (0.0 to 0.2) | 0.7 (0.0 to 1.8) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.6) | 1.5 (0.0 to 3.2) |
| NY SPARCS discharges | PATE-CTGAN, epsilon 2 | 0.0 (0.0 to 0.2) | 0.9 (0.1 to 1.8) | 0.0 (0.0 to 0.2) | 0.1 (0.0 to 0.6) | 1.2 (0.0 to 3.2) |
| NY SPARCS discharges | PATE-CTGAN, epsilon 4 | 0.0 (0.0 to 0.2) | 0.6 (0.0 to 2.1) | 0.0 (0.0 to 0.2) | 0.8 (0.2 to 1.4) **leak** | 0.0 (0.0 to 1.5) |
| NY SPARCS discharges | PATE-CTGAN, epsilon 8 | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 2.2) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.3) | 1.1 (0.0 to 2.9) |
| ACS PUMS, California 2018 | Perturbed copy, epsilon inf | 0.0 (0.0 to 0.2) | 1.3 (0.0 to 2.7) | 8.9 (7.5 to 10.4) **leak** | 32.4 (29.9 to 35.0) **leak** | 22.7 (18.8 to 26.6) **leak** |
| ACS PUMS, California 2018 | SMOTE-NC, epsilon inf | 0.0 (0.0 to 0.2) | 3.7 (1.1 to 6.4) **leak** | 1.1 (0.5 to 1.8) **leak** | 12.7 (10.6 to 14.9) **leak** | 29.9 (25.6 to 34.1) **leak** |
| ACS PUMS, California 2018 | k-anonymity, k = 5, epsilon inf | 0.0 (0.0 to 0.2) | 0.5 (0.0 to 3.2) | 0.1 (0.0 to 0.4) | 3.0 (1.6 to 4.5) **leak** | 8.5 (4.3 to 12.7) **leak** |
| ACS PUMS, California 2018 | TVAE, 3,000 epochs, epsilon inf | 0.0 (0.0 to 0.1) | 1.8 (0.0 to 3.9) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.2) | 4.1 (0.4 to 7.9) |
| IEEE-CIS card transactions | Perturbed copy, epsilon inf | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.2) | 0.4 (0.0 to 0.8) | 6.8 (4.9 to 8.7) **leak** | 9.0 (5.0 to 13.0) **leak** |
| IEEE-CIS card transactions | SMOTE-NC, epsilon inf | 0.0 (0.0 to 0.2) | 2.1 (0.0 to 4.7) | 0.7 (0.1 to 1.2) | 14.3 (11.8 to 16.8) **leak** | 37.9 (33.5 to 42.3) **leak** |
| IEEE-CIS card transactions | k-anonymity, k = 5, epsilon inf | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 2.1) | 0.0 (0.0 to 0.3) | 4.0 (2.0 to 5.9) **leak** | 6.4 (1.7 to 11.2) **leak** |
| IEEE-CIS card transactions | TVAE, 3,000 epochs, epsilon inf | 0.0 (0.0 to 0.3) | 0.0 (0.0 to 2.2) | 0.0 (0.0 to 0.3) | 0.4 (0.0 to 1.9) | 8.4 (3.7 to 13.2) **leak** |
| NY SPARCS discharges | Perturbed copy, epsilon inf | 0.0 (0.0 to 0.1) | 0.0 (0.0 to 0.9) | 6.6 (5.3 to 7.9) **leak** | 36.5 (33.9 to 39.1) **leak** | 70.0 (66.7 to 73.3) **leak** |
| NY SPARCS discharges | SMOTE-NC, epsilon inf | 0.2 (0.0 to 0.5) | 2.2 (0.0 to 4.8) | 1.4 (0.8 to 2.0) **leak** | 15.5 (13.3 to 17.6) **leak** | 29.7 (24.4 to 35.0) **leak** |
| NY SPARCS discharges | k-anonymity, k = 5, epsilon inf | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 2.1) | 0.1 (0.0 to 0.5) | 4.8 (3.3 to 6.3) **leak** | 3.1 (0.0 to 8.0) |
| NY SPARCS discharges | TVAE, 3,000 epochs, epsilon inf | 0.1 (0.0 to 0.3) | 0.1 (0.0 to 2.5) | 0.0 (0.0 to 0.2) | 0.0 (0.0 to 0.0) | 0.0 (0.0 to 1.2) |

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

## Through the 03 gate: synthetic-trained against real-trained

Project 03's release gate, asked whether a model trained on the synthetic table is
non-inferior to the same model trained on the real data, at a margin of 2
points. An item is a disjoint pair of one positive and one negative real test record,
correct when the model scores the positive higher, so the share correct estimates the
AUC. Difference is synthetic minus real, in points, with the gate's 95% paired bootstrap
interval. The candidates, per dataset, are the configuration nearest the real-data
ceiling and the nearest with a privacy budget (`facsimile/gate.py`, `docs/gate.md`).

| Dataset | Candidate | Seed | Gate | Task: difference, points (95% CI), items |
|---|---|---|---|---|
| ACS PUMS, California 2018 | AIM, epsilon 1 | 0 | block | income: -12.5 (-14.1 to -10.8), 2,601; employment: -12.0 (-13.4 to -10.6), 4,417 |
| ACS PUMS, California 2018 | AIM, epsilon 1 | 1 | block | income: -17.0 (-18.8 to -15.2), 2,601; employment: -9.8 (-11.1 to -8.5), 4,417 |
| ACS PUMS, California 2018 | AIM, epsilon 1 | 2 | block | income: -9.0 (-10.6 to -7.4), 2,601; employment: -22.9 (-24.5 to -21.3), 4,417 |
| ACS PUMS, California 2018 | TVAE, epsilon inf | 0 | block | income: -6.2 (-7.6 to -4.7), 2,601; employment: -4.5 (-5.5 to -3.3), 4,417 |
| ACS PUMS, California 2018 | TVAE, epsilon inf | 1 | block | income: -5.1 (-6.4 to -3.8), 2,601; employment: -3.8 (-4.8 to -2.8), 4,417 |
| ACS PUMS, California 2018 | TVAE, epsilon inf | 2 | block | income: -2.3 (-3.6 to -1.2), 2,601; employment: -5.3 (-6.4 to -4.2), 4,417 |
| IEEE-CIS card transactions | AIM, epsilon 2 | 0 | not decided | fraud: -12.3 (-16.8 to -7.8), 333 (power screen asks 370) |
| IEEE-CIS card transactions | AIM, epsilon 2 | 1 | not decided | fraud: -18.9 (-24.0 to -13.5), 333 (power screen asks 370) |
| IEEE-CIS card transactions | AIM, epsilon 2 | 2 | not decided | fraud: -18.6 (-23.4 to -13.5), 333 (power screen asks 370) |
| IEEE-CIS card transactions | TVAE, epsilon inf | 0 | not decided | fraud: -17.4 (-22.5 to -12.3), 333 (power screen asks 370) |
| IEEE-CIS card transactions | TVAE, epsilon inf | 1 | not decided | fraud: -8.4 (-13.2 to -3.6), 333 (power screen asks 370) |
| IEEE-CIS card transactions | TVAE, epsilon inf | 2 | not decided | fraud: -9.0 (-13.8 to -4.5), 333 (power screen asks 370) |
| NY SPARCS discharges | AIM, epsilon 2 | 0 | block | long_stay: -17.1 (-18.9 to -15.3), 2,913; high_charge: -14.4 (-15.7 to -13.0), 4,885 |
| NY SPARCS discharges | AIM, epsilon 2 | 1 | block | long_stay: -14.9 (-16.5 to -13.1), 2,913; high_charge: -15.3 (-16.7 to -13.9), 4,885 |
| NY SPARCS discharges | AIM, epsilon 2 | 2 | block | long_stay: -13.0 (-14.7 to -11.2), 2,913; high_charge: -13.8 (-15.1 to -12.5), 4,885 |
| NY SPARCS discharges | CTGAN, epsilon inf | 0 | block | long_stay: -7.6 (-9.0 to -6.1), 2,913; high_charge: -6.7 (-7.7 to -5.6), 4,885 |
| NY SPARCS discharges | CTGAN, epsilon inf | 1 | block | long_stay: -7.4 (-8.8 to -5.9), 2,913; high_charge: -5.9 (-6.9 to -4.8), 4,885 |
| NY SPARCS discharges | CTGAN, epsilon inf | 2 | block | long_stay: -7.0 (-8.3 to -5.5), 2,913; high_charge: -5.6 (-6.6 to -4.6), 4,885 |

## Data

SPARCS: source New York State Department of Health, Hospital Inpatient Discharges
(SPARCS De-Identified): 2024, Health Data NY dataset `sf4k-39ay`, published 2025-10-10,
accessed 2026-10-16. The New York State Department of Health makes no representation,
warranty or guarantee relating to the data or analyses derived from these data. The terms
of all three sets are in `docs/data.md`.

## Hardware

Fit times were measured on:

- AWS m6a.8xlarge (AMD EPYC, 32 vCPU, 128 GB)
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz
- Intel(R) Core(TM) i5-10400F CPU @ 2.90GHz with NVIDIA GeForce GTX 1650
