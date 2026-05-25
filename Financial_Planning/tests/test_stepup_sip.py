"""Tests for step-up SIP horizon and recommendation helpers."""

from Financial_Planning.Utilities.utility_functions import (
    recommend_stepup_sip_for_gap,
    stepup_sip_horizon_months,
    stepup_sip_required,
)


def test_horizon_next_year_one_year_goal_not_zero():
    """Regression: old code used (years*12)-12 which was 0 for a 2027 goal in 2026."""
    months = stepup_sip_horizon_months(2027, 2026, sip_starts_next_year=True)
    assert months == 12


def test_stepup_sip_positive_for_vacation_gap():
    gap = 203952
    sip, msg = recommend_stepup_sip_for_gap(
        gap,
        target_year=2027,
        current_year=2026,
        funded_from=[{"type": "lumpsum_from_liquid_partial"}],
    )
    assert sip > 1000
    assert msg == "from next year onwards"


def test_stepup_sip_required_zero_months_with_positive_gap():
    assert stepup_sip_required(203952, 0.08, 0, 0.07) == 0


def test_stepup_sip_required_twelve_months():
    sip = stepup_sip_required(203952, 0.08, 12, 0.07)
    assert 1000 <= sip <= 20000
