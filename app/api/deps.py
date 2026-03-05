from datetime import UTC, datetime, timedelta
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.interfaces.queue import JobQueue
from app.infrastructure.db.repositories import MongoRepository, MongoSessionRepository
from app.infrastructure.queue.arq_queue import ArqJobQueue
from app.shared.errors import UnauthorizedError
from app.shared.security import decode_token, token_fingerprint

bearer = HTTPBearer(auto_error=False)


def get_repo() -> MongoRepository:
    return MongoRepository()


def get_session_repo() -> MongoSessionRepository:
    return MongoSessionRepository()


def get_queue() -> JobQueue:
    return ArqJobQueue()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session_repo: MongoSessionRepository = Depends(get_session_repo),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    user_id = str(payload["sub"])
    if payload.get("exp", 0) < int(datetime.now(UTC).timestamp()):
        raise UnauthorizedError("Token expired")
    return user_id


async def validate_refresh_token(
    refresh_token: str,
    session_repo: MongoSessionRepository,
) -> str:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token type")
    fp = token_fingerprint(refresh_token)
    active = await session_repo.is_refresh_token_active(fp)
    if not active:
        raise UnauthorizedError("Refresh token revoked or expired")
    return str(payload["sub"])

