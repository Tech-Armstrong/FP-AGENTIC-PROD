"""
ExtractedPolicy — full nested OCR extraction schema for insurance / ULIP policies.

The full nested object is what the pipeline produces and validates. For chat we
return a *compact* flattened view (compact_dump) so the LLM context stays small.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PolicyholderDetails(BaseModel):
    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    address: str | None = None
    client_id: str | None = None


class LifeAssuredDetails(BaseModel):
    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    age_at_entry: int | None = None
    client_id: str | None = None


class PolicyDetails(BaseModel):
    policy_number: str | None = None
    plan_name: str | None = None
    uin: str | None = None
    plan_option: str | None = None
    plan_type: str | None = None  # linked / non-linked / participating etc.
    commencement_date: str | None = None
    risk_commencement_date: str | None = None
    maturity_date: str | None = None
    policy_term_years: int | None = None
    premium_paying_term_years: int | None = None
    payment_frequency: str | None = None
    modal_premium_excl_tax: float | None = None
    modal_premium_incl_tax: float | None = None
    underwriting_extra_premium: float | None = None
    grace_period_days: int | None = None
    free_look_period_days: int | None = None
    final_premium_due_date: str | None = None
    premium_due_dates: str | None = None


class BenefitDetails(BaseModel):
    sum_assured_on_death: float | None = None
    maturity_benefit: float | None = None
    total_income_post_maturity: float | None = None
    survival_benefit_amount: float | None = None
    survival_benefit_frequency: str | None = None
    survival_benefit_start: str | None = None
    survival_benefit_end: str | None = None
    income_benefit_amount: float | None = None
    critical_illness_cover: float | None = None
    hospi_cash_per_day: float | None = None
    other_benefits: list[str] = Field(default_factory=list)


class NomineeDetails(BaseModel):
    name: str | None = None
    relationship: str | None = None
    dob: str | None = None
    age: int | None = None
    nomination_pct: float | None = None
    appointee_name: str | None = None


class RiderDetails(BaseModel):
    rider_name: str | None = None
    sum_assured: float | None = None
    premium: float | None = None
    maturity_date: str | None = None
    term_years: int | None = None
    ppt_years: int | None = None


class ExtractedPolicy(BaseModel):
    """Full structured extraction. compact_dump() is what chat receives."""

    insurer: str | None = None
    policyholder: PolicyholderDetails | None = None
    life_assured: LifeAssuredDetails | None = None
    policy: PolicyDetails | None = None
    benefits: BenefitDetails | None = None
    nominee: NomineeDetails | None = None
    riders: list[RiderDetails] = Field(default_factory=list)
    tgriy_table: list[dict[str, Any]] = Field(default_factory=list)  # ULIP yield table
    special_provisions: list[str] = Field(default_factory=list)
    notes: str | None = None

    def full_dump(self) -> dict[str, Any]:
        """Complete nested extraction (nulls dropped)."""
        return self.model_dump(exclude_none=True)

    def compact_dump(self) -> dict[str, Any]:
        """
        Flattened, chat-friendly summary. Keeps the high-signal fields a planner
        cares about and drops nulls so the LLM context stays small.
        """
        pol = self.policy or PolicyDetails()
        ben = self.benefits or BenefitDetails()
        ph = self.policyholder or PolicyholderDetails()
        la = self.life_assured or LifeAssuredDetails()
        nom = self.nominee or NomineeDetails()

        summary: dict[str, Any] = {
            "insurer": self.insurer,
            "product_name": pol.plan_name,
            "uin": pol.uin,
            "plan_type": pol.plan_type,
            "policy_number": pol.policy_number,
            "policyholder_name": ph.name,
            "life_assured_name": la.name,
            "age_at_entry": la.age_at_entry,
            "commencement_date": pol.commencement_date,
            "maturity_date": pol.maturity_date,
            "policy_term_years": pol.policy_term_years,
            "premium_payment_term_years": pol.premium_paying_term_years,
            "payment_frequency": pol.payment_frequency,
            "annual_premium_excl_tax": pol.modal_premium_excl_tax,
            "annual_premium_incl_tax": pol.modal_premium_incl_tax,
            "sum_assured_on_death": ben.sum_assured_on_death,
            "maturity_benefit": ben.maturity_benefit,
            "survival_benefit_amount": ben.survival_benefit_amount,
            "total_income_post_maturity": ben.total_income_post_maturity,
            "nominee_name": nom.name,
            "nominee_pct": nom.nomination_pct,
            "riders": [r.rider_name for r in self.riders if r.rider_name],
            "num_riders": len(self.riders),
            "notes": self.notes,
        }
        # Drop null / empty so context stays compact.
        return {
            k: v
            for k, v in summary.items()
            if v not in (None, "", [], 0) or k == "num_riders"
        }
