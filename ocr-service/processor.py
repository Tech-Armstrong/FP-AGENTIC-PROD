"""
Policy PDF OCR processor.

Pipeline:  Azure Document Intelligence (prebuilt-layout, pages 1-6)
           -> DSPy ChainOfThought extractor (Claude Sonnet 4.5 on Azure AI)
           -> Pydantic validation into ExtractedPolicy.

Credentials come ONLY from environment variables and use namespaced keys so they
never collide with the gpt-4o agent (which reads AZURE_OPENAI_* / AZURE_API_*):

    Azure Document Intelligence : AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT / _KEY
    Claude extraction (DSPy)    : AZURE_EXTRACTION_ENDPOINT / _KEY / _DEPLOYMENT

NOTE: do NOT pass api_version to dspy.LM — Claude via LiteLLM breaks if it is set.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import threading

from models import (
    BenefitDetails,
    ExtractedPolicy,
    LifeAssuredDetails,
    NomineeDetails,
    PolicyDetails,
    PolicyholderDetails,
    RiderDetails,
)

log = logging.getLogger("ocr-service.processor")

# Number of leading PDF pages sent to Azure DI (matches the Colab pipeline).
OCR_PAGE_RANGE = os.getenv("OCR_PAGE_RANGE", "1-6")

_CONFIG_KEYS = (
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "AZURE_EXTRACTION_ENDPOINT",
    "AZURE_EXTRACTION_KEY",
    "AZURE_EXTRACTION_DEPLOYMENT",
)

_REQUIRED_KEYS = (
    "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT",
    "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "AZURE_EXTRACTION_ENDPOINT",
    "AZURE_EXTRACTION_KEY",
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
    """Print compact extracted OCR summary to the server console (no secrets)."""
    payload = policy.compact_dump()
    log.info("=== OCR extracted: %s ===", filename)
    log.info("\n%s", json.dumps(payload, indent=2, ensure_ascii=False))


# ==============================================================
#  DSPy extractor — configured lazily, ONCE, inside this process.
# ==============================================================

_dspy_lock = threading.Lock()
_extractor = None  # type: ignore[var-annotated]


class _ExtractInsurancePolicy:
    """Lazily-built dspy.Signature (deferred so importing this module is cheap)."""


def _build_extractor():
    """
    Build and cache the DSPy ChainOfThought extractor.

    dspy.configure() sets a process-global LM. That is safe here because the OCR
    service runs as its own process (port 8010) — the gpt-4o agent lives in a
    separate process and never imports this module.
    """
    global _extractor
    if _extractor is not None:
        return _extractor

    with _dspy_lock:
        if _extractor is not None:
            return _extractor

        import dspy

        endpoint = _env("AZURE_EXTRACTION_ENDPOINT")
        api_key = _env("AZURE_EXTRACTION_KEY")
        deployment = _env("AZURE_EXTRACTION_DEPLOYMENT") or "claude-sonnet-4-5"

        # LiteLLM Azure-AI route. Deliberately NO api_version (breaks Claude).
        lm = dspy.LM(
            model=f"azure_ai/{deployment}",
            api_key=api_key,
            api_base=endpoint,
        )
        dspy.configure(lm=lm)

        class ExtractInsurancePolicy(dspy.Signature):
            """
            Extract ALL structured fields from insurance policy document text.

            Rules:
            - Extract every field you can find; use null for missing values.
            - Monetary amounts are plain numbers (no currency symbols, no commas).
            - Dates as DD/MM/YYYY strings.
            - Output a single strict JSON object matching the schema — no prose, no fences.

            JSON schema:
            {
              "insurer": string,
              "policyholder": {"name": string, "dob": string, "gender": string,
                "address": string, "client_id": string},
              "life_assured": {"name": string, "dob": string, "gender": string,
                "age_at_entry": number, "client_id": string},
              "policy": {"policy_number": string, "plan_name": string, "uin": string,
                "plan_option": string, "plan_type": string, "commencement_date": string,
                "risk_commencement_date": string, "maturity_date": string,
                "policy_term_years": number, "premium_paying_term_years": number,
                "payment_frequency": string, "modal_premium_excl_tax": number,
                "modal_premium_incl_tax": number, "underwriting_extra_premium": number,
                "grace_period_days": number, "free_look_period_days": number,
                "final_premium_due_date": string, "premium_due_dates": string},
              "benefits": {"sum_assured_on_death": number, "maturity_benefit": number,
                "total_income_post_maturity": number, "survival_benefit_amount": number,
                "survival_benefit_frequency": string, "survival_benefit_start": string,
                "survival_benefit_end": string, "income_benefit_amount": number,
                "critical_illness_cover": number, "hospi_cash_per_day": number,
                "other_benefits": [string]},
              "nominee": {"name": string, "relationship": string, "dob": string,
                "age": number, "nomination_pct": number, "appointee_name": string},
              "riders": [{"rider_name": string, "sum_assured": number, "premium": number,
                "maturity_date": string, "term_years": number, "ppt_years": number}],
              "tgriy_table": [{"policy_year": number, "tgriy": number}],
              "special_provisions": [string]
            }
            """

            document_text: str = dspy.InputField(
                desc="Full text extracted from insurance policy PDF (all pages concatenated)"
            )
            json_output: str = dspy.OutputField(
                desc="Strict JSON object only — no markdown, no preamble, no fences"
            )

        _extractor = dspy.ChainOfThought(ExtractInsurancePolicy)
        log.info("DSPy extractor configured (azure_ai/%s)", deployment)
        return _extractor


# ==============================================================
#  Azure Document Intelligence — text + tables from the PDF.
# ==============================================================

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Run prebuilt-layout OCR and return concatenated page text + tables markdown."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    endpoint = _env("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = _env("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    b64 = base64.b64encode(file_bytes).decode("utf-8")
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        {"base64Source": b64},
        pages=OCR_PAGE_RANGE,
    )
    result = poller.result()
    log.info(
        "Azure DI: %d pages | %d tables",
        len(result.pages or []),
        len(result.tables or []),
    )

    pages_text: list[str] = []
    for page in result.pages or []:
        page_lines = [line.content for line in (page.lines or [])]
        pages_text.append("\n".join(page_lines))

    tables_md: list[str] = []
    for table in result.tables or []:
        rows, cols = table.row_count, table.column_count
        grid = [["" for _ in range(cols)] for _ in range(rows)]
        for cell in table.cells:
            grid[cell.row_index][cell.column_index] = str(cell.content).strip()
        # Plain pipe-table so the LLM sees structure without needing pandas.
        lines = [" | ".join(r) for r in grid]
        tables_md.append("\n".join(lines))

    combined = pages_text.copy()
    if tables_md:
        combined.append("\n\n--- TABLES ---\n" + "\n\n".join(tables_md))

    return "\n\n--- PAGE BREAK ---\n\n".join(combined)


# ==============================================================
#  Validation — nested dict -> ExtractedPolicy (lenient).
# ==============================================================

def _safe(model, data, errors: list[str]):
    try:
        return model(**data) if data else None
    except Exception as exc:  # noqa: BLE001 - collect, never crash extraction
        errors.append(f"validation({model.__name__}): {exc}")
        return None


def _validate(parsed: dict, errors: list[str]) -> ExtractedPolicy:
    riders_raw = parsed.get("riders") or []
    riders = [
        r
        for r in (
            _safe(RiderDetails, item, errors)
            for item in riders_raw
            if isinstance(item, dict)
        )
        if r
    ]

    return ExtractedPolicy(
        insurer=parsed.get("insurer"),
        policyholder=_safe(PolicyholderDetails, parsed.get("policyholder") or {}, errors),
        life_assured=_safe(LifeAssuredDetails, parsed.get("life_assured") or {}, errors),
        policy=_safe(PolicyDetails, parsed.get("policy") or {}, errors),
        benefits=_safe(BenefitDetails, parsed.get("benefits") or {}, errors),
        nominee=_safe(NomineeDetails, parsed.get("nominee") or {}, errors),
        riders=riders,
        tgriy_table=parsed.get("tgriy_table") or [],
        special_provisions=parsed.get("special_provisions") or [],
    )


def _parse_json(raw: str) -> dict:
    """Strip accidental markdown fences and parse the JSON object."""
    cleaned = re.sub(r"```(?:json)?|```", "", raw or "").strip()
    return json.loads(cleaned)


# ==============================================================
#  Public entry point — called by main.py /extract.
# ==============================================================

def process_pdf(file_bytes: bytes, filename: str) -> ExtractedPolicy:
    """Run OCR + Claude extraction on a policy PDF and return ExtractedPolicy."""
    log_config_status()

    missing = [k for k in _REQUIRED_KEYS if not _env(k)]
    if missing:
        raise RuntimeError(
            f"OCR processor not configured. Set env vars: {', '.join(missing)}"
        )

    log.info("OCR processing %s (%d bytes)", filename, len(file_bytes))

    # 1) Azure Document Intelligence -> text.
    try:
        document_text = _extract_text_from_pdf(file_bytes)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Azure Document Intelligence failed: {exc}") from exc

    if not document_text.strip():
        raise RuntimeError("Azure DI returned no text (scanned/empty PDF?)")

    # 2) DSPy ChainOfThought (Claude) -> JSON.
    extractor = _build_extractor()
    errors: list[str] = []
    try:
        result = extractor(document_text=document_text)
        parsed = _parse_json(result.json_output or "")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Claude extraction failed: {exc}") from exc

    # 3) Validate into the structured model (lenient — partial data is fine).
    policy = _validate(parsed, errors)
    if errors:
        log.warning("Validation issues for %s: %s", filename, errors)
        existing = (policy.notes or "").strip()
        note = f"Partial extraction: {len(errors)} field group(s) failed validation."
        policy.notes = f"{existing} {note}".strip() if existing else note

    log_extracted_policy(policy, filename)
    return policy
