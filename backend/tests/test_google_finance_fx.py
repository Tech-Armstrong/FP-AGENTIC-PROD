"""Tests for Google Finance USD/INR parsing (no live HTTP)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parent.parent
_REPO = _BACKEND.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from Financial_Planning.RSU.google_finance_fx import (  # noqa: E402
    GOOGLE_FINANCE_USD_INR_URL,
    fetch_usd_inr_from_google_finance,
    parse_usd_inr_from_google_finance_html,
)


SAMPLE_HTML = """
<html><body>
<h1>USD / INR</h1>
<div class="N6SYTe"><span jsname="Pdsbrc" class=""><span>95.3460</span></span></div>
<div>Compare EUR / INR 110.90</div>
</body></html>
"""


def test_parse_from_usd_inr_section():
    assert parse_usd_inr_from_google_finance_html(SAMPLE_HTML) == 95.346


def test_rejects_wrong_url():
    with pytest.raises(ValueError, match="only from"):
        fetch_usd_inr_from_google_finance(url="https://example.com/fx")


def test_canonical_url_constant():
    assert GOOGLE_FINANCE_USD_INR_URL == "https://www.google.com/finance/beta/quote/USD-INR"
