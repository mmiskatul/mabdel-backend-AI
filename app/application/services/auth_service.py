from datetime import UTC, datetime, timedelta

from app.domain.models import LoginRequest, SignupRequest, TokenPair
from app.persistence.repositories import MongoRepository, MongoSessionRepository
from app.shared.config import get_settings
from app.shared.errors import AppError, UnauthorizedError
from app.shared.security import (
    create_access_token,
    create_refresh_token,
    generate_execute_token,
    generate_otp,
    hash_password,
    hash_secret,
    token_fingerprint,
    verify_password,
)


async def ensure_seed_admin(repo: MongoRepository) -> None:
    settings = get_settings()
    email = settings.admin_email.strip().lower()
    password = settings.admin_password
    if not email or not password:
        return

    now = datetime.now(UTC)
    existing = await repo.find_one("users", {"email": email})
    if existing:
        await repo.update_one(
            "users",
            {"_id": repo.object_id(existing["id"])},
            {
                "$set": {
                    "name": settings.admin_name,
                    "password_hash": hash_password(password),
                    "role": "admin",
                    "status": "unblocked",
                    "registered_month": existing.get("registered_month") or now.strftime("%Y-%m"),
                    "password_updated_at": now,
                }
            },
        )
        return

    await repo.insert_one(
        "users",
        {
            "email": email,
            "name": settings.admin_name,
            "password_hash": hash_password(password),
            "role": "admin",
            "status": "unblocked",
            "created_at": now,
            "registered_month": now.strftime("%Y-%m"),
            "last_login_at": None,
            "language": "en",
            "timezone": "UTC",
            "password_updated_at": now,
        },
    )


class AuthService:
    def __init__(self, repo: MongoRepository, sessions: MongoSessionRepository, email_service):
        self.repo = repo
        self.sessions = sessions
        self.email_service = email_service

    async def start_registration(self, payload: SignupRequest, role: str = "admin") -> dict:
        normalized = str(payload.email).strip().lower()
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
                    "pending_name": payload.name,
                    "pending_password_hash": hash_password(payload.password),
                    "pending_language": payload.language,
                    "pending_timezone": payload.timezone,
                    "pending_role": role,
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

    async def complete_registration(self, email: str, code: str) -> dict:
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
        if not doc.get("pending_password_hash") or not doc.get("pending_name"):
            raise AppError("Registration payload missing. Register again.", 400)
        if await self.repo.find_one("users", {"email": normalized}):
            raise AppError("Email already in use.", 409)

        user_id = await self.repo.insert_one(
            "users",
            {
                "email": normalized,
                "name": doc["pending_name"],
                "password_hash": doc["pending_password_hash"],
                "role": doc.get("pending_role", "admin"),
                "created_at": datetime.now(UTC),
                "registered_month": datetime.now(UTC).strftime("%Y-%m"),
                "status": "unblocked",
                "last_login_at": None,
                "language": doc.get("pending_language", "en"),
                "timezone": doc.get("pending_timezone", "UTC"),
            },
        )
        await self.repo.update_one(
            "signup_validations",
            {"email": normalized},
            {
                "$set": {
                    "code_hash": None,
                    "code_expires_at": None,
                    "pending_name": None,
                    "pending_password_hash": None,
                    "pending_language": None,
                    "pending_timezone": None,
                    "pending_role": None,
                    "completed_at": datetime.now(UTC),
                }
            },
        )
        return {
            "user_id": user_id,
            "email": normalized,
            "message": "Registration successful.",
        }

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

    async def customer_login(self, payload: LoginRequest) -> TokenPair:
        user = await self.repo.find_one("users", {"email": str(payload.email).lower()})
        if not user:
            raise UnauthorizedError("Invalid credentials.")
        if user.get("role", "customer") != "customer":
            raise UnauthorizedError("Customer access required.")
        if user.get("status", "unblocked") == "blocked":
            raise UnauthorizedError("Account is blocked.")
        if not verify_password(payload.password, user["password_hash"]):
            raise UnauthorizedError("Invalid credentials.")
        await self.repo.update_one(
            "users",
            {"_id": self.repo.object_id(user["id"])},
            {"$set": {"last_login_at": datetime.now(UTC)}},
        )
        return await self._issue_tokens(user["id"])

    async def admin_login(self, payload: LoginRequest) -> TokenPair:
        user = await self.repo.find_one("users", {"email": str(payload.email).lower()})
        if not user:
            raise UnauthorizedError("Invalid credentials.")
        if user.get("role", "admin") != "admin":
            raise UnauthorizedError("Admin access required.")
        if not verify_password(payload.password, user["password_hash"]):
            raise UnauthorizedError("Invalid credentials.")
        await self.repo.update_one(
            "users",
            {"_id": self.repo.object_id(user["id"])},
            {"$set": {"last_login_at": datetime.now(UTC)}},
        )
        return await self._issue_tokens(user["id"])

    async def start_password_reset(self, email: str) -> dict:
        normalized = email.strip().lower()
        user = await self.repo.find_one("users", {"email": normalized})
        if not user or user.get("role", "admin") != "admin":
            return {
                "email": normalized,
                "message": "If the account exists, a verification code has been sent.",
            }

        code = generate_otp()
        expires_at = datetime.now(UTC) + timedelta(minutes=10)
        await self.repo.update_one(
            "password_reset_requests",
            {"email": normalized},
            {
                "$set": {
                    "email": normalized,
                    "code_hash": hash_secret(code),
                    "code_expires_at": expires_at,
                    "reset_token_hash": None,
                    "reset_token_expires_at": None,
                    "updated_at": datetime.now(UTC),
                }
            },
            upsert=True,
        )
        await self.email_service.send_otp(normalized, code, 10)
        return {
            "email": normalized,
            "message": "Verification code sent.",
            "expires_in_seconds": 600,
            "dev_verification_code": code,
        }

    async def verify_password_reset_code(self, email: str, code: str) -> dict:
        normalized = email.strip().lower()
        doc = await self.repo.find_one("password_reset_requests", {"email": normalized})
        if not doc:
            raise AppError("No password reset request found.", 400)
        if not doc.get("code_hash") or not doc.get("code_expires_at"):
            raise AppError("No active password reset code.", 400)

        code_exp = doc["code_expires_at"]
        if code_exp.tzinfo is None:
            code_exp = code_exp.replace(tzinfo=UTC)
        if code_exp < datetime.now(UTC):
            raise AppError("Password reset code expired.", 400)
        if hash_secret(code) != doc["code_hash"]:
            raise AppError("Invalid password reset code.", 400)

        reset_token = generate_execute_token()
        await self.repo.update_one(
            "password_reset_requests",
            {"email": normalized},
            {
                "$set": {
                    "code_hash": None,
                    "code_expires_at": None,
                    "reset_token_hash": hash_secret(reset_token),
                    "reset_token_expires_at": datetime.now(UTC) + timedelta(minutes=15),
                    "verified_at": datetime.now(UTC),
                }
            },
        )
        return {
            "email": normalized,
            "message": "Verification successful.",
            "reset_token": reset_token,
            "expires_in_seconds": 900,
        }

    async def reset_password(
        self,
        email: str,
        reset_token: str,
        new_password: str,
        confirm_password: str,
        current_password: str | None = None,
    ) -> dict:
        if new_password != confirm_password:
            raise AppError("Passwords do not match.", 400)

        normalized = email.strip().lower()
        user = await self.repo.find_one("users", {"email": normalized})
        if not user or user.get("role", "admin") != "admin":
            raise AppError("Admin account not found.", 404)

        if current_password and not verify_password(current_password, user["password_hash"]):
            raise AppError("Current password is incorrect.", 400)

        doc = await self.repo.find_one("password_reset_requests", {"email": normalized})
        if not doc or not doc.get("reset_token_hash") or not doc.get("reset_token_expires_at"):
            raise AppError("Password reset verification missing.", 400)

        token_exp = doc["reset_token_expires_at"]
        if token_exp.tzinfo is None:
            token_exp = token_exp.replace(tzinfo=UTC)
        if token_exp < datetime.now(UTC):
            raise AppError("Password reset token expired.", 400)
        if hash_secret(reset_token) != doc["reset_token_hash"]:
            raise AppError("Invalid password reset token.", 400)

        await self.repo.update_one(
            "users",
            {"_id": self.repo.object_id(user["id"])},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "password_updated_at": datetime.now(UTC),
                }
            },
        )
        await self.repo.update_one(
            "password_reset_requests",
            {"email": normalized},
            {
                "$set": {
                    "reset_token_hash": None,
                    "reset_token_expires_at": None,
                    "completed_at": datetime.now(UTC),
                }
            },
        )
        return {
            "email": normalized,
            "message": "Password reset successful.",
        }

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
