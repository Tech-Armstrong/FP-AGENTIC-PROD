"""Client for the local OCR policy microservice (POST /extract)."""

from __future__ import annotations

import os
from typing import Any

import requests


class OCRServiceError(Exception):
    """OCR microservice call failed."""


def _base_url() -> str:
    url = (os.environ.get("OCR_SERVICE_URL") or "").strip()
    if not url:
        raise OCRServiceError("OCR_SERVICE_URL is not set")
    return url.rstrip("/")


def _timeout() -> int:
    raw = os.environ.get("OCR_SERVICE_TIMEOUT", "120")
    try:
        n = int(raw)
        return n if n > 0 else 120
    except ValueError:
        return 120


def summarize_document(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """POST multipart file to OCR /extract; returns ExtractedPolicy dict."""
    url = f"{_base_url()}/extract"
    try:
        resp = requests.post(
            url,
            files={"file": (filename, file_bytes, "application/pdf")},
            timeout=_timeout(),
        )
        resp.raise_for_status()
    except requests.Timeout as exc:
        raise OCRServiceError(f"OCR service timeout: {exc}") from exc
    except requests.RequestException as exc:
        raise OCRServiceError(str(exc)) from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise OCRServiceError("OCR service returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise OCRServiceError("OCR service returned unexpected response shape")
    return data
