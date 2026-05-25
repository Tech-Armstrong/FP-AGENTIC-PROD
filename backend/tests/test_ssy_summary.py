"""Tests for SSY Tracker summary built for the dashboard plan review."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from financial_plan_runner import build_ssy_summary_preview


def test_build_ssy_summary_from_tracker_and_funded_from():
    oga = {
        "ssy_tracker": {
            "Ananya": {
                "remaining_balance": 350000,
                "total_withdrawn": 150000,
                "maturity_year": 2037,
                "total_fv": 500000,
                "locked": True,
            }
        },
        "goals": [
            {
                "goal_name": "Ananya UG",
                "funded_from": [
                    {
                        "type": "ssy_funds",
                        "source": "SSY account of Ananya",
                        "total_ssy_fv": 500000,
                        "amount_used": 150000,
                    }
                ],
            }
        ],
    }
    rows = build_ssy_summary_preview(oga)
    assert len(rows) == 1
    assert rows[0]["child_name"] == "Ananya"
    assert rows[0]["total_fv"] == 500000
    assert rows[0]["total_withdrawn"] == 150000
    assert rows[0]["remaining_balance"] == 350000
    assert rows[0]["maturity_year"] == 2037
    assert rows[0]["locked"] is True


def test_build_ssy_summary_empty_when_no_tracker():
    assert build_ssy_summary_preview({}) == []
    assert build_ssy_summary_preview({"goals": []}) == []
