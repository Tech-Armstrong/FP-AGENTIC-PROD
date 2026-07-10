"""Education destination field whitelist and coercion for Airtable PATCH."""

from __future__ import annotations

EDUCATION_DESTINATION_FIELDS = frozenset(
    {
        f"child_{slot}_{suffix}"
        for slot in (1, 2, 3)
        for suffix in ("graduation_destination", "post_graduation_destination")
    }
)

ALLOWED_DESTINATIONS = frozenset({"Domestic", "International"})


class EducationPatchValidationError(ValueError):
    """Raised when education PATCH fields are invalid."""


def coerce_education_destination(value) -> str:
    if value is None or value == "":
        raise EducationPatchValidationError("Destination is required")

    normalized = str(value).strip().lower()
    if normalized == "domestic":
        return "Domestic"
    if normalized == "international":
        return "International"
    raise EducationPatchValidationError(
        f"Invalid education destination: {value!r}. Use Domestic or International."
    )


def coerce_education_value(key: str, value) -> str:
    if key not in EDUCATION_DESTINATION_FIELDS:
        raise EducationPatchValidationError(f"Unknown education field: {key}")
    return coerce_education_destination(value)


def validate_education_patch_fields(fields: dict) -> dict[str, str]:
    if not fields:
        raise EducationPatchValidationError("At least one education field is required")

    unknown = set(fields) - EDUCATION_DESTINATION_FIELDS
    if unknown:
        raise EducationPatchValidationError(
            f"Unknown education fields: {', '.join(sorted(unknown))}"
        )

    return {key: coerce_education_value(key, value) for key, value in fields.items()}
