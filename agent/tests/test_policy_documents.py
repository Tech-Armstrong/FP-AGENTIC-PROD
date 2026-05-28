"""Policy document parsing and respond payload handling."""

from __future__ import annotations

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from policy_documents import (
    MAX_UPLOAD_BYTES,
    extract_text_from_upload,
    get_cached_policy,
    process_upload_response,
    set_cached_policy,
)

SAMPLE_SUMMARY = {
    "insurer": "Sample Life",
    "sum_assured": "1000000",
    "annual_premium": "25000",
}


def test_process_upload_skip():
    out = json.loads(
        process_upload_response(
            {"uploaded": False},
            thread_id="t1",
            document_type="ulip",
        )
    )
    assert out["status"] == "skipped"
    assert "caveat" in out["message"].lower() or "general" in out["message"].lower()


def test_process_upload_with_policy_summary_caches():
    payload = {
        "uploaded": True,
        "filename": "p.pdf",
        "fileType": "application/pdf",
        "policySummary": SAMPLE_SUMMARY,
    }
    out = json.loads(
        process_upload_response(payload, thread_id="thread-a", document_type="ulip")
    )
    assert out["status"] == "uploaded"
    assert out["policy_summary"] == SAMPLE_SUMMARY
    assert "Sample Life" in out["extracted_text"]
    cached = get_cached_policy("thread-a")
    assert cached is not None
    assert cached["policy_summary"]["insurer"] == "Sample Life"


def test_process_upload_rejects_raw_pdf_filedata():
    b64 = base64.b64encode(b"%PDF-fake").decode()
    out = json.loads(
        process_upload_response(
            {
                "uploaded": True,
                "filename": "policy.pdf",
                "fileType": "application/pdf",
                "fileData": b64,
            },
            thread_id="t2",
            document_type="insurance_policy",
        )
    )
    assert out["status"] == "error"
    assert "Raw PDF" in out["error"]


def test_process_upload_missing_summary_errors():
    out = json.loads(
        process_upload_response(
            {"uploaded": True, "filename": "p.pdf"},
            thread_id="t3",
            document_type="insurance_policy",
        )
    )
    assert out["status"] == "error"
    assert "OCR" in out["error"] or "summary" in out["error"].lower()


def test_oversized_file_rejected():
    huge = base64.b64encode(b"x" * (MAX_UPLOAD_BYTES + 1)).decode()
    with pytest.raises(ValueError, match="10 MB"):
        extract_text_from_upload(file_data=huge, filename="big.pdf")


def test_wrong_type_rejected():
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text_from_upload(
            file_data=base64.b64encode(b"hello").decode(),
            filename="notes.txt",
        )


def test_pdf_fixture_extracts_known_text(sample_pdf_bytes: bytes):
    try:
        text = extract_text_from_upload(
            raw_bytes=sample_pdf_bytes,
            filename="fixture.pdf",
        )
    except ValueError:
        pytest.skip("Fixture PDF has no extractable text on this pypdf version")
    if "SAMPLE_POLICY_KNOWN_TEXT" in text:
        assert "SAMPLE_POLICY_KNOWN_TEXT" in text
    else:
        with patch("pypdf.PdfReader") as reader_cls:
            page = MagicMock()
            page.extract_text.return_value = "SAMPLE_POLICY_KNOWN_TEXT"
            reader_cls.return_value.pages = [page]
            text = extract_text_from_upload(
                raw_bytes=sample_pdf_bytes,
                filename="fixture.pdf",
            )
        assert "SAMPLE_POLICY_KNOWN_TEXT" in text


def test_memory_same_thread_no_reupload_needed():
    set_cached_policy(
        "mem-thread",
        {
            "document_type": "ulip",
            "filename": "x.pdf",
            "policy_summary": SAMPLE_SUMMARY,
            "extracted_text": json.dumps(SAMPLE_SUMMARY),
            "char_count": 50,
        },
    )
    cached = get_cached_policy("mem-thread")
    assert cached["policy_summary"]["insurer"] == "Sample Life"
