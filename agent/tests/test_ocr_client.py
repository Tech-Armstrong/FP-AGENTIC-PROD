"""Tests for OCR microservice client (mocked — never hits real service)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from ocr_client import OCRServiceError, summarize_document


def test_summarize_document_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"insurer": "ABC Life", "sum_assured": "1000000"}
    mock_resp.raise_for_status = MagicMock()

    with patch.dict("os.environ", {"OCR_SERVICE_URL": "http://localhost:8010"}):
        with patch("ocr_client.requests.post", return_value=mock_resp) as post:
            out = summarize_document(b"%PDF", "policy.pdf")

    assert out["insurer"] == "ABC Life"
    post.assert_called_once()
    args, kwargs = post.call_args
    assert args[0] == "http://localhost:8010/extract"
    assert kwargs["files"]["file"][0] == "policy.pdf"
    assert kwargs["files"]["file"][1] == b"%PDF"
    assert kwargs["files"]["file"][2] == "application/pdf"


def test_summarize_document_timeout():
    with patch.dict("os.environ", {"OCR_SERVICE_URL": "http://localhost:8010"}):
        with patch(
            "ocr_client.requests.post",
            side_effect=requests.Timeout("slow"),
        ):
            with pytest.raises(OCRServiceError, match="timeout"):
                summarize_document(b"x", "p.pdf")


def test_summarize_document_non_200():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("502")

    with patch.dict("os.environ", {"OCR_SERVICE_URL": "http://localhost:8010"}):
        with patch("ocr_client.requests.post", return_value=mock_resp):
            with pytest.raises(OCRServiceError):
                summarize_document(b"x", "p.pdf")


def test_summarize_document_bad_json():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.side_effect = ValueError("bad json")

    with patch.dict("os.environ", {"OCR_SERVICE_URL": "http://localhost:8010"}):
        with patch("ocr_client.requests.post", return_value=mock_resp):
            with pytest.raises(OCRServiceError, match="invalid JSON"):
                summarize_document(b"x", "p.pdf")


def test_summarize_document_url_unset():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(OCRServiceError, match="OCR_SERVICE_URL"):
            summarize_document(b"x", "p.pdf")
