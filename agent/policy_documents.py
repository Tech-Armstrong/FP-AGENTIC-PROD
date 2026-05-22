"""
Insurance / ULIP policy document upload handling for the chat agent.
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import re
from typing import Any, Literal

DocumentType = Literal["insurance_policy", "ulip"]

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARS = 80_000

_policy_cache: dict[str, dict[str, Any]] = {}


def thread_key(config: dict | None) -> str:
    if not config:
        return "default"
    configurable = config.get("configurable") or {}
    return str(
        configurable.get("thread_id")
        or configurable.get("threadId")
        or "default"
    )


def get_cached_policy(thread_id: str) -> dict[str, Any] | None:
    return _policy_cache.get(thread_id)


def set_cached_policy(thread_id: str, payload: dict[str, Any]) -> None:
    _policy_cache[thread_id] = payload


def _decode_base64_payload(file_data: str) -> bytes:
    raw = (file_data or "").strip()
    if "," in raw and raw.lower().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        return base64.b64decode(raw, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 file data") from exc


def extract_text_from_upload(
    *,
    file_data: str | None = None,
    file_type: str | None = None,
    filename: str | None = None,
    raw_bytes: bytes | None = None,
) -> str:
    """Extract plain text from an uploaded policy file (PDF primary)."""
    data = raw_bytes
    if data is None:
        if not file_data:
            raise ValueError("No file data provided")
        data = _decode_base64_payload(file_data)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")

    ext = (filename or "").lower().rsplit(".", 1)[-1] if filename and "." in filename else ""
    mime = (file_type or "").lower()

    if ext == "pdf" or "pdf" in mime:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "pypdf is required for PDF parsing. pip install pypdf"
            ) from exc
        reader = PdfReader(io.BytesIO(data))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        text = "\n\n".join(parts).strip()
        if not text:
            raise ValueError("Could not extract text from PDF (scanned image PDFs are not supported)")
        return text[:MAX_EXTRACTED_CHARS]

    if ext in ("png", "jpg", "jpeg", "webp") or "image" in mime:
        raise ValueError(
            "Image uploads are accepted in the UI but OCR is not implemented. "
            "Please upload a text-based PDF."
        )

    raise ValueError("Unsupported file type. Upload a PDF policy document.")


def process_upload_response(
    raw_response: Any,
    *,
    thread_id: str,
    document_type: str,
) -> str:
    """
    Turn interrupt / frontend respond payload into a tool result string and cache text.
    """
    if isinstance(raw_response, str):
        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError:
            payload = {"uploaded": False, "note": raw_response}
    elif isinstance(raw_response, dict):
        payload = raw_response
    else:
        payload = {"uploaded": False, "note": str(raw_response)}

    if not payload.get("uploaded"):
        return json.dumps(
            {
                "status": "skipped",
                "document_type": document_type,
                "message": (
                    "User skipped document upload. Answer with general educational "
                    "information only and clearly state you do not have their actual "
                    "policy document."
                ),
            }
        )

    extracted = payload.get("extractedText") or payload.get("extracted_text")
    if not extracted and payload.get("fileData"):
        try:
            extracted = extract_text_from_upload(
                file_data=payload.get("fileData"),
                file_type=payload.get("fileType"),
                filename=payload.get("filename"),
            )
        except (ValueError, RuntimeError) as exc:
            return json.dumps(
                {
                    "status": "error",
                    "document_type": document_type,
                    "error": str(exc),
                }
            )

    if not extracted or not str(extracted).strip():
        return json.dumps(
            {
                "status": "error",
                "document_type": document_type,
                "error": "Upload succeeded but no text could be extracted.",
            }
        )

    text = str(extracted).strip()[:MAX_EXTRACTED_CHARS]
    cache_entry = {
        "document_type": document_type,
        "filename": payload.get("filename"),
        "extracted_text": text,
        "char_count": len(text),
    }
    set_cached_policy(thread_id, cache_entry)

    return json.dumps(
        {
            "status": "uploaded",
            "document_type": document_type,
            "filename": payload.get("filename"),
            "char_count": len(text),
            "extracted_text": text,
            "instruction": (
                "Use ONLY extracted_text for policy-specific facts (coverage, charges, "
                "fund names, surrender values, etc.). If a detail is not in the text, say so."
            ),
        }
    )


def cached_policy_tool_hint(thread_id: str) -> str | None:
    cached = get_cached_policy(thread_id)
    if not cached:
        return None
    preview = cached["extracted_text"][:2000]
    return (
        f"A {cached.get('document_type', 'policy')} document is already on file for this "
        f"thread ({cached.get('filename', 'uploaded file')}, {cached.get('char_count', 0)} chars). "
        f"Do NOT call request_policy_document again. Excerpt:\n{preview}"
    )
