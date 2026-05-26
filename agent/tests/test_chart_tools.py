"""Chart tools are frontend-only (useComponent); agent must not bind stale Python names."""

from __future__ import annotations

import main


def test_static_backend_tools_exclude_charts():
    """barChart/pieChart come from CopilotKitMiddleware + frontend useComponent, not static @tool."""
    static = {
        main.get_current_date.name,
        main.search_internet.name,
        main.request_policy_document.name,
    }
    assert static == {"getCurrentDate", "searchInternet", "request_policy_document"}
    assert "showBarChart" not in static
    assert "showPieChart" not in static
    assert "barChart" not in static
    assert "pieChart" not in static


def test_system_prompt_mentions_frontend_chart_tools():
    assert "pieChart" in main.SYSTEM_PROMPT
    assert "barChart" in main.SYSTEM_PROMPT
    assert "showPieChart" not in main.SYSTEM_PROMPT
    assert "showBarChart" not in main.SYSTEM_PROMPT
