from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.service_factory import get_settings_service
from app.application.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
):
    return await service.get_or_create(user_id)


@router.patch("")
async def patch_settings(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    service: SettingsService = Depends(get_settings_service),
):
    return await service.update(user_id, body)

