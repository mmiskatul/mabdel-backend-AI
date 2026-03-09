from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    text: str
    created_at: datetime | None = None


class AgentSessionResponse(BaseModel):
    session_id: str
    created_at: datetime


class AgentReplyResponse(BaseModel):
    session_id: str
    reply_text: str
    turns: list[AgentMessage] = Field(default_factory=list)


class RealtimeUserMessage(BaseModel):
    type: Literal["user_message"]
    text: str = Field(min_length=1)


class RealtimeAgentEvent(BaseModel):
    type: Literal["session_ready", "assistant_message", "agent_status", "error"]
    session_id: str
    text: str | None = None
    detail: str | None = None
    stage: str | None = None


class AgentGraphState(TypedDict, total=False):
    user_id: str
    session_id: str
    user_text: str
    history: list[dict[str, str]]
    reply_text: str
    persisted_turns: list[dict[str, str]]
