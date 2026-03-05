import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from app.shared.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_token_days)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def token_fingerprint(token: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{token}:{settings.jwt_secret_key}".encode("utf-8")).hexdigest()


def generate_otp() -> str:
    return f"{secrets.randbelow(10000):04d}"


def hash_secret(value: str) -> str:
    settings = get_settings()
    return hashlib.sha256(f"{value}:{settings.jwt_secret_key}".encode("utf-8")).hexdigest()


def generate_execute_token() -> str:
    return secrets.token_urlsafe(32)


def get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.fernet_key.encode("utf-8"))


def encrypt_text(plain_text: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_text(cipher_text: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")


def safe_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)

