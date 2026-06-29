"""Tests for the medical-insurance block produced by ``airtable_record_to_client_data``.

The function lives in ``backend-airtable/main.py``. That directory name contains a
hyphen (not importable as a normal module) and the module performs heavy top-level
imports (FastAPI app, rsu_market, financial_plan_runner). We therefore:

* stub the heavy/optional dependencies in ``sys.modules`` so the import stays fast and
  fully offline (per project testing rules), and
* load the module from its file path under a unique name via importlib to avoid a
  collision with the other ``main`` modules in the repo (agent/main.py, etc.).

Run: ``python -m pytest backend/tests/test_medical_insurance.py -q``
"""

import importlib.util
import sys
import types
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_AIRTABLE = _REPO_ROOT / "backend-airtable"
_BACKEND_SHARED = _REPO_ROOT / "backend"
for _p in (_BACKEND_AIRTABLE, _BACKEND_SHARED):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _make_stub(name: str, **attrs) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


# Keep the import light + offline: stub the dependencies main.py imports at top level
# that pull in heavy/optional packages. ``airtable_record_to_client_data`` does not use
# any of them, so stubbing is safe for this test. The stubs are installed ONLY for the
# duration of the module load and then sys.modules is restored, so other backend tests
# in the same pytest session still import the real modules.
_STUBS = {
    "stdio_utf8": _make_stub("stdio_utf8", force_utf8_stdio=lambda: None),
    "rsu_market": _make_stub(
        "rsu_market",
        get_prices_for_tickers=lambda *a, **k: {},
        get_rsu_market_payload=lambda *a, **k: {},
        refresh_rsu_market_payload=lambda *a, **k: {},
    ),
    "financial_plan_runner": _make_stub(
        "financial_plan_runner",
        FinancialPlanDependencyError=type(
            "FinancialPlanDependencyError", (Exception,), {}
        ),
        run_financial_plan_for_client=lambda *a, **k: {},
    ),
}

_saved_modules = {name: sys.modules.get(name) for name in _STUBS}
sys.modules.update(_STUBS)
try:
    _spec = importlib.util.spec_from_file_location(
        "airtable_api_main", _BACKEND_AIRTABLE / "main.py"
    )
    assert _spec is not None and _spec.loader is not None
    _airtable_api_main = importlib.util.module_from_spec(_spec)
    sys.modules["airtable_api_main"] = _airtable_api_main
    _spec.loader.exec_module(_airtable_api_main)
finally:
    for _name, _original in _saved_modules.items():
        if _original is None:
            sys.modules.pop(_name, None)
        else:
            sys.modules[_name] = _original

airtable_record_to_client_data = _airtable_api_main.airtable_record_to_client_data


def _medical(fields: dict) -> list:
    return airtable_record_to_client_data(fields)["medical_insurance"]


def test_no_medical_fields_yields_empty_list():
    assert _medical({"Name": "Test Client"}) == []


def test_single_employer_policy():
    fields = {
        "Name": "Test Client",
        "medical_insurance_employer_name": "Star Health",
        "medical_insurance_employer_coverage_value": 500000,
    }
    assert _medical(fields) == [
        {
            "policy_type": "Employer",
            "company_name": "Star Health",
            "coverage_value": 500000.0,
        }
    ]


def test_employer_and_self_policies_kept_in_order():
    fields = {
        "Name": "Test Client",
        "medical_insurance_employer_name": "Star Health",
        "medical_insurance_employer_coverage_value": 500000,
        "medical_insurance_self_name": "HDFC Ergo",
        "medical_insurance_self_coverage_value": 1000000,
    }
    assert _medical(fields) == [
        {
            "policy_type": "Employer",
            "company_name": "Star Health",
            "coverage_value": 500000.0,
        },
        {
            "policy_type": "Self",
            "company_name": "HDFC Ergo",
            "coverage_value": 1000000.0,
        },
    ]


def test_self_only_when_employer_blank():
    fields = {
        "Name": "Test Client",
        "medical_insurance_self_name": "Niva Bupa",
        "medical_insurance_self_coverage_value": 750000,
    }
    assert _medical(fields) == [
        {
            "policy_type": "Self",
            "company_name": "Niva Bupa",
            "coverage_value": 750000.0,
        }
    ]


def test_name_without_coverage_still_included_with_zero():
    fields = {
        "Name": "Test Client",
        "medical_insurance_self_name": "Niva Bupa",
    }
    assert _medical(fields) == [
        {"policy_type": "Self", "company_name": "Niva Bupa", "coverage_value": 0.0}
    ]


def test_coverage_without_name_still_included():
    fields = {
        "Name": "Test Client",
        "medical_insurance_employer_coverage_value": 600000,
    }
    assert _medical(fields) == [
        {"policy_type": "Employer", "company_name": "", "coverage_value": 600000.0}
    ]


def test_string_coverage_with_commas_is_parsed():
    fields = {
        "Name": "Test Client",
        "medical_insurance_employer_name": "Care Health",
        "medical_insurance_employer_coverage_value": "10,00,000",
    }
    assert _medical(fields) == [
        {
            "policy_type": "Employer",
            "company_name": "Care Health",
            "coverage_value": 1000000.0,
        }
    ]
