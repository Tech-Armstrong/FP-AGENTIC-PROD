"""Tests for spouse Airtable PATCH mapping and API route."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

BACKEND_AIRTABLE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_AIRTABLE))

from spouse_fields import (  # noqa: E402
    SpousePatchValidationError,
    coerce_spouse_value,
    validate_spouse_patch_fields,
)


def test_validate_spouse_patch_fields_maps_nested_rate_as_percent():
    validated = validate_spouse_patch_fields(
        {"spouse_investment_fd_bond_rate_intrest": 8.5},
    )
    assert validated["spouse_investment_fd_bond_rate_intrest"] == 8.5


def test_validate_spouse_patch_fields_rejects_unknown_keys():
    with pytest.raises(SpousePatchValidationError, match="Unknown spouse fields"):
        validate_spouse_patch_fields({"spouse_name": "Jane", "Name": "Jane"})


def test_coerce_spouse_value_clears_numeric_with_null():
    assert coerce_spouse_value("spouse_investment_mutual_fund_value", "") is None


def test_coerce_spouse_value_clears_text_with_empty_string():
    assert coerce_spouse_value("spouse_name", "") == ""


@patch.dict("os.environ", {"AIRTABLE_TOKEN": "test-token"})
@patch("main.http_requests.get")
@patch("main.http_requests.patch")
def test_patch_client_data_updates_airtable_and_returns_client(mock_patch, mock_get):
    import main  # noqa: WPS433

    mock_patch.return_value = MagicMock(status_code=200, json=lambda: {"fields": {}})
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "fields": {
                "Name": "Client",
                "spouse_name": "Jane Doe",
                "spouse_investment_mutual_fund_value": 5_000_000,
            },
        },
    )

    client = TestClient(main.app)
    response = client.patch(
        "/clients/recTEST",
        json={"fields": {"spouse_name": "Jane Doe", "spouse_investment_mutual_fund_value": 5_000_000}},
    )

    assert response.status_code == 200
    mock_patch.assert_called_once()
    patch_body = mock_patch.call_args.kwargs["json"]
    assert patch_body == {
        "fields": {
            "spouse_name": "Jane Doe",
            "spouse_investment_mutual_fund_value": 5_000_000.0,
        },
    }
    payload = response.json()
    assert payload["record_id"] == "recTEST"
    assert payload["client_data"]["client_data"]["spouse_name"] == "Jane Doe"


@patch.dict("os.environ", {"AIRTABLE_TOKEN": "test-token"})
@patch("main.http_requests.patch")
def test_patch_client_data_surfaces_airtable_error(mock_patch):
    import main  # noqa: WPS433

    mock_patch.return_value = MagicMock(status_code=422, text="Invalid field")

    client = TestClient(main.app)
    response = client.patch(
        "/clients/recTEST",
        json={"fields": {"spouse_name": "Jane"}},
    )

    assert response.status_code == 502
    assert "Airtable error" in response.json()["detail"]
