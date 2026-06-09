"""Unit tests for calculate_retirement_annuity (income-preservation model)."""

from Financial_Planning.Nodes.retirement_nodes import calculate_retirement_annuity


def _base_state(
    *,
    desired_monthly_annuity: float = 50_000,
    surplus_monthly: float = 50_000,
    fd_fv: float = 5_000_000,
    fd_rate: str = "6.5%",
    mf_cv: float = 2_000_000,
    mf_rate: float = 0.12,
    years_to_retirement: int = 10,
):
    mf_fv = mf_cv * ((1 + mf_rate) ** years_to_retirement)
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
                "esops": [],
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
        "optimal_goal_allocation": {"rsu_portfolio": []},
    }


def test_income_covers_annuity_no_assets_required():
    result = calculate_retirement_annuity(_base_state())
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is True
    assert annuity["shortfall_monthly"] == 0
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["rental_other_income"]["required"] is True
    assert by_key["fixed_deposits"]["required"] is False
    assert by_key["mutual_funds"]["required"] is False
    assert by_key["rsu_esop"]["required"] is False


def test_shortfall_taps_fd_then_mf_in_order():
    state = _base_state(desired_monthly_annuity=300_000, surplus_monthly=0)
    result = calculate_retirement_annuity(state)
    annuity = result["retirement_annuity"]
    assert annuity["achievable"] is False
    assert annuity["shortfall_monthly"] > 0
    by_key = {s["key"]: s for s in annuity["sources"]}
    assert by_key["fixed_deposits"]["required"] is True
    assert by_key["mutual_funds"]["required"] is True
    assert annuity["max_monthly_annuity"] == annuity["total_available_monthly"]


def test_zero_desired_annuity_returns_empty():
    state = _base_state(desired_monthly_annuity=0)
    assert calculate_retirement_annuity(state) == {}
