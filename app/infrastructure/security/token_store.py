from datetime import UTC, datetime

from app.shared.security import decrypt_text, encrypt_text


def encrypt_oauth_tokens(access_token: str, refresh_token: str | None = None) -> dict:
    return {
        "access_token_enc": encrypt_text(access_token),
        "refresh_token_enc": encrypt_text(refresh_token) if refresh_token else None,
        "stored_at": datetime.now(UTC),
    }


def decrypt_oauth_access_token(encrypted: str) -> str:
    return decrypt_text(encrypted)

