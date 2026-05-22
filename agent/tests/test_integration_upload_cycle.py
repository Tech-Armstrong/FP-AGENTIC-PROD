"""
Integration: interrupt → respond → resume cycle (stubbed).

Simulates: client respond payload → finalize → cached state → tool sees document.
"""

from __future__ import annotations

import json

from policy_document_tool import finalize_client_upload, request_policy_document
from policy_documents import get_cached_policy


def test_full_upload_resume_cycle():
    thread = "integration-thread"
    respond_payload = {
        "uploaded": True,
        "filename": "plan.pdf",
        "fileType": "application/pdf",
        "fileData": "dGVzdA==",
        "extractedText": "Coverage limit: INR 10,00,000. Annual premium: INR 25,000.",
    }
    tool_json = finalize_client_upload(
        respond_payload,
        thread_id=thread,
        document_type="insurance_policy",
    )
    parsed = json.loads(tool_json)
    assert parsed["status"] == "uploaded"
    assert "Coverage limit" in parsed["extracted_text"]

    # Follow-up in same thread: tool must not ask for upload again
    again = json.loads(
        request_policy_document.invoke(
            {"document_type": "insurance_policy", "reason": "again"},
            config={"configurable": {"thread_id": thread}},
        )
    )
    assert again["status"] == "already_uploaded"
    assert again["extracted_text"] == parsed["extracted_text"]
    assert get_cached_policy(thread)["extracted_text"] == parsed["extracted_text"]
