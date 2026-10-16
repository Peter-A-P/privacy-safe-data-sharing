# ACS PUMS, California 2018, one-year person file

Written by `facsimile build`; do not edit by hand.

- Population after the dataset's filter: 302,640 records
- Split seed 20261016: train 20,000, control 2,000, test 10,000, attack targets 2,000 drawn from train
- Split ids published: yes, in split.json
- Full contingency table: 1.51e+14 cells

## Attribute subset and domain

| Column | Kind | Codes | Labels |
|---|---|---:|---|
| `AGEP` | numeric | 8 | [17, 26), [26, 35), [35, 44), [44, 53), [53, 62), [62, 71), [71, 80), [80, 89] |
| `COW` | categorical | 10 | 1, 2, 3, 4, 5, 6, 7, 8, ... |
| `SCHL` | categorical | 18 | 1, 9, 11, 12, 13, 14, 15, 16, ... |
| `MAR` | categorical | 5 | 1, 2, 3, 4, 5 |
| `OCCP` | categorical | 52 | 10, 20, 120, 410, 440, 630, 705, 800, ... |
| `POBP` | categorical | 25 | 4, 6, 17, 25, 26, 34, 36, 39, ... |
| `RELP` | categorical | 16 | 0, 1, 2, 4, 5, 6, 7, 9, ... |
| `WKHP` | numeric | 8 | [1, 20), [20, 30), [30, 40), [40, 41), [41, 50), [50, 60), [60, 99], NA |
| `SEX` | categorical | 2 | 1, 2 |
| `RAC1P` | categorical | 9 | 1, 2, 3, 4, 5, 6, 7, 8, ... |
| `DIS` | categorical | 2 | 1, 2 |
| `CIT` | categorical | 5 | 1, 2, 3, 4, 5 |
| `MIL` | categorical | 5 | 1, 2, 3, 4, NA |
| `NATIVITY` | categorical | 2 | 1, 2 |
| `PINCP` | numeric | 10 | [-20000, 101), [101, 10000), [10000, 20000), [20000, 30000), [30000, 40000), [40000, 50001), [50001, 75000), [75000, 100000), ... |
| `ESR` | categorical | 7 | 1, 2, 3, 4, 5, 6, NA |

## Tasks

| Task | Target | Features | Test rows | Positive rate (test) | Note |
|---|---|---:|---:|---:|---|
| income | `PINCP` | 10 | 6,349 | 41.0% | ACSIncome: PINCP > 50,000 among adults with income above 100 and hours worked |
| employment | `ESR` | 10 | 10,000 | 55.8% | ACSEmployment: ESR == 1 (civilian employed, at work), ten of its sixteen features |

## Notes

- row_id is the record's 0-based position in psam_p06.csv inside the checksummed archive
