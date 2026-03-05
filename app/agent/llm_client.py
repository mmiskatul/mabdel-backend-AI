from abc import ABC, abstractmethod

from app.agent.models import AutoReplyDecision, DraftReplyResponse, SmartFlowResponse, SummaryResponse
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
        preview = text[:250] if text else "No conversation text available."
        return SummaryResponse(
            summary=f"Summary: {preview}",
            key_points=["Inbound context analyzed", "Top intent identified"],
            action_items=["Review draft reply", "Confirm next action"],
        )

    async def draft_reply(self, text: str) -> DraftReplyResponse:
        _ = text
        return DraftReplyResponse(
            reply_text="Thanks for reaching out. I can help with that and will follow up shortly.",
            confidence=0.74,
            requires_human_review=True,
            tags=["draft", "safe"],
        )

    async def auto_reply_decision(self, text: str) -> AutoReplyDecision:
        sensitive = any(keyword in text.lower() for keyword in ["legal", "payment dispute", "threat", "emergency"])
        if sensitive:
            return AutoReplyDecision(
                should_reply=False,
                reply_text="",
                reason="Sensitive topic detected.",
                confidence=0.89,
                safe_to_auto_send=False,
            )
        return AutoReplyDecision(
            should_reply=True,
            reply_text="Thanks for your message. We are currently in busy mode and will get back to you soon.",
            reason="Busy mode safe fallback.",
            confidence=0.72,
            safe_to_auto_send=True,
        )

    async def ask(self, text: str) -> SmartFlowResponse:
        return SmartFlowResponse(answer=f"SmartFlow response for: {text}", suggested_actions=[])


def get_llm_client() -> LLMClient:
    _ = get_settings()
    return StubLLMClient()

