"""Unit tests for term insurance existing cover sourcing."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from Financial_Planning.Nodes.basic_calculations_nodes import (
    calculate_term_insurance_requirement,
)
from Financial_Planning.Utilities.utility_functions import sum_life_insurance_cover
from financial_plan_runner import summarize_plan_state


def _term_state(
    *,
    monthly_expenses: float = 30_000,
    kids_education_cost: float = 1_000_000,
    liabilities: float = 500_000,
    liquid_pool: float = 200_000,
    life_insurance=None,
    medical_insurance=None,
):
    client_data = {
        "education_planning_summary": [
            {"future_cost": kids_education_cost},
        ],
    }
    if life_insurance is not None:
        client_data["life_insurance"] = life_insurance
    if medical_insurance is not None:
        client_data["medical_insurance"] = medical_insurance

    return {
        "required_retirement_corpus": {
            "client_info": {"current_monthly_expenses": monthly_expenses},
        },
        "client_data": client_data,
        "liabilities": [{"outstanding_balance": liabilities}],
        "liquid_pool": liquid_pool,
    }


def _expected_total(*, existing_cover: float) -> int:
    pv_of_expenses = int(30_000 * 12 / 0.06)
    raw = (
        pv_of_expenses
        + 1_000_000
        + 500_000
        - existing_cover
        - 200_000
    )
    return max(raw, 0)


def test_sum_life_insurance_cover_sums_coverage_values():
    client_data = {
        "life_insurance": [
            {"company_name": "HDFC", "coverage_value": 3_000_000},
            {"company_name": "ICICI", "coverage_value": 2_000_000},
        ],
    }
    assert sum_life_insurance_cover(client_data) == 5_000_000


def test_life_cover_is_deducted_from_term_requirement():
    state = _term_state(
        life_insurance=[{"company_name": "HDFC", "coverage_value": 5_000_000}],
    )
    result = calculate_term_insurance_requirement(state)
    summary = result["term_insurance_summary"]

    assert summary["existing_cover"] == 5_000_000
    assert summary["total_term_required"] == _expected_total(existing_cover=5_000_000)


def test_medical_cover_is_ignored():
    state = _term_state(
        medical_insurance=[
            {
                "policy_type": "Self",
                "company_name": "Star Health",
                "coverage_value": 500_000,
            },
        ],
    )
    result = calculate_term_insurance_requirement(state)
    summary = result["term_insurance_summary"]

    assert summary["existing_cover"] == 0
    assert summary["total_term_required"] == _expected_total(existing_cover=0)


def test_no_insurance_yields_zero_existing_cover():
    state = _term_state()
    result = calculate_term_insurance_requirement(state)
    summary = result["term_insurance_summary"]

    assert summary["existing_cover"] == 0
    assert summary["total_term_required"] == _expected_total(existing_cover=0)


def test_summarize_plan_state_maps_less_existing_cover():
    workflow_state = {
        "client_data": {"client_data": {"name": "Test Client"}},
        "term_insurance_summary": {
            "pv_of_expenses": 6_000_000,
            "kids_education_cost": 1_000_000,
            "current_liabilities": 500_000,
            "existing_cover": 5_000_000,
            "liquidable_assets": 200_000,
            "total_term_required": 2_300_000,
        },
    }
    summary = summarize_plan_state(workflow_state)
    breakdown = summary["term_insurance_requirement"]["breakdown"]

    assert breakdown["less_existing_cover"] == -5_000_000
    assert summary["term_insurance_requirement"]["total_cover_required"] == 2_300_000
