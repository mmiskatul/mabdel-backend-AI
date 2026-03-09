from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.persistence.repositories import MongoRepository, MongoSessionRepository
from app.shared.errors import ForbiddenError, UnauthorizedError
from app.shared.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_repo() -> MongoRepository:
    return MongoRepository()


def get_session_repo() -> MongoSessionRepository:
    return MongoSessionRepository()


def validate_access_token(token: str) -> str:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    if payload.get("exp", 0) < int(datetime.now(UTC).timestamp()):
        raise UnauthorizedError("Token expired")
    return str(payload["sub"])


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    return validate_access_token(credentials.credentials)


async def get_current_admin_user_id(
    user_id: str = Depends(get_current_user_id),
    repo: MongoRepository = Depends(get_repo),
) -> str:
    user = await repo.find_one("users", {"_id": repo.object_id(user_id)})
    if not user:
        raise UnauthorizedError("User not found")
    if user.get("role") != "admin":
        raise ForbiddenError("Admin access required")
    return user_id
