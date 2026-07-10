"""Spouse field whitelist and coercion for Airtable PATCH."""

from __future__ import annotations

SPOUSE_AIRTABLE_FIELDS = frozenset(
    {
        "spouse_name",
        "spouse_dob",
        "spouse_investment_mutual_fund_value",
        "spouse_investment_direct_equity_value",
        "spouse_investment_vestd_esop",
        "spouse_investment_unvested_esop",
        "spouse_investment_pf_current_value",
        "spouse_investment_pf_contribution",
        "spouse_investment_fd_bond_invested_amount",
        "spouse_investment_fd_bond_rate_intrest",
        "spouse_investment_fd_bond_maturity_date",
    }
)

TEXT_FIELDS = frozenset({"spouse_name", "spouse_dob", "spouse_investment_fd_bond_maturity_date"})
RATE_FIELDS = frozenset({"spouse_investment_fd_bond_rate_intrest"})
NUMERIC_FIELDS = SPOUSE_AIRTABLE_FIELDS - TEXT_FIELDS - RATE_FIELDS


class SpousePatchValidationError(ValueError):
    """Raised when spouse PATCH fields are invalid."""


def coerce_spouse_value(key: str, value) -> str | float | None:
    if key not in SPOUSE_AIRTABLE_FIELDS:
        raise SpousePatchValidationError(f"Unknown spouse field: {key}")

    if value is None:
        return None if key in NUMERIC_FIELDS or key in RATE_FIELDS else ""

    if key in TEXT_FIELDS:
        return str(value).strip()

    if key in RATE_FIELDS:
        if value == "":
            return None
        rate = float(value)
        return rate

    if key in NUMERIC_FIELDS:
        if value == "":
            return None
        return float(value)

    raise SpousePatchValidationError(f"Unhandled spouse field: {key}")


def validate_spouse_patch_fields(fields: dict) -> dict[str, str | float | None]:
    if not fields:
        raise SpousePatchValidationError("At least one spouse field is required")

    unknown = set(fields) - SPOUSE_AIRTABLE_FIELDS
    if unknown:
        raise SpousePatchValidationError(
            f"Unknown spouse fields: {', '.join(sorted(unknown))}"
        )

    return {key: coerce_spouse_value(key, value) for key, value in fields.items()}
