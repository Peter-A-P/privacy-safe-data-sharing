# IEEE-CIS Fraud Detection, training transactions

Written by `facsimile build`; do not edit by hand.

- Population after the dataset's filter: 590,540 records
- Split seed 20261016: train 20,000, control 2,000, test 10,000, attack targets 2,000 drawn from train
- Split ids published: no, counts and hashes only
- Full contingency table: 3.16e+14 cells

## Attribute subset and domain

| Column | Kind | Codes | Labels |
|---|---|---:|---|
| `TransactionAmt` | numeric | 12 | [0, 1.37372), [1.37372, 4.63457), [4.63457, 12.3749), [12.3749, 30.7484), [30.7484, 74.3618), [74.3618, 177.888), [177.888, 423.631), [423.631, 1006.96), ... |
| `ProductCD` | categorical | 6 | C, H, R, S, W, OTHER |
| `card4` | categorical | 6 | american express, discover, mastercard, visa, OTHER, NA |
| `card6` | categorical | 4 | credit, debit, OTHER, NA |
| `addr1` | categorical | 41 | 110, 123, 126, 143, 177, 181, 184, 191, ... |
| `addr2` | categorical | 3 | 87, OTHER, NA |
| `dist1` | numeric | 9 | [0, 2.16232), [2.16232, 9.00025), [9.00025, 30.624), [30.624, 99.005), [99.005, 315.248), [315.248, 999.075), [999.075, 3161.55), [3161.55, 10000], ... |
| `P_emaildomain` | categorical | 16 | anonymous.com, aol.com, att.net, comcast.net, gmail.com, hotmail.com, icloud.com, live.com, ... |
| `R_emaildomain` | categorical | 14 | anonymous.com, aol.com, att.net, comcast.net, cox.net, gmail.com, hotmail.com, icloud.com, ... |
| `C1` | numeric | 8 | [0, 1.89989), [1.89989, 7.40939), [7.40939, 23.3863), [23.3863, 69.7177), [69.7177, 204.074), [204.074, 593.693), [593.693, 1723.55), [1723.55, 5000] |
| `C2` | numeric | 8 | [0, 1.89989), [1.89989, 7.40939), [7.40939, 23.3863), [23.3863, 69.7177), [69.7177, 204.074), [204.074, 593.693), [593.693, 1723.55), [1723.55, 5000] |
| `D1` | numeric | 9 | [0, 80), [80, 160), [160, 240), [240, 320), [320, 400), [400, 480), [480, 560), [560, 640], ... |
| `M4` | categorical | 5 | M0, M1, M2, OTHER, NA |
| `M6` | categorical | 4 | F, T, OTHER, NA |
| `DeviceType` | categorical | 4 | desktop, mobile, OTHER, NA |
| `hour` | numeric | 8 | [0, 3), [3, 6), [6, 9), [9, 12), [12, 15), [15, 18), [18, 21), [21, 24] |
| `isFraud` | categorical | 2 | 0, 1 |

## Tasks

| Task | Target | Features | Test rows | Positive rate (test) | Note |
|---|---|---:|---:|---:|---|
| fraud | `isFraud` | 16 | 10,000 | 3.3% | fraud classification on all fifteen predictors |

## Notes

- row_id is TransactionID; never published (competition rules 7.B)
