from pydantic import BaseModel, EmailStr, Field


class RegisterRequestSchema(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(min_length=8)
    language: str = "en"
    timezone: str = "UTC"


class RegisterVerifyRequestSchema(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{4}$")


class ForgotPasswordRequestSchema(BaseModel):
    email: EmailStr


class ForgotPasswordVerifyRequestSchema(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{4}$")


class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    current_password: str | None = None


class LoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class RefreshRequestSchema(BaseModel):
    refresh_token: str


class AgentRealtimeMessageBody(BaseModel):
    text: str = Field(min_length=1)
