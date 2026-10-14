"""Tests for PPT generation helpers and workflow_state serialization."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from financial_plan_runner import json_safe_workflow_state  # noqa: E402
from Financial_Planning.Utilities.ppt_runner import (  # noqa: E402
    PptTemplateError,
    default_template_path,
    generate_financial_plan_ppt,
    sanitize_client_filename,
)


def test_json_safe_workflow_state_round_trips_date():
    raw = {"as_of": date(2026, 6, 30), "nested": {"value": 1}}
    safe = json_safe_workflow_state(raw)
    assert safe["as_of"] == "2026-06-30"
    assert safe["nested"]["value"] == 1


def test_sanitize_client_filename_strips_invalid_chars():
    assert sanitize_client_filename('Aakash / "Test"') == "Aakash  Test"
    assert sanitize_client_filename("") == "Client"
    assert sanitize_client_filename("   ") == "Client"


def test_generate_financial_plan_ppt_rejects_empty_state():
    with pytest.raises(ValueError, match="non-empty dict"):
        generate_financial_plan_ppt({})


def test_generate_financial_plan_ppt_missing_template():
    with pytest.raises(PptTemplateError, match="template not found"):
        generate_financial_plan_ppt(
            {"client_data": {"client_data": {"name": "X"}}},
            template_path="/nonexistent/template.pptx",
        )


def test_generate_financial_plan_ppt_returns_pk_zip_with_mocks():
    """Smoke test: mocked populate + LLM produces a valid zip (pptx) buffer."""
    from pptx import Presentation

    template = default_template_path()
    if not Path(template).is_file():
        pytest.skip("PPT template not present on this machine")

    prs = Presentation(template)

    def fake_populate(presentation, final_state, llm_azure):
        return final_state["client_data"]["client_data"]["name"]

    with patch(
        "Financial_Planning.Utilities.ppt_runner._build_azure_llm",
        return_value=MagicMock(),
    ), patch(
        "Financial_Planning.Utilities.ppt_runner.populate_presentation",
        side_effect=lambda p, s, _llm: fake_populate(p, s, _llm),
    ), patch(
        "Financial_Planning.Utilities.ppt_runner.Presentation",
        return_value=prs,
    ):
        ppt_bytes, filename = generate_financial_plan_ppt(
            {"client_data": {"client_data": {"name": "Priya"}}},
            template_path=template,
        )

    assert ppt_bytes[:2] == b"PK"
    assert filename == "Priya_financial_plan.pptx"


def test_generate_financial_plan_ppt_missing_azure_env():
    template = default_template_path()
    if not Path(template).is_file():
        pytest.skip("PPT template not present on this machine")

    from Financial_Planning.Utilities.ppt_runner import PptDependencyError

    with patch.dict("os.environ", {}, clear=True), patch(
        "Financial_Planning.Utilities.ppt_runner.load_dotenv"
    ):
        with pytest.raises(PptDependencyError, match="AZURE_API"):
            generate_financial_plan_ppt(
                {"client_data": {"client_data": {"name": "X"}}},
                template_path=template,
            )


def test_build_retirement_annuity_slide_adds_table_and_title():
    template = default_template_path()
    if not Path(template).is_file():
        pytest.skip("PPT template not present on this machine")

    from pptx import Presentation
    from Financial_Planning.Utilities.ppt_builder import PPTBuilder
    from Financial_Planning.Utilities.ppt_utilities import duplicate_slide, move_slide

    prs = Presentation(template)
    wealth_idx = 20
    duplicate_slide(prs, wealth_idx)
    move_slide(prs, len(prs.slides) - 1, wealth_idx + 1)

    state = {
        "required_retirement_corpus": {
            "client_info": {"years_to_retirement": 19},
        },
        "retirement_annuity": {
            "model": "income_preservation",
            "retirement_year": 2045,
            "desired_monthly_annuity": 150_000,
            "achievable": True,
            "achievable_monthly_annuity": 150_000,
            "shortfall_monthly": 0,
            "total_available_monthly": 150_000,
            "sources": [
                {
                    "key": "epf_ppf",
                    "label": "EPF / PPF yield",
                    "rate": "8.5%",
                    "monthly_income": 69_125,
                    "corpus_fv": 9_758_793,
                    "required": True,
                },
                {
                    "key": "mutual_funds",
                    "label": "Mutual fund yield",
                    "rate": "10.0%",
                    "monthly_income": 70_623,
                    "corpus_fv": 19_751_402,
                    "required": True,
                },
                {
                    "key": "fixed_deposits",
                    "label": "FD interest",
                    "rate": "6.5%",
                    "monthly_income": 3_584,
                    "corpus_fv": 661_717,
                    "required": True,
                },
            ],
        }
    }
    builder = PPTBuilder(prs, state)
    annuity_idx = wealth_idx + 1
    assert builder.build_retirement_annuity_slide(annuity_idx) is True

    slide = prs.slides[annuity_idx]
    titles = [
        sh.text_frame.text
        for sh in slide.shapes
        if sh.has_text_frame and "annuity" in sh.text_frame.text.lower()
    ]
    assert titles, "expected Retirement Annuity title on slide"
    assert "2045" in titles[0]

    today_sentences = [
        sh.text_frame.text
        for sh in slide.shapes
        if sh.has_text_frame and "today's terms" in sh.text_frame.text.lower()
    ]
    assert len(today_sentences) == 1, f"expected one today's-terms sentence, got: {today_sentences}"
    assert today_sentences[0].startswith("This Rs.")
    assert "6% inflation" in today_sentences[0]
    assert "1,50,000" in today_sentences[0] or "150,000" in today_sentences[0]

    tables = [s for s in slide.shapes if s.has_table]
    assert tables
    header = [tables[0].table.cell(0, c).text for c in range(3)]
    assert header[0].lower().startswith("source")
    assert "growth" in header[1].lower()
    assert "monthly" in header[2].lower()
    # header + 3 sources + total used
    assert tables[0].table.rows.__len__() == 5
    assert "Total used" in tables[0].table.cell(4, 0).text
    assert "8.5%" in tables[0].table.cell(1, 1).text


def test_build_retirement_annuity_slide_skips_without_sources():
    from pptx import Presentation
    from Financial_Planning.Utilities.ppt_builder import PPTBuilder

    prs = Presentation()
    prs.slides.add_slide(prs.slide_layouts[6])
    builder = PPTBuilder(prs, {"retirement_annuity": {"desired_monthly_annuity": 0}})
    assert builder.build_retirement_annuity_slide(0) is False


def test_annuity_source_label_includes_rate_and_corpus():
    from Financial_Planning.Utilities.ppt_builder import PPTBuilder

    label = PPTBuilder._annuity_source_label(
        {
            "key": "epf_ppf",
            "label": "EPF / PPF yield",
            "rate": "8.5%",
            "corpus_fv": 1_000_000,
            "required": True,
        },
        include_rate=True,
    )
    assert "EPF / PPF yield @ 8.5%" in label
    assert "corpus" in label.lower()
    assert PPTBuilder._annuity_growth_rate({"rate": "8.5%"}) == "8.5%"
    assert PPTBuilder._annuity_growth_rate({"rate": "-"}) == "-"

    template = default_template_path()
    if not Path(template).is_file():
        pytest.skip("PPT template not present on this machine")

    from pptx import Presentation
    from Financial_Planning.Utilities.ppt_builder import PPTBuilder

    prs = Presentation(template)
    state = {
        "required_retirement_corpus": {"client_info": {"current_monthly_expenses": 100_000}},
        "client_data": {"education_planning_summary": [], "insurance_policies": []},
        "liabilities": [{"outstanding_balance": 500_000}],
        "liquid_pool": 200_000,
        "term_insurance_summary": {
            "pv_of_expenses": 20_000_000,
            "kids_education_cost": 1_000_000,
            "current_liabilities": 500_000,
            "existing_cover": 0,
            "liquidable_assets": 200_000,
            "total_term_required": 21_300_000,
        },
    }
    builder = PPTBuilder(prs, state)
    assert builder.build_term_cover_slide(22) is True
    tables = [s for s in prs.slides[22].shapes if s.has_table]
    assert tables
    assert "21,300,000" in tables[0].table.cell(6, 1).text or "2,13,00,000" in tables[0].table.cell(6, 1).text


def test_replace_pie_chart_without_template_chart_does_not_raise():
    """Wealth slide may lack a pie placeholder — chart is placed at default coords."""
    from pptx import Presentation
    from Financial_Planning.Utilities.ppt_utilities import replace_pie_chart_with_matplotlib

    prs = Presentation()
    layout = prs.slide_layouts[6]
    prs.slides.add_slide(layout)
    replace_pie_chart_with_matplotlib(
        prs,
        0,
        {"EPF": 0.5, "PPF": 0.5},
        "Wealth Created - 2045",
    )
    assert len(prs.slides[0].shapes) >= 1


def test_find_term_cover_slide_after_optional_deletes():
    template = default_template_path()
    if not Path(template).is_file():
        pytest.skip("PPT template not present on this machine")

    from pptx import Presentation
    from Financial_Planning.Utilities.ppt_runner import _resolve_term_cover_slide
    from Financial_Planning.Utilities.ppt_utilities import delete_slide, find_slide_index_by_text

    prs = Presentation(template)
    for idx in sorted([16, 17, 18, 19, 14, 15, 7], reverse=True):
        if idx < len(prs.slides):
            delete_slide(prs, idx)

    assert find_slide_index_by_text(prs, "{term cover heading}") is not None
    term_idx = _resolve_term_cover_slide(prs, slide_offset=0)
    assert "{term cover heading}" in (
        prs.slides[term_idx].shapes[2].text_frame.text.lower()
    )
