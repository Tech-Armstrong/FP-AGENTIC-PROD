"""Unit tests for calculate_retirement_annuity (income-preservation model)."""

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


def test_rental_covers_annuity_esop_rsu_absent_fd_mf_not_required():
    result = calculate_retirement_annuity(_base_state())
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is True
    assert annuity["shortfall_monthly"] == 0
    keys = [s["key"] for s in annuity["sources"]]
    assert "rental_other_income" in keys
    assert "esop" not in keys
    assert "rsu" not in keys
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["rental_other_income"]["required"] is True
    assert by_key["fixed_deposits"]["required"] is False
    assert by_key["mutual_funds"]["required"] is False


def test_esop_rsu_remaining_first_and_required_before_rental():
    vested = 1_000_000.0
    esop_remaining = vested * 0.60
    rsu_remaining = 500_000.0
    years = 10
    esop_rate = 0.12
    rsu_rate = 0.10
    esop_fv = calculate_future_value(esop_remaining, esop_rate, years)
    rsu_fv = calculate_future_value(rsu_remaining, rsu_rate, years)
    esop_monthly = (esop_fv * esop_rate) / 12
    rsu_monthly = (rsu_fv * rsu_rate) / 12
    desired = esop_monthly + rsu_monthly - 1_000

    state = _base_state(
        desired_monthly_annuity=desired,
        surplus_monthly=100_000,
        fd_fv=0,
        mf_cv=0,
        years_to_retirement=years,
        esops=[{"vested_esops_value": vested, "unvested_esops_value": 0}],
        rsu_portfolio=[{"rsu_remaining": rsu_remaining, "total_rsu_value_inr": 1_000_000}],
    )
    state["client_data"]["investment_details"]["mutual_funds"] = []

    result = calculate_retirement_annuity(state)
    annuity = result["retirement_annuity"]
    keys = [s["key"] for s in annuity["sources"]]
    assert keys.index("esop") < keys.index("rsu")
    assert keys.index("rsu") < keys.index("rental_other_income")
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["esop"]["required"] is True
    assert by_key["rsu"]["required"] is True
    assert by_key["rental_other_income"]["required"] is False
    assert by_key["esop"]["remaining_base"] == esop_remaining
    assert by_key["rsu"]["remaining_base"] == rsu_remaining
    assert state["optimal_goal_allocation"]["rsu_portfolio"][0]["rsu_remaining"] == rsu_remaining


def test_shortfall_flags_sources_in_priority_order():
    state = _base_state(desired_monthly_annuity=300_000, surplus_monthly=0)
    state["client_data"]["investment_details"]["esops"] = [
        {"vested_esops_value": 100_000, "unvested_esops_value": 0},
    ]
    result = calculate_retirement_annuity(state)
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is False
    assert annuity["shortfall_monthly"] > 0
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["esop"]["required"] is True
    assert by_key["fixed_deposits"]["required"] is True
    assert by_key["mutual_funds"]["required"] is True
    assert annuity["max_monthly_annuity"] == annuity["total_available_monthly"]


def test_zero_desired_annuity_returns_empty():
    state = _base_state(desired_monthly_annuity=0)
    assert calculate_retirement_annuity(state) == {}
