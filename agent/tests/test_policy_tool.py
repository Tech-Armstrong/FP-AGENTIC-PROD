"""request_policy_document tool registration and behavior."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

from policy_document_tool import TOOL_NAME, finalize_client_upload, request_policy_document


def test_tool_name_canonical():
    assert request_policy_document.name == "request_policy_document"
    assert TOOL_NAME == "request_policy_document"


def test_tool_registered_on_agent_lifespan_tools():
    """Bound tools list matches main.py lifespan (searchInternet + request_policy_document)."""
    with patch("main.run_startup_self_test", new_callable=AsyncMock):
        import main

        assert request_policy_document.name == "request_policy_document"
        assert main.search_internet.name == "searchInternet"


def test_cached_thread_returns_already_uploaded():
    from policy_documents import set_cached_policy

    set_cached_policy(
        "cached-1",
        {
            "document_type": "ulip",
            "extracted_text": "Fund X 12%",
            "char_count": 12,
            "filename": "u.pdf",
        },
    )
    config = {"configurable": {"thread_id": "cached-1"}}
    raw = request_policy_document.invoke(
        {"document_type": "ulip", "reason": "need doc"},
        config=config,
    )
    data = json.loads(raw)
    assert data["status"] == "already_uploaded"
    assert "Fund X" in data["extracted_text"]


def test_finalize_client_upload_matches_respond_contract():
    result = json.loads(
        finalize_client_upload(
            {
                "uploaded": True,
                "filename": "p.pdf",
                "fileType": "application/pdf",
                "fileData": "abc",
                "extractedText": "Premium is 5000",
            },
            thread_id="fin-1",
            document_type="insurance_policy",
        )
    )
    assert result["status"] == "uploaded"
    assert result["extracted_text"] == "Premium is 5000"


def test_skip_finalize():
    result = json.loads(
        finalize_client_upload(
            {"uploaded": False},
            thread_id="fin-2",
            document_type="ulip",
        )
    )
    assert result["status"] == "skipped"
