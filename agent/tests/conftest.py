"""Pytest fixtures — no live Azure/Tavily/Airtable."""

from __future__ import annotations

import base64
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

AGENT_DIR = Path(__file__).resolve().parent.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))


@pytest.fixture
def client():
    with patch("main.run_startup_self_test", new_callable=AsyncMock):
        import main
        from fastapi.testclient import TestClient

        with TestClient(main.app) as tc:
            yield tc


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    try:
        from io import BytesIO

        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject

        writer = PdfWriter()
        page = writer.add_blank_page(width=200, height=200)
        content = b"BT /F1 24 Tf 50 100 Td (SAMPLE_POLICY_KNOWN_TEXT) Tj ET"
        stream = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject("/Contents")] = stream
        buf = BytesIO()
        writer.write(buf)
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def sample_pdf_b64(sample_pdf_bytes: bytes) -> str:
    return base64.b64encode(sample_pdf_bytes).decode("ascii")


@pytest.fixture(autouse=True)
def clear_policy_cache():
    from policy_documents import _policy_cache

    _policy_cache.clear()
    yield
    _policy_cache.clear()
