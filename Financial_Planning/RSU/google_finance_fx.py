"""
USD/INR rate from Google Finance only.

Source: https://www.google.com/finance/beta/quote/USD-INR
"""

from __future__ import annotations

import re
from typing import Optional

import requests

GOOGLE_FINANCE_USD_INR_URL = "https://www.google.com/finance/beta/quote/USD-INR"

USD_INR_MIN = 60.0
USD_INR_MAX = 150.0

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _rate_in_range(value: float) -> bool:
    return USD_INR_MIN <= value <= USD_INR_MAX


def parse_usd_inr_from_google_finance_html(html: str) -> Optional[float]:
    """
    Parse the live USD/INR quote from a Google Finance USD-INR page body.
    """
    if not html or not html.strip():
        return None

    # Primary: main quote price in the USD / INR section (jsname Pdsbrc)
    for anchor in ("USD / INR", "USD / INR • Currency"):
        idx = html.find(anchor)
        if idx >= 0:
            chunk = html[idx : idx + 12_000]
            match = re.search(
                r'jsname="Pdsbrc"[^>]*>.*?<span>([\d]{2,3}(?:\.\d{1,6})?)</span>',
                chunk,
                re.DOTALL,
            )
            if match:
                rate = float(match.group(1))
                if _rate_in_range(rate):
                    return rate

    # Fallback: slug near first in-range rate in page metadata
    slug_match = re.search(
        r"USD-INR.{0,800}?([\d]{2,3}(?:\.\d{2,6})?)",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if slug_match:
        rate = float(slug_match.group(1))
        if _rate_in_range(rate):
            return rate

    return None


def fetch_usd_inr_from_google_finance(
    *,
    url: str = GOOGLE_FINANCE_USD_INR_URL,
    timeout: float = 30.0,
) -> float:
    """
    Fetch the current USD/INR rate from Google Finance (single allowed source).

    Raises:
        RuntimeError: HTTP failure or rate could not be parsed.
    """
    if url.rstrip("/") != GOOGLE_FINANCE_USD_INR_URL.rstrip("/"):
        raise ValueError(
            f"USD/INR must be fetched only from {GOOGLE_FINANCE_USD_INR_URL!r}, got {url!r}"
        )

    response = requests.get(url, headers=_DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()

    rate = parse_usd_inr_from_google_finance_html(response.text)
    if rate is None:
        raise RuntimeError(
            f"Could not parse USD/INR from Google Finance page ({url}). "
            "The page layout may have changed."
        )

    return rate
