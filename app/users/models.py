from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr


UserStatus = Literal["blocked", "unblocked"]


class UserRecord(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    status: UserStatus
    registered_month: str
    created_at: datetime | None = None


class UserStatusUpdate(BaseModel):
    user_id: str
    status: UserStatus


class UserListResponse(BaseModel):
    users: list[UserRecord]
