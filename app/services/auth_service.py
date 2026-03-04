from datetime import timedelta

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_otp_code,
    generate_reset_token,
    hash_password,
    hash_secret_value,
    utc_now,
    verify_password,
)
from app.models.auth import AccountEntity
from app.repositories.base import IAuthRepository
from app.schemas.auth import (
    ForgotPasswordOptionsResponse,
    LoginRequest,
    LoginResponse,
    ResetPasswordRequest,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    SignUpRequest,
    VerifyOtpRequest,
    VerifyOtpResponse,
)


class AuthService:
    def __init__(self, repository: IAuthRepository):
        self.repository = repository

    async def sign_up(self, payload: SignUpRequest) -> LoginResponse:
        email = payload.email.strip().lower()
        phone = self._normalize_phone(payload.phone)

        existing_email = await self.repository.get_by_email(email)
        if existing_email is not None:
            raise ValueError("Email is already registered.")

        existing_phone = await self.repository.get_by_phone(phone)
        if existing_phone is not None:
            raise ValueError("Phone number is already registered.")

        now = utc_now()
        account = AccountEntity(
            full_name=payload.full_name.strip(),
            email=email,
            phone=phone,
            password_hash=hash_password(payload.password),
            created_at=now,
            updated_at=now,
        )

        created = await self.repository.create(account)
        token = create_access_token(created.id)
        return LoginResponse(access_token=token, user=self._to_user_read(created))

    async def login(self, payload: LoginRequest) -> LoginResponse:
        identifier = self._normalize_identifier(payload.identifier)
        account = await self.repository.get_by_identifier(identifier)
        if account is None or not verify_password(payload.password, account.password_hash):
            raise ValueError("Invalid credentials.")
        if not account.is_active:
            raise ValueError("Account is inactive.")

        token = create_access_token(account.id)
        return LoginResponse(access_token=token, user=self._to_user_read(account))

    async def forgot_password_options(
        self,
        identifier: str,
    ) -> ForgotPasswordOptionsResponse:
        normalized_identifier = self._normalize_identifier(identifier)
        account = await self.repository.get_by_identifier(normalized_identifier)
        if account is None:
            raise ValueError("Account not found.")

        channels: list[str] = []
        masked_email: str | None = None
        masked_phone: str | None = None

        if account.email:
            channels.append("email")
            masked_email = self._mask_email(account.email)
        if account.phone:
            channels.append("sms")
            masked_phone = self._mask_phone(account.phone)

        return ForgotPasswordOptionsResponse(
            channels=channels,
            masked_email=masked_email,
            masked_phone=masked_phone,
        )

    async def send_verification_code(
        self,
        payload: SendVerificationCodeRequest,
    ) -> SendVerificationCodeResponse:
        account = await self._get_account_by_identifier(payload.identifier)
        if payload.channel == "email" and not account.email:
            raise ValueError("Email verification is not available for this account.")
        if payload.channel == "sms" and not account.phone:
            raise ValueError("SMS verification is not available for this account.")

        code = generate_otp_code()
        now = utc_now()
        account.reset_code_hash = hash_secret_value(code)
        account.reset_code_expires_at = now + timedelta(minutes=settings.otp_code_expire_minutes)
        account.reset_code_channel = payload.channel
        account.reset_token_hash = None
        account.reset_token_expires_at = None
        account.updated_at = now

        await self.repository.update(account)
        return SendVerificationCodeResponse(
            message="Verification code sent.",
            expires_in_seconds=settings.otp_code_expire_minutes * 60,
            dev_verification_code=code if settings.expose_test_verification_code else None,
        )

    async def verify_otp(self, payload: VerifyOtpRequest) -> VerifyOtpResponse:
        account = await self._get_account_by_identifier(payload.identifier)
        if account.reset_code_hash is None or account.reset_code_expires_at is None:
            raise ValueError("No active verification code.")
        if account.reset_code_expires_at < utc_now():
            raise ValueError("Verification code expired.")
        if hash_secret_value(payload.code) != account.reset_code_hash:
            raise ValueError("Invalid verification code.")

        token = generate_reset_token()
        now = utc_now()
        account.reset_token_hash = hash_secret_value(token)
        account.reset_token_expires_at = now + timedelta(minutes=settings.reset_token_expire_minutes)
        account.reset_code_hash = None
        account.reset_code_expires_at = None
        account.reset_code_channel = None
        account.updated_at = now
        await self.repository.update(account)

        return VerifyOtpResponse(
            reset_token=token,
            expires_in_seconds=settings.reset_token_expire_minutes * 60,
        )

    async def reset_password(self, payload: ResetPasswordRequest) -> None:
        token_hash = hash_secret_value(payload.reset_token)
        account = await self.repository.get_by_reset_token_hash(token_hash)
        if account is None or account.reset_token_expires_at is None:
            raise ValueError("Invalid reset token.")
        if account.reset_token_expires_at < utc_now():
            raise ValueError("Reset token expired.")

        now = utc_now()
        account.password_hash = hash_password(payload.new_password)
        account.reset_token_hash = None
        account.reset_token_expires_at = None
        account.updated_at = now
        await self.repository.update(account)

    async def _get_account_by_identifier(self, identifier: str) -> AccountEntity:
        normalized = self._normalize_identifier(identifier)
        account = await self.repository.get_by_identifier(normalized)
        if account is None:
            raise ValueError("Account not found.")
        return account

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        cleaned = phone.strip().replace(" ", "").replace("-", "")
        return cleaned

    def _normalize_identifier(self, identifier: str) -> str:
        trimmed = identifier.strip()
        if "@" in trimmed:
            return trimmed.lower()
        return self._normalize_phone(trimmed)

    @staticmethod
    def _mask_email(email: str) -> str:
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[:2] + "*" * (len(local) - 2)
        return f"{masked_local}@{domain}"

    @staticmethod
    def _mask_phone(phone: str) -> str:
        if len(phone) <= 4:
            return "*" * len(phone)
        return "*" * (len(phone) - 4) + phone[-4:]

    @staticmethod
    def _to_user_read(account: AccountEntity) -> dict:
        return {
            "id": account.id,
            "full_name": account.full_name,
            "email": account.email,
            "phone": account.phone,
            "is_active": account.is_active,
        }

