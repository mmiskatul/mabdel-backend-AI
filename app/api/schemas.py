from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class SignupSendCodeRequest(BaseModel):
    email: EmailStr


class SignupVerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{4}$")


class SignupRequestSchema(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)
    language: str = "en"
    timezone: str = "UTC"
    signup_validation_token: str


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class RefreshRequestSchema(BaseModel):
    refresh_token: str


class OutboundMessageBody(BaseModel):
    text: str
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    send_as_ai: bool = False


class MarkReadBody(BaseModel):
    pass


class TagsBody(BaseModel):
    tags: list[str]


class ForwardBody(BaseModel):
    to_conversation_id: str | None = None
    target_platform: str | None = None
    text: str | None = None


class InvoiceCreateBody(BaseModel):
    title: str = "Invoice Draft"
    invoice_number: str = "INV-0001"
    amount: float = 0
    currency: str = "USD"
    due_date: datetime | None = None
    recipient: str | None = None
    line_items: list[dict[str, Any]] = Field(default_factory=list)


class InvoicePatchBody(BaseModel):
    amount: float | None = None
    due_date: datetime | None = None
    line_items: list[dict[str, Any]] | None = None


class SendDocumentBody(BaseModel):
    channel: str = "email"


class UploadRecordingBody(BaseModel):
    recording_url: str


class InterpretCommandBody(BaseModel):
    text: str
    context: dict[str, Any] | None = None


class ExecuteCommandBody(BaseModel):
    execute_token: str


class SmartFlowBody(BaseModel):
    text: str


class CalendarAvailabilityQuery(BaseModel):
    date_from: datetime
    date_to: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)


class CreateMeetingBody(BaseModel):
    conversation_id: str
    title: str = Field(min_length=3, max_length=120)
    start_at: datetime
    duration_minutes: int = Field(default=30, ge=15, le=180)
    agenda: str | None = None
    send_message_to_client: bool = True
