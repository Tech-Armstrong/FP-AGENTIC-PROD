"""
Policy PDF OCR processor.

Wire your existing process_pdf / Azure Document Intelligence + LLM pipeline here.
All credentials MUST come from environment variables — never hardcode keys.
"""

from __future__ import annotations

import json
import logging
import os

from models import ExtractedPolicy

log = logging.getLogger("ocr-service.processor")

_CONFIG_KEYS = (
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "GROQ_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)

_REQUIRED_KEYS = (
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
)


def _env(name: str) -> str | None:
    val = os.getenv(name)
    if val is None:
        return None
    stripped = str(val).strip()
    return stripped or None


def log_config_status() -> None:
    """Log presence of keys only — never log secret values."""
    for name in _CONFIG_KEYS:
        log.info("config %s=%s", name, "set" if _env(name) else "missing")


def log_extracted_policy(policy: ExtractedPolicy, filename: str) -> None:
    """Print extracted OCR summary to the server console (no secrets)."""
    payload = policy.compact_dump()
    log.info("=== OCR extracted: %s ===", filename)
    log.info("\n%s", json.dumps(payload, indent=2, ensure_ascii=False))


def process_pdf(file_bytes: bytes, filename: str) -> ExtractedPolicy:
    """
    Run OCR + LLM summarization on a policy PDF.

    Replace this stub with your real pipeline (Azure DI → Groq/Azure OpenAI extract).
    """
    log_config_status()

    missing = [k for k in _REQUIRED_KEYS if not _env(k)]
    if missing:
        raise RuntimeError(
            f"OCR processor not configured. Set env vars: {', '.join(missing)}"
        )

    # TODO: plug in real process_pdf implementation (Azure DI + summarizer).
    # Stub returns minimal shape so integration can be tested end-to-end.
    log.warning(
        "process_pdf stub active for %s (%d bytes) — replace with real OCR pipeline",
        filename,
        len(file_bytes),
    )
    policy = ExtractedPolicy(
        insurer="(stub — configure OCR pipeline)",
        product_name=filename,
        notes="Replace ocr-service/processor.py with your Azure DI + LLM summarizer.",
    )
    log_extracted_policy(policy, filename)
    return policy
