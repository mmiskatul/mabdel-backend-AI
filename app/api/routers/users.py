from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_admin_user_id
from app.api.service_factory import get_user_service
from app.users.models import UserListResponse, UserRecord, UserStatus
from app.users.service import UserService

router = APIRouter(prefix="/admin/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    month: str | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    _: str = Depends(get_current_admin_user_id),
    service: UserService = Depends(get_user_service),
):
    return UserListResponse(users=await service.list_users(month=month, status=status))


@router.patch("/{user_id}/status", response_model=UserRecord)
async def update_user_status(
    user_id: str,
    status: UserStatus = Query(...),
    _: str = Depends(get_current_admin_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.update_status(user_id, status)
