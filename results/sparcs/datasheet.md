# New York SPARCS de-identified inpatient discharges, 2024

Written by `facsimile build`; do not edit by hand.

- Population after the dataset's filter: 2,196,737 records
- Split seed 20261016: train 20,000, control 2,000, test 10,000, attack targets 2,000 drawn from train
- Split ids published: yes, in split.json
- Full contingency table: 4.04e+13 cells

## Attribute subset and domain

| Column | Kind | Codes | Labels |
|---|---|---:|---|
| `age_group` | categorical | 6 | 0-17, 18-29, 30-49, 50-69, 70 or Older, OTHER |
| `gender` | categorical | 3 | F, M, OTHER |
| `race` | categorical | 5 | Black/African American, Multi-racial, Other Race, White, OTHER |
| `ethnicity` | categorical | 4 | Not Span/Hispanic, Spanish/Hispanic, Unknown, OTHER |
| `zip_code` | categorical | 44 | 100, 103, 104, 105, 106, 107, 109, 110, ... |
| `health_service_area` | categorical | 10 | Capital/Adirondacks, Central NY, Finger Lakes, Hudson Valley, Long Island, New York City, Southern Tier, Western NY, ... |
| `type_of_admission` | categorical | 5 | Elective, Emergency, Newborn, Urgent, OTHER |
| `patient_disposition` | categorical | 9 | Expired, Home or Self Care, Home w/ Home Health Services, Hospice - Medical Facility, Inpatient Rehabilitation Facility, Left Against Medical Advice, Short-term Hospital, Skilled Nursing Home, ... |
| `apr_mdc_code` | categorical | 21 | 01, 03, 04, 05, 06, 07, 08, 09, ... |
| `apr_severity_of_illness_code` | categorical | 5 | 1, 2, 3, 4, OTHER |
| `apr_risk_of_mortality` | categorical | 6 | Extreme, Major, Minor, Moderate, OTHER, NA |
| `apr_medical_surgical` | categorical | 3 | Medical, Surgical, OTHER |
| `payment_typology_1` | categorical | 10 | Blue Cross/Blue Shield, Federal/State/Local/VA, Managed Care, Unspecified, Medicaid, Medicare, Miscellaneous/Other, Private Health Insurance, Self-Pay, ... |
| `emergency_department_indicator` | categorical | 3 | N, Y, OTHER |
| `length_of_stay` | numeric | 10 | [1, 2), [2, 3), [3, 4), [4, 5), [5, 6), [6, 8), [8, 11), [11, 15), ... |
| `total_charges` | numeric | 10 | [0, 5000), [5000, 10000), [10000, 20000), [20000, 30000), [30000, 50000), [50000, 75000), [75000, 100000), [100000, 200000), ... |

## Tasks

| Task | Target | Features | Test rows | Positive rate (test) | Note |
|---|---|---:|---:|---:|---|
| long_stay | `length_of_stay` | 14 | 10,000 | 29.1% | length of stay above five days, from the fourteen non-outcome attributes |
| high_charge | `total_charges` | 14 | 10,000 | 48.9% | total charges of US$50,000 or more, from the fourteen non-outcome attributes |

## Notes

- row_id is the record's 0-based position in the fetched file ($order=:id)
