from app.agent.models import AutoReplyDecision


def enforce_auto_reply_guardrails(
    decision: AutoReplyDecision,
    automation_mode: str,
    auto_reply_mode_enabled: bool,
    rule_enabled: bool,
) -> AutoReplyDecision:
    if automation_mode != "auto" or not auto_reply_mode_enabled or not rule_enabled:
        decision.should_reply = False
        decision.safe_to_auto_send = False
        decision.reason = "Auto-send disabled by policy."
        return decision
    if decision.confidence < 0.6:
        decision.should_reply = False
        decision.safe_to_auto_send = False
        decision.reason = "Low confidence."
        return decision
    return decision

