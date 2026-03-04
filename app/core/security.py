import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings

PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, password_hash = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
    except ValueError:
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(candidate_hash, password_hash)


def create_access_token(subject: str) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "iat": int(now.timestamp()), "exp": int(expires_at.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def hash_secret_value(value: str) -> str:
    return hashlib.sha256(f"{value}:{settings.jwt_secret_key}".encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    return f"{secrets.randbelow(10000):04d}"


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def utc_now() -> datetime:
    return datetime.now(UTC)

