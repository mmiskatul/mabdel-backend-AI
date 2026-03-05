from datetime import UTC, datetime, timedelta

from app.domain.models import LoginRequest, SignupRequest, TokenPair
from app.infrastructure.db.repositories import MongoRepository, MongoSessionRepository
from app.shared.errors import AppError, UnauthorizedError
from app.shared.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_password,
    hash_secret,
    token_fingerprint,
    verify_password,
)


class AuthService:
    def __init__(self, repo: MongoRepository, sessions: MongoSessionRepository, email_service):
        self.repo = repo
        self.sessions = sessions
        self.email_service = email_service

    async def send_signup_code(self, email: str) -> dict:
        normalized = email.strip().lower()
        exists = await self.repo.find_one("users", {"email": normalized})
        if exists:
            return {"email": normalized, "is_available": False, "message": "Email already in use."}
        code = generate_otp()
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        await self.repo.update_one(
            "signup_validations",
            {"email": normalized},
            {
                "$set": {
                    "email": normalized,
                    "code_hash": hash_secret(code),
                    "code_expires_at": expires_at,
                    "token_hash": None,
                    "token_expires_at": None,
                    "updated_at": datetime.now(UTC),
                }
            },
            upsert=True,
        )
        await self.email_service.send_otp(normalized, code, 10)
        return {
            "email": normalized,
            "is_available": True,
            "message": "Verification code sent.",
            "expires_in_seconds": 600,
            "dev_verification_code": code,
        }

    async def verify_signup_code(self, email: str, code: str) -> dict:
        normalized = email.strip().lower()
        doc = await self.repo.find_one("signup_validations", {"email": normalized})
        if not doc:
            raise AppError("No signup validation found.", 400)
        if not doc.get("code_hash") or not doc.get("code_expires_at"):
            raise AppError("No active signup code.", 400)
        code_exp = doc["code_expires_at"]
        if code_exp.tzinfo is None:
            code_exp = code_exp.replace(tzinfo=UTC)
        if code_exp < datetime.now(UTC):
            raise AppError("Signup code expired.", 400)
        if hash_secret(code) != doc["code_hash"]:
            raise AppError("Invalid signup code.", 400)

        signup_token = create_refresh_token(normalized)  # short-lived reuse format
        await self.repo.update_one(
            "signup_validations",
            {"email": normalized},
            {
                "$set": {
                    "token_hash": hash_secret(signup_token),
                    "token_expires_at": datetime.now(UTC) + timedelta(minutes=10),
                    "code_hash": None,
                    "code_expires_at": None,
                }
            },
        )
        return {"email": normalized, "signup_validation_token": signup_token, "expires_in_seconds": 600}

    async def signup(self, payload: SignupRequest, signup_validation_token: str) -> TokenPair:
        email = str(payload.email).lower()
        token_doc = await self.repo.find_one("signup_validations", {"email": email})
        if not token_doc or not token_doc.get("token_hash"):
            raise AppError("Signup token missing. Verify email first.", 400)
        token_expires = token_doc["token_expires_at"]
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=UTC)
        if token_expires < datetime.now(UTC):
            raise AppError("Signup token expired.", 400)
        if hash_secret(signup_validation_token) != token_doc["token_hash"]:
            raise AppError("Invalid signup token.", 400)
        if await self.repo.find_one("users", {"email": email}):
            raise AppError("Email already in use.", 409)

        user_id = await self.repo.insert_one(
            "users",
            {
                "email": email,
                "name": payload.name,
                "password_hash": hash_password(payload.password),
                "created_at": datetime.now(UTC),
                "last_login_at": None,
                "language": payload.language,
                "timezone": payload.timezone,
            },
        )
        await self.repo.update_one("signup_validations", {"email": email}, {"$set": {"token_hash": None}})
        return await self._issue_tokens(user_id)

    async def login(self, payload: LoginRequest) -> TokenPair:
        user = await self.repo.find_one("users", {"email": str(payload.email).lower()})
        if not user:
            raise UnauthorizedError("Invalid credentials.")
        if not verify_password(payload.password, user["password_hash"]):
            raise UnauthorizedError("Invalid credentials.")
        await self.repo.update_one(
            "users",
            {"_id": self.repo.object_id(user["id"])},
            {"$set": {"last_login_at": datetime.now(UTC)}},
        )
        return await self._issue_tokens(user["id"])

    async def refresh(self, refresh_token: str) -> TokenPair:
        fp = token_fingerprint(refresh_token)
        if not await self.sessions.is_refresh_token_active(fp):
            raise UnauthorizedError("Refresh token invalid.")
        user_id = str(await self._extract_subject(refresh_token))
        await self.sessions.revoke_refresh_token(fp)
        return await self._issue_tokens(user_id)

    async def _issue_tokens(self, user_id: str) -> TokenPair:
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        await self.sessions.store_refresh_token(
            user_id=user_id,
            token_hash=token_fingerprint(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=14),
        )
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def _extract_subject(token: str) -> str:
        from app.shared.security import decode_token

        return str(decode_token(token)["sub"])
