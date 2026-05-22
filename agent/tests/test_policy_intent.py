"""Intent detection for policy upload tool."""

from policy_intent import user_message_requests_policy_upload


def test_ulip_message_triggers():
    assert user_message_requests_policy_upload("Please review my ULIP")


def test_policy_cover_triggers():
    assert user_message_requests_policy_upload("What does my insurance policy cover?")


def test_nifty_does_not_trigger():
    assert not user_message_requests_policy_upload("What's the NIFTY today?")


def test_make_plan_does_not_trigger():
    assert not user_message_requests_policy_upload("Run make plan for this client")
