"""FIFO mapping of RSU pool draws to vest years."""

from Financial_Planning.Nodes.allocations_nodes import rsu_years_utilized_for_draw


def _tranches():
    return [
        {"year": 2026, "tranche_value_inr": 1_072_095.45},
        {"year": 2027, "tranche_value_inr": 4_688_456.42},
        {"year": 2028, "tranche_value_inr": 12_909_075.11},
        {"year": 2029, "tranche_value_inr": 14_199_982.62},
    ]


def test_draw_within_first_tranche_only():
    cap = 0.6
    slice_2026 = round(1_072_095.45 * cap, 2)
    years = rsu_years_utilized_for_draw(_tranches(), 2040, 0, slice_2026 - 1, cap)
    assert years == [2026]


def test_draw_spans_2026_and_2027():
    """Kabir UG–like draw ~1.42M from empty pool touches 2026 then 2027."""
    amount = 1_416_576
    years = rsu_years_utilized_for_draw(_tranches(), 2040, 0, amount, 0.6)
    assert years == [2026, 2027]


def test_draw_respects_fifo_cursor_after_prior_goal():
    cap = 0.6
    first_slice = round(1_072_095.45 * cap, 2)
    years = rsu_years_utilized_for_draw(_tranches(), 2040, first_slice, 100_000, cap)
    assert years == [2027]
