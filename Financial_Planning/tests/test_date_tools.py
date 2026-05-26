"""Verify get_current_date tool and priority score use today's calendar year."""

from datetime import date

from Financial_Planning.Toools.custom_tools import (
    calculate_priority_score,
    get_current_date,
)


def test_get_current_date_returns_today():
    import json

    payload = json.loads(get_current_date.invoke({}))
    today = date.today()
    assert payload["date"] == today.isoformat()
    assert payload["year"] == today.year


def test_calculate_priority_score_uses_today_year():
    target = date.today().year + 5
    score = calculate_priority_score.invoke({"weight": 0.8, "target_year": target})
    assert score > 0
