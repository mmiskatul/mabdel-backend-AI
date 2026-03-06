from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class DraftReplyResponse(BaseModel):
    reply_text: str
    confidence: float
    requires_human_review: bool
    safe_to_auto_send: bool = False
    reason: str | None = None
    tags: list[str] = Field(default_factory=list)


class AutoReplyDecision(BaseModel):
    should_reply: bool
    reply_text: str
    reason: str
    confidence: float
    safe_to_auto_send: bool
    requires_human_review: bool = True
    prompt_injection_detected: bool = False
    sensitive_topic: bool = False


class SmartFlowResponse(BaseModel):
    answer: str
    suggested_actions: list[dict] = Field(default_factory=list)
