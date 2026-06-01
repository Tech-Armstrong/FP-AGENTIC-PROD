"""Tests for user-entered education target corpus override in calculate_education_funding."""

from datetime import date

from Financial_Planning.Nodes.child_education_nodes import calculate_education_funding


def _base_state(*, user_ug_target: float | None = None):
    child_name = "Aarav"
    child_dob = "2010-06-01"
    education_row = {
        "name_of_kid": child_name,
        "dob": child_dob,
        "graduation_stream": "B.Tech",
        "graduation_destination": "Domestic",
        "course_duration_ug": 4,
        "course_duration_pg": None,
        "fund_allocated_for_graduation": 0,
        "post_graduation_stream": "NA",
        "post_graduation_destination": None,
        "scheme_for_education": [],
        "current_fees_of_graduation": 1_000_000,
        "current_fees_of_post_graduation": 1_200_000,
    }
    if user_ug_target is not None:
        education_row["user_target_corpus_graduation"] = user_ug_target

    return {
        "client_data": {
            "education_planning": [education_row],
            "client_data": {
                "children": [{"child_name": child_name, "child_dob": child_dob}],
            },
        }
    }


def test_user_target_corpus_used_as_future_cost_without_inflation():
    override = 5_000_000.0
    state = _base_state(user_ug_target=override)
    result = calculate_education_funding(state)
    summary = result["client_data"]["education_planning_summary"]
    ug_goals = [g for g in summary if g["type"] == "UG"]
    assert len(ug_goals) == 1
    assert ug_goals[0]["future_cost"] == override


def test_missing_user_target_still_inflates_from_lookup_cost():
    state = _base_state()
    result = calculate_education_funding(state)
    summary = result["client_data"]["education_planning_summary"]
    ug_goals = [g for g in summary if g["type"] == "UG"]
    assert len(ug_goals) == 1
    years = ug_goals[0]["years_to_goal"]
    expected = 1_000_000 * (1.06 ** years)
    assert ug_goals[0]["future_cost"] == round(expected, 2)
    assert ug_goals[0]["future_cost"] != 5_000_000
