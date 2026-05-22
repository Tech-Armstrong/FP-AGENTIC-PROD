"""Human-in-the-loop tool: request_policy_document (executed on the client via CopilotKit)."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Literal

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from policy_documents import get_cached_policy, process_upload_response, thread_key

log = logging.getLogger("agent")

DocumentType = Literal["insurance_policy", "ulip"]

TOOL_NAME = "request_policy_document"


@tool(TOOL_NAME)
def request_policy_document(
    document_type: DocumentType,
    reason: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
) -> str:
    """
    Pause the chat and ask the user to upload their insurance policy or ULIP document.

    Call this when the user asks about their insurance policy, life insurance, term plan,
    ULIP, unit-linked plan, policy coverage, premiums, charges, surrender value, fund
    allocation, or wants a document reviewed — and no policy document has been uploaded
    yet in this conversation thread.

    Do NOT call for general market questions, NIFTY, mutual funds unrelated to ULIP/policy,
    or dashboard Airtable data.

    Args:
        document_type: "insurance_policy" for life/general insurance policies;
            "ulip" for unit-linked insurance plans.
        reason: Short user-facing sentence explaining why the upload is needed.
    """
    tid = thread_key(config)
    cached = get_cached_policy(tid)
    if cached and cached.get("extracted_text"):
        return json.dumps(
            {
                "status": "already_uploaded",
                "document_type": cached.get("document_type"),
                "filename": cached.get("filename"),
                "char_count": cached.get("char_count"),
                "extracted_text": cached["extracted_text"],
                "instruction": (
                    "Answer using this document only. Do not call request_policy_document again."
                ),
            }
        )

    # CopilotKitMiddleware intercepts this tool on the client (renderAndWaitForResponse).
    # If the server body runs, the client did not handle the tool call.
    log.warning(
        "request_policy_document reached server for thread=%s (expected client execution)",
        tid,
    )
    return json.dumps(
        {
            "status": "error",
            "document_type": document_type,
            "error": (
                "Policy upload must be completed in the chat UI. "
                "If you do not see an upload card, refresh and try again."
            ),
            "reason": reason,
        }
    )


def finalize_client_upload(
    payload: dict,
    *,
    thread_id: str,
    document_type: str,
) -> str:
    """Process respond(...) payload from the upload card (also used by /parse-policy-document)."""
    return process_upload_response(
        payload,
        thread_id=thread_id,
        document_type=document_type,
    )
