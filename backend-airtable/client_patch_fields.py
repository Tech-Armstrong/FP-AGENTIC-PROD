"""Combined whitelist validation for client PATCH fields."""

from __future__ import annotations

from education_fields import (
    EDUCATION_DESTINATION_FIELDS,
    EducationPatchValidationError,
    validate_education_patch_fields,
)
from spouse_fields import (
    SPOUSE_AIRTABLE_FIELDS,
    SpousePatchValidationError,
    validate_spouse_patch_fields,
)

CLIENT_PATCH_FIELDS = SPOUSE_AIRTABLE_FIELDS | EDUCATION_DESTINATION_FIELDS


class ClientPatchValidationError(ValueError):
    """Raised when client PATCH fields are invalid."""


def validate_client_patch_fields(fields: dict) -> dict[str, str | float | None]:
    if not fields:
        raise ClientPatchValidationError("At least one field is required")

    unknown = set(fields) - CLIENT_PATCH_FIELDS
    if unknown:
        raise ClientPatchValidationError(
            f"Unknown client fields: {', '.join(sorted(unknown))}"
        )

    spouse_subset = {k: v for k, v in fields.items() if k in SPOUSE_AIRTABLE_FIELDS}
    education_subset = {
        k: v for k, v in fields.items() if k in EDUCATION_DESTINATION_FIELDS
    }

    validated: dict[str, str | float | None] = {}
    try:
        if spouse_subset:
            validated.update(validate_spouse_patch_fields(spouse_subset))
        if education_subset:
            validated.update(validate_education_patch_fields(education_subset))
    except (SpousePatchValidationError, EducationPatchValidationError) as exc:
        raise ClientPatchValidationError(str(exc)) from exc

    return validated
