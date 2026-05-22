"""POST /parse-policy-document FastAPI route."""

from __future__ import annotations

import base64
import json
from unittest.mock import patch


def test_parse_route_valid_input(client, sample_pdf_b64):
    with patch(
        "main.extract_text_from_upload",
        return_value="Route parsed text",
    ):
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
    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted_text"] == "Route parsed text"
    assert data["char_count"] == len("Route parsed text")
    assert data["thread_id"] == "route-thread"
    assert data["tool_result"]["status"] == "uploaded"

    from policy_documents import get_cached_policy

    assert get_cached_policy("route-thread")["extracted_text"] == "Route parsed text"


def test_parse_route_bad_input(client):
    with patch(
        "main.extract_text_from_upload",
        side_effect=ValueError("Unsupported file type"),
    ):
        resp = client.post(
            "/parse-policy-document",
            json={"fileData": base64.b64encode(b"x").decode()},
        )
    assert resp.status_code == 400
    assert "Unsupported" in resp.json()["detail"]
