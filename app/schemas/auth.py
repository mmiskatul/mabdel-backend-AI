from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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


class ForgotPasswordOptionsResponse(BaseModel):
    channels: list[Literal["email", "sms"]]
    masked_email: str | None = None
    masked_phone: str | None = None


class SendVerificationCodeRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    channel: Literal["email", "sms"]


class SendVerificationCodeResponse(BaseModel):
    message: str
    expires_in_seconds: int
    dev_verification_code: str | None = None


class VerifyOtpRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=120)
    code: str = Field(min_length=4, max_length=4)


class VerifyOtpResponse(BaseModel):
    reset_token: str
    expires_in_seconds: int


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(min_length=24, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str

