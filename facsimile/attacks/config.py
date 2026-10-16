"""Per dataset: the secret the inference attacker wants and the two halves the linkability attacker holds.

Chosen once, before any table was attacked (2026-10-16), and the same for every synthesiser:

- **Secret**: the attribute whose disclosure would matter to the person. ACS: the income band.
  IEEE-CIS: the transaction amount band. SPARCS: the major diagnostic category, which is health
  information. The attacker knows every other attribute, as in the paper's strongest setting.
- **Halves**: who-you-are attributes against what-happened attributes, the split a real linkage
  across two releases would have.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttackConfig:
    secret: str
    half_a: tuple[str, ...]
    half_b: tuple[str, ...]
    n_attacks: int = 2000
    n_cols: int = 3
    k_values: tuple[int, ...] = (1, 10)


CONFIGS: dict[str, AttackConfig] = {
    "acs": AttackConfig(
        secret="PINCP",
        half_a=("AGEP", "SEX", "RAC1P", "MAR", "POBP", "CIT", "NATIVITY", "RELP"),
        half_b=("SCHL", "OCCP", "COW", "WKHP", "PINCP", "DIS", "MIL", "ESR"),
    ),
    "ieeecis": AttackConfig(
        secret="TransactionAmt",
        half_a=(
            "ProductCD",
            "card4",
            "card6",
            "addr1",
            "addr2",
            "P_emaildomain",
            "R_emaildomain",
            "DeviceType",
        ),
        half_b=("TransactionAmt", "dist1", "C1", "C2", "D1", "M4", "M6", "hour", "isFraud"),
    ),
    "sparcs": AttackConfig(
        secret="apr_mdc_code",
        half_a=(
            "age_group",
            "gender",
            "race",
            "ethnicity",
            "zip_code",
            "health_service_area",
            "payment_typology_1",
        ),
        half_b=(
            "type_of_admission",
            "patient_disposition",
            "apr_mdc_code",
            "apr_severity_of_illness_code",
            "apr_risk_of_mortality",
            "apr_medical_surgical",
            "emergency_department_indicator",
            "length_of_stay",
            "total_charges",
        ),
    ),
}
