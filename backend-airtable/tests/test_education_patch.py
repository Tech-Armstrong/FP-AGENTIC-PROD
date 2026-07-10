"""Tests for education destination PATCH mapping and airtable_slot."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

BACKEND_AIRTABLE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_AIRTABLE))

from education_fields import (  # noqa: E402
    EducationPatchValidationError,
    coerce_education_destination,
    validate_education_patch_fields,
)
from main import airtable_record_to_client_data  # noqa: E402


def test_coerce_education_destination_normalizes_case():
    assert coerce_education_destination("international") == "International"
    assert coerce_education_destination("DOMESTIC") == "Domestic"


def test_coerce_education_destination_rejects_invalid():
    with pytest.raises(EducationPatchValidationError, match="Invalid education destination"):
        coerce_education_destination("Abroad")


def test_validate_education_patch_fields_rejects_unknown_keys():
    with pytest.raises(EducationPatchValidationError, match="Unknown education fields"):
        validate_education_patch_fields({"child_1_graduation_destination": "Domestic", "Name": "x"})


def test_airtable_slot_uses_real_child_column_when_child_1_empty():
    fields = {
        "Name": "Client",
        "child_2_name": "Asha",
        "child_2_dob": "2010-01-01",
        "child_2_graduation_stream": "MBBS",
        "child_2_graduation_destination": "International",
        "child_2_post_graduation_stream": "NA",
        "child_2_post_graduation_destination": "NA",
    }
    payload = airtable_record_to_client_data(fields)
    edu = payload["education_planning"]
    assert len(edu) == 1
    assert edu[0]["airtable_slot"] == 2
    assert edu[0]["graduation_destination"] == "International"
    assert edu[0]["name_of_kid"] == "Asha"


@patch.dict("os.environ", {"AIRTABLE_TOKEN": "test-token"})
@patch("main.http_requests.get")
@patch("main.http_requests.patch")
def test_patch_client_data_updates_education_destination(mock_patch, mock_get):
    import main  # noqa: WPS433

    mock_patch.return_value = MagicMock(status_code=200, json=lambda: {"fields": {}})
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "fields": {
                "Name": "Client",
                "child_2_name": "Asha",
                "child_2_dob": "2010-01-01",
                "child_2_graduation_stream": "MBBS",
                "child_2_graduation_destination": "International",
                "child_2_post_graduation_stream": "NA",
                "child_2_post_graduation_destination": "NA",
            },
        },
    )

    client = TestClient(main.app)
    response = client.patch(
        "/clients/recTEST",
        json={"fields": {"child_2_graduation_destination": "International"}},
    )

    assert response.status_code == 200
    patch_body = mock_patch.call_args.kwargs["json"]
    assert patch_body == {"fields": {"child_2_graduation_destination": "International"}}
    payload = response.json()
    assert payload["client_data"]["education_planning"][0]["airtable_slot"] == 2
    assert (
        payload["client_data"]["education_planning"][0]["graduation_destination"]
        == "International"
    )
