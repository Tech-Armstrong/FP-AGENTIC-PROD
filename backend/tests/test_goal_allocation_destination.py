"""Tests for education destination on goal_allocation_preview."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from financial_plan_runner import summarize_plan_state  # noqa: E402


def _base_state(*, goals: list[dict], education_summary: list[dict] | None = None) -> dict:
    client_data = {
        "client_data": {"name": "Test Client"},
        "education_target_years_by_child": {
            "Asha": {
                "ug_start_year": 2030,
                "ug_end_year": 2035,
                "ug_target_year": 2035,
            }
        },
    }
    if education_summary is not None:
        client_data["education_planning_summary"] = education_summary
    return {
        "client_data": client_data,
        "optimal_goal_allocation": {
            "goals": goals,
            "ending_monthly_surplus": 0,
            "ending_liquid_pool": 0,
        },
    }


def test_goal_allocation_preview_includes_education_destination():
    state = _base_state(
        goals=[
            {
                "goal_name": "Asha UG",
                "destination": "International",
                "corpus_needed": 5_000_000,
                "corpus_gap": 0,
                "target_corpus": 5_000_000,
                "target_year": 2035,
                "filter": [{"type": "funded"}],
                "funded_from": [],
            }
        ],
    )
    summary = summarize_plan_state(state)
    preview = summary["goal_allocation_preview"]
    assert len(preview) == 1
    assert preview[0]["destination"] == "International"


def test_goal_allocation_preview_normalizes_domestic_case():
    state = _base_state(
        goals=[
            {
                "goal_name": "Asha UG",
                "destination": "domestic",
                "corpus_needed": 5_000_000,
                "corpus_gap": 0,
                "target_corpus": 5_000_000,
                "target_year": 2035,
                "filter": [{"type": "funded"}],
            }
        ],
    )
    summary = summarize_plan_state(state)
    assert summary["goal_allocation_preview"][0]["destination"] == "Domestic"


def test_goal_allocation_preview_omits_destination_for_retirement():
    state = _base_state(
        goals=[
            {
                "goal_name": "Retirement",
                "corpus_needed": 10_000_000,
                "corpus_gap": 0,
                "target_corpus": 10_000_000,
                "target_year": 2045,
                "filter": [{"type": "funded"}],
            }
        ],
    )
    summary = summarize_plan_state(state)
    assert "destination" not in summary["goal_allocation_preview"][0]


def test_goal_allocation_preview_falls_back_to_education_summary():
    state = _base_state(
        goals=[
            {
                "goal_name": "Asha UG",
                "corpus_needed": 5_000_000,
                "corpus_gap": 0,
                "target_corpus": 5_000_000,
                "target_year": 2035,
                "filter": [{"type": "funded"}],
            }
        ],
        education_summary=[
            {
                "name": "Asha",
                "type": "UG",
                "destination": "International",
            }
        ],
    )
    summary = summarize_plan_state(state)
    assert summary["goal_allocation_preview"][0]["destination"] == "International"
