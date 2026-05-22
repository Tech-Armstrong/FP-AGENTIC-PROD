"""Detect when a user message should trigger policy document upload."""

from __future__ import annotations

import re

# Phrases that suggest insurance / ULIP document intent
_POLICY_PATTERNS = [
    r"\bulip\b",
    r"\bunit[- ]?linked\b",
    r"\binsurance\s+polic",
    r"\blife\s+insur",
    r"\bterm\s+plan\b",
    r"\bpolicy\s+document\b",
    r"\bmy\s+polic",
    r"\breview\s+my\s+(?:ulip|policy|insurance)",
    r"\bwhat\s+does\s+my\s+polic",
    r"\bpolicy\s+cover",
    r"\bsurrender\s+value\b",
    r"\bfund\s+allocation\b",
    r"\bpremium(?:s)?\s+(?:of|for|on)\s+my",
]

# Unrelated financial queries that should NOT trigger upload
_EXCLUDE_PATTERNS = [
    r"\bnifty\b",
    r"\bsensex\b",
    r"\bstock\s+market\b",
    r"\bmutual\s+fund\b(?!\s+linked)",
    r"\bmake\s+plan\b",
    r"\bportfolio\s+allocation\b",
]


def user_message_requests_policy_upload(text: str) -> bool:
    """Return True if the message is about the user's policy/ULIP document."""
    if not text or not str(text).strip():
        return False
    lower = str(text).lower()
    for pat in _EXCLUDE_PATTERNS:
        if re.search(pat, lower):
            return False
    for pat in _POLICY_PATTERNS:
        if re.search(pat, lower):
            return True
    return False
