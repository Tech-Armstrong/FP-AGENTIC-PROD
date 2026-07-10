"""Tests for SSY funded_from preview rows in goal allocation summary."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from financial_plan_runner import summarize_plan_state  # noqa: E402


def test_goal_allocation_preview_includes_ssy_funded_from():
    state = {
        "client_data": {"client_data": {"name": "Test Client"}},
        "optimal_goal_allocation": {
            "goals": [
                {
                    "goal_name": "Ananya UG",
                    "corpus_needed": 5_000_000,
                    "corpus_gap": 0,
                    "target_corpus": 5_000_000,
                    "target_year": 2035,
                    "filter": [{"type": "funded"}],
                    "funded_from": [
                        {
                            "type": "ssy_funds",
                            "source": "SSY account of Ananya",
                            "amount_used": 500_000,
                            "total_ssy_fv": 500_000,
                        }
                    ],
                }
            ],
            "ending_monthly_surplus": 0,
            "ending_liquid_pool": 0,
        },
    }

    summary = summarize_plan_state(state)
    preview = summary["goal_allocation_preview"]
    assert len(preview) == 1

    funded = preview[0]["funded_from_preview"]
    assert len(funded) == 1
    assert funded[0]["type"] == "SSY"
    assert funded[0]["amount"] == 500_000
    assert funded[0]["source"] == "SSY account of Ananya"
    assert "fv" not in funded[0]
