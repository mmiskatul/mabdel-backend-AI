from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.domain.enums import Platform


class NormalizedInboundMessage(BaseModel):
    platform: Platform
    external_account_id: str
    external_thread_id: str
    external_contact_id: str
    contact_name: str
    text: str
    timestamp: datetime
    platform_message_id: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class NormalizedSendResult(BaseModel):
    success: bool
    platform_message_id: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class OutboundMessageRequest(BaseModel):
    text: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class OAuthTokenPayload(BaseModel):
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    language: str = "en"
    timezone: str = "UTC"

