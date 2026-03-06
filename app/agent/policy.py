from app.agent.models import AutoReplyDecision


def enforce_auto_reply_guardrails(
    decision: AutoReplyDecision,
    automation_mode: str,
    auto_reply_mode_enabled: bool,
    rule_enabled: bool,
    backend_auto_send_allowed: bool,
) -> AutoReplyDecision:
    if decision.prompt_injection_detected or decision.sensitive_topic:
        decision.safe_to_auto_send = False
        decision.requires_human_review = True
        decision.reason = "review_required_untrusted_or_sensitive"
        return decision
    if automation_mode != "auto" or not auto_reply_mode_enabled or not rule_enabled:
        decision.safe_to_auto_send = False
        decision.requires_human_review = True
        decision.reason = "draft_only_policy"
        return decision
    if not backend_auto_send_allowed:
        decision.safe_to_auto_send = False
        decision.requires_human_review = True
        decision.reason = "backend_auto_send_disabled"
        return decision
    if decision.confidence < 0.6:
        decision.safe_to_auto_send = False
        decision.requires_human_review = True
        decision.reason = "low_confidence_review_required"
        return decision
    return decision
