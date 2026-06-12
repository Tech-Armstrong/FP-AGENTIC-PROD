"""Unit tests for calculate_retirement_annuity (income-preservation, used-sources only)."""

from Financial_Planning.Nodes.retirement_nodes import calculate_retirement_annuity
from Financial_Planning.Utilities.utility_functions import calculate_future_value


def _base_state(
    *,
    desired_monthly_annuity: float = 50_000,
    surplus_monthly: float = 50_000,
    fd_fv: float = 5_000_000,
    fd_rate: str = "6.5%",
    mf_cv: float = 2_000_000,
    mf_rate: float = 0.12,
    years_to_retirement: int = 10,
    esops=None,
    rsu_portfolio=None,
    goals=None,
):
    return {
        "client_data": {
            "client_data": {
                "retirement_age": 60,
                "desired_monthly_annuity": desired_monthly_annuity,
            },
            "investment_details": {
                "financial_summary": [
                    {"other_income(rental/interest/other)": surplus_monthly},
                ],
                "mutual_funds": [
                    {"current_value": mf_cv, "expected_annual_return": mf_rate},
                ],
                "esops": esops if esops is not None else [],
                "rsu": [],
            },
        },
        "required_retirement_corpus": {
            "client_info": {"years_to_retirement": years_to_retirement},
        },
        "wealth_at_retirement": {
            "retirement_year": 2036,
            "breakdown": {
                "fixed_deposits": {"future_value": fd_fv, "rate": fd_rate},
            },
        },
        "optimal_goal_allocation": {
            "goals": goals or [],
            "rsu_portfolio": rsu_portfolio or [],
        },
    }


def test_rental_only_covers_desired_single_source_capped_to_target():
    desired = 50_000.0
    result = calculate_retirement_annuity(_base_state(desired_monthly_annuity=desired))
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is True
    assert len(annuity["sources"]) == 1
    assert annuity["sources"][0]["key"] == "rental_other_income"
    assert annuity["sources"][0]["monthly_income"] == desired
    assert annuity["total_available_monthly"] == desired
    assert all(s["required"] is True for s in annuity["sources"])
    keys = {s["key"] for s in annuity["sources"]}
    assert "fixed_deposits" not in keys
    assert "mutual_funds" not in keys


def test_multi_source_last_row_capped_and_rows_sum_to_desired():
    vested = 1_000_000.0
    esop_remaining = vested * 0.60
    years = 10
    esop_rate = 0.12
    esop_fv = calculate_future_value(esop_remaining, esop_rate, years)
    esop_monthly = (esop_fv * esop_rate) / 12
    desired = esop_monthly + 20_000.0

    state = _base_state(
        desired_monthly_annuity=desired,
        surplus_monthly=100_000,
        fd_fv=0,
        mf_cv=0,
        years_to_retirement=years,
        esops=[{"vested_esops_value": vested, "unvested_esops_value": 0}],
    )
    state["client_data"]["investment_details"]["mutual_funds"] = []

    result = calculate_retirement_annuity(state)
    annuity = result["retirement_annuity"]
    keys = [s["key"] for s in annuity["sources"]]
    assert keys == ["esop", "rental_other_income"]
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["esop"]["monthly_income"] == round(esop_monthly, 2)
    assert by_key["rental_other_income"]["monthly_income"] == 20_000.0
    used_sum = sum(s["monthly_income"] for s in annuity["sources"])
    assert round(used_sum, 2) == round(desired, 2)
    assert annuity["total_available_monthly"] == round(desired, 2)


def test_shortfall_shows_all_positive_sources_at_full_income():
    desired = 300_000.0
    state = _base_state(desired_monthly_annuity=desired, surplus_monthly=0)
    state["client_data"]["investment_details"]["esops"] = [
        {"vested_esops_value": 100_000, "unvested_esops_value": 0},
    ]
    result = calculate_retirement_annuity(state)
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is False
    assert annuity["shortfall_monthly"] > 0
    assert annuity["total_available_monthly"] < desired
    assert annuity["total_available_monthly"] == annuity["max_monthly_annuity"]
    keys = {s["key"] for s in annuity["sources"]}
    assert "esop" in keys
    assert "fixed_deposits" in keys
    assert "mutual_funds" in keys
    assert all(s["required"] is True for s in annuity["sources"])


def test_zero_desired_annuity_returns_empty():
    state = _base_state(desired_monthly_annuity=0)
    assert calculate_retirement_annuity(state) == {}
