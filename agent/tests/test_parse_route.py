"""POST /parse-policy-document — rejects raw PDF; accepts OCR summary."""

from __future__ import annotations

import json


def test_parse_route_rejects_raw_pdf(client, sample_pdf_b64):
    resp = client.post(
        "/parse-policy-document",
        json={
            "filename": "policy.pdf",
            "fileType": "application/pdf",
            "fileData": sample_pdf_b64,
            "thread_id": "route-thread",
            "document_type": "ulip",
        },
    )
    assert resp.status_code == 400
    assert "Raw PDF" in resp.json()["detail"]


def test_parse_route_accepts_policy_summary(client):
    summary = {
        "insurer": "Test Life",
        "sum_assured": "500000",
        "annual_premium": "25000",
    }
    resp = client.post(
        "/parse-policy-document",
        json={
            "filename": "policy.pdf",
            "fileType": "application/pdf",
            "policy_summary": summary,
            "thread_id": "route-thread",
            "document_type": "ulip",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_summary"] == summary
    assert data["thread_id"] == "route-thread"
    assert data["tool_result"]["status"] == "uploaded"
    assert "Test Life" in data["tool_result"]["extracted_text"]

    from policy_documents import get_cached_policy

    cached = get_cached_policy("route-thread")
    assert cached is not None
    assert cached["policy_summary"]["insurer"] == "Test Life"
