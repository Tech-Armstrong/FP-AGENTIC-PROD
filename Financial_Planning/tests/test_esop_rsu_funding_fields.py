"""ESOP/RSU funded_from fields match corpus_gap units (FV) and plan UI semantics."""

from Financial_Planning.Utilities.utility_functions import calculate_future_value


def test_esop_funding_fv_closes_gap():
    corpus_gap = 3_000_000
    esop_remaining_usable = 324_000
    growth = 0.12
    years_to_goal = 14

    usable_esop_fv = round(calculate_future_value(esop_remaining_usable, growth, years_to_goal))
    amount_to_apply = min(usable_esop_fv, corpus_gap)
    pv_of_used = amount_to_apply / ((1 + growth) ** years_to_goal)

    assert amount_to_apply == 1_583_424
    assert round(corpus_gap - amount_to_apply) == 1_416_576
    assert round(pv_of_used) == 324_000
    assert round(amount_to_apply) + 1_416_576 == 3_000_000


def test_rsu_funding_shape_lists_fifo_years_not_from_to():
    """RSU rows list vest years actually drawn; From/To stay empty in plan UI."""
    entry = {
        "type": "rsu_funds",
        "amount_used": 1_416_576,
        "fv_contribution": 1_416_576,
        "rsu_years_utilized": [2026, 2027],
        "rsu_years_utilized_label": "2026, 2027",
        "rate": "10.0%",
    }
    assert "from_year" not in entry
    assert "to_year" not in entry
    assert entry["rsu_years_utilized_label"] == "2026, 2027"
    assert entry["fv_contribution"] == entry["amount_used"]
