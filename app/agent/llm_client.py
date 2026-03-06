from abc import ABC, abstractmethod

from app.agent.models import AutoReplyDecision, DraftReplyResponse, SmartFlowResponse, SummaryResponse
from app.agent.prompts import UNIFIED_INBOX_SYSTEM_PROMPT, analyze_inbound_text, safe_review_reply
from app.shared.config import get_settings


class LLMClient(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> SummaryResponse:
        raise NotImplementedError

    @abstractmethod
    async def draft_reply(self, text: str) -> DraftReplyResponse:
        raise NotImplementedError

    @abstractmethod
    async def auto_reply_decision(self, text: str) -> AutoReplyDecision:
        raise NotImplementedError

    @abstractmethod
    async def ask(self, text: str) -> SmartFlowResponse:
        raise NotImplementedError


class StubLLMClient(LLMClient):
    async def summarize(self, text: str) -> SummaryResponse:
        _ = UNIFIED_INBOX_SYSTEM_PROMPT
        analysis = analyze_inbound_text(text)
        preview = analysis["normalized_text"][:250] if analysis["normalized_text"] else "No conversation text available."
        key_points = ["Inbound context analyzed", "Top intent identified"]
        if analysis["prompt_injection_detected"]:
            key_points.append("Prompt-injection style content detected")
        if analysis["sensitive_topic"]:
            key_points.append("Sensitive handling required")
        return SummaryResponse(
            summary=f"Summary: {preview}",
            key_points=key_points,
            action_items=["Review draft reply", "Confirm next action"],
        )

    async def draft_reply(self, text: str) -> DraftReplyResponse:
        analysis = analyze_inbound_text(text)
        secure_channel = bool(analysis["secret_request_detected"])
        reply_text = safe_review_reply(text, secure_channel=secure_channel)
        tags = ["draft", "review_required"]
        if analysis["prompt_injection_detected"]:
            tags.append("prompt_injection")
        if analysis["sensitive_topic"]:
            tags.append("sensitive")
        return DraftReplyResponse(
            reply_text=reply_text,
            confidence=0.58 if analysis["prompt_injection_detected"] else 0.72,
            requires_human_review=True,
            safe_to_auto_send=False,
            reason="secure_review_required" if secure_channel else "draft_only_policy",
            tags=tags,
        )

    async def auto_reply_decision(self, text: str) -> AutoReplyDecision:
        analysis = analyze_inbound_text(text)
        if analysis["prompt_injection_detected"] or analysis["sensitive_topic"]:
            return AutoReplyDecision(
                should_reply=False,
                reply_text="",
                reason="sensitive_or_untrusted_inbound",
                confidence=0.92 if analysis["prompt_injection_detected"] else 0.89,
                safe_to_auto_send=False,
                requires_human_review=True,
                prompt_injection_detected=bool(analysis["prompt_injection_detected"]),
                sensitive_topic=bool(analysis["sensitive_topic"]),
            )
        return AutoReplyDecision(
            should_reply=True,
            reply_text=safe_review_reply(text),
            reason="routine_busy_mode_candidate",
            confidence=0.72,
            safe_to_auto_send=True,
            requires_human_review=False,
            prompt_injection_detected=False,
            sensitive_topic=False,
        )

    async def ask(self, text: str) -> SmartFlowResponse:
        analysis = analyze_inbound_text(text)
        if analysis["sensitive_topic"] or analysis["prompt_injection_detected"]:
            return SmartFlowResponse(
                answer=safe_review_reply(text, secure_channel=bool(analysis["secret_request_detected"])),
                suggested_actions=[],
            )
        return SmartFlowResponse(answer=f"SmartFlow response for: {analysis['normalized_text']}", suggested_actions=[])


def get_llm_client() -> LLMClient:
    _ = get_settings()
    return StubLLMClient()
