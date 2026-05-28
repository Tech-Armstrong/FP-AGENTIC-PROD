"""ExtractedPolicy — compact single-page OCR summary returned to chat."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExtractedPolicy(BaseModel):
    insurer: str | None = None
    product_name: str | None = None
    policy_number: str | None = None
    sum_assured: str | None = None
    annual_premium: str | None = None
    policy_term_years: int | None = None
    premium_payment_term_years: int | None = None
    fund_allocation: list[dict[str, Any]] = Field(default_factory=list)
    charges: list[dict[str, Any]] = Field(default_factory=list)
    surrender_value: str | None = None
    riders: list[str] = Field(default_factory=list)
    notes: str | None = None

    def compact_dump(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, exclude_defaults=True)
