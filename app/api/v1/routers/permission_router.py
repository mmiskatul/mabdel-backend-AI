from fastapi import APIRouter, Depends

from app.dependencies import get_permission_service
from app.schemas.permission import PermissionRead, PermissionToggle, PermissionUpdate
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/{user_id}", response_model=PermissionRead)
async def get_permissions(
    user_id: str,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.get_permissions(user_id)
    return PermissionRead.model_validate(permission.__dict__)


@router.patch("/{user_id}", response_model=PermissionRead)
async def update_permissions(
    user_id: str,
    payload: PermissionUpdate,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.update_permissions(user_id, payload)
    return PermissionRead.model_validate(permission.__dict__)


@router.post("/{user_id}/accept-all", response_model=PermissionRead)
async def accept_all_permissions(
    user_id: str,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.accept_all(user_id)
    return PermissionRead.model_validate(permission.__dict__)


@router.patch("/{user_id}/microphone", response_model=PermissionRead)
async def toggle_microphone_permission(
    user_id: str,
    payload: PermissionToggle,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.set_microphone(user_id, payload.enabled)
    return PermissionRead.model_validate(permission.__dict__)


@router.patch("/{user_id}/notifications", response_model=PermissionRead)
async def toggle_notifications_permission(
    user_id: str,
    payload: PermissionToggle,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.set_notifications(user_id, payload.enabled)
    return PermissionRead.model_validate(permission.__dict__)


@router.patch("/{user_id}/contacts", response_model=PermissionRead)
async def toggle_contacts_permission(
    user_id: str,
    payload: PermissionToggle,
    service: PermissionService = Depends(get_permission_service),
) -> PermissionRead:
    permission = await service.set_contacts(user_id, payload.enabled)
    return PermissionRead.model_validate(permission.__dict__)
