from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, TypeAdapter, ValidationError, model_validator

PHONE_PATTERN = re.compile(r"^\+?[0-9]{6,20}$")
EMAIL_ADAPTER = TypeAdapter(EmailStr)


def _looks_like_email(value: str) -> bool:
    return "@" in value


def _is_valid_phone(value: str) -> bool:
    normalized = value.strip().replace(" ", "").replace("-", "")
    return bool(PHONE_PATTERN.fullmatch(normalized))


def _is_valid_email(value: str) -> bool:
    try:
        EMAIL_ADAPTER.validate_python(value)
        return True
    except ValidationError:
        return False


class SignUpRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    accept_terms: bool

    @model_validator(mode="after")
    def validate_terms(self) -> "SignUpRequest":
        if not self.accept_terms:
            raise ValueError("Terms and conditions must be accepted.")
        return self


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class AuthUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: EmailStr
    phone: str
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserRead


class ForgotPasswordOptionsRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)

    @model_validator(mode="after")
    def validate_identifier(self) -> "ForgotPasswordOptionsRequest":
        raw = self.identifier.strip()
        if _looks_like_email(raw):
            if not _is_valid_email(raw):
                raise ValueError("Identifier must be a valid email or phone number.")
            return self
        if not _is_valid_phone(raw):
            raise ValueError("Identifier must be a valid email or phone number.")
        return self


class ForgotPasswordOptionsResponse(BaseModel):
    channels: list[Literal["email", "sms"]]
    masked_email: str | None = None
    masked_phone: str | None = None


class SendVerificationCodeRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    channel: Literal["email", "sms"]

    @model_validator(mode="after")
    def validate_channel_and_identifier(self) -> "SendVerificationCodeRequest":
        raw = self.identifier.strip()
        if self.channel == "email":
            if not _looks_like_email(raw):
                raise ValueError("For email channel, identifier must be an email.")
            if not _is_valid_email(raw):
                raise ValueError("For email channel, identifier must be a valid email.")
            return self
        if not _is_valid_phone(raw):
            raise ValueError("For sms channel, identifier must be a valid phone number.")
        return self


class SendVerificationCodeResponse(BaseModel):
    message: str
    expires_in_seconds: int
    dev_verification_code: str | None = None


class VerifyOtpRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    code: str = Field(pattern=r"^\d{4}$")


class VerifyOtpResponse(BaseModel):
    reset_token: str
    expires_in_seconds: int


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=24, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str
