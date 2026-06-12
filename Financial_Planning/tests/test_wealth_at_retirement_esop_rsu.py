"""Tests for leftover ESOP/RSU in wealth_at_retirement breakdown."""

from Financial_Planning.Nodes.retirement_nodes import wealth_at_retirement
from Financial_Planning.Utilities.utility_functions import calculate_future_value


def _wealth_state(
    *,
    vested_esop: float = 1_000_000,
    esop_consumed: float = 200_000,
    rsu_remaining: float = 500_000,
    years_to_retirement: int = 10,
):
    esop_usable = vested_esop * 0.60
    esop_remaining = max(0.0, esop_usable - esop_consumed)
    esop_rate = 0.12
    rsu_rate = 0.10
    expected_esop_fv = calculate_future_value(esop_remaining, esop_rate, years_to_retirement)
    expected_rsu_fv = calculate_future_value(rsu_remaining, rsu_rate, years_to_retirement)

    return {
        "state": {
            "client_data": {
                "investment_details": {
                    "esops": [{"vested_esops_value": vested_esop, "unvested_esops_value": 0}],
                    "rsu_growth_rate": rsu_rate,
                    "retirement_investments": {},
                },
            },
            "required_retirement_corpus": {
                "client_info": {"years_to_retirement": years_to_retirement},
            },
            "retirement_schemes_fv": {"category_totals": {}},
            "liquid_assets": [],
            "fixed_assets": [],
            "optimal_goal_allocation": {
                "goals": [
                    {
                        "goal_name": "education",
                        "funded_from": [
                            {
                                "type": "esop_funds",
                                "pv_allocated_today": esop_consumed,
                            },
                        ],
                    },
                ],
                "rsu_portfolio": [{"rsu_remaining": rsu_remaining}],
            },
        },
        "expected_esop_fv": expected_esop_fv,
        "expected_rsu_fv": expected_rsu_fv,
    }


def test_wealth_includes_leftover_esop_and_rsu_fv():
    fixture = _wealth_state()
    result = wealth_at_retirement(fixture["state"])
    wealth = result["wealth_at_retirement"]
    breakdown = wealth["breakdown"]

    assert round(breakdown["esop"]["future_value"], 2) == round(fixture["expected_esop_fv"], 2)
    assert round(breakdown["rsu"]["future_value"], 2) == round(fixture["expected_rsu_fv"], 2)
    assert wealth["total_corpus"] >= breakdown["esop"]["future_value"] + breakdown["rsu"]["future_value"]


def test_wealth_zero_leftover_esop_rsu():
    fixture = _wealth_state(vested_esop=0, esop_consumed=0, rsu_remaining=0)
    result = wealth_at_retirement(fixture["state"])
    breakdown = result["wealth_at_retirement"]["breakdown"]
    assert breakdown["esop"]["future_value"] == 0
    assert breakdown["rsu"]["future_value"] == 0
