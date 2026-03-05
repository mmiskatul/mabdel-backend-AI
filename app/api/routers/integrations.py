from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.service_factory import get_integration_service
from app.application.services.integration_service import IntegrationService
from app.domain.enums import Platform

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/catalog")
async def catalog(
    user_id: str = Depends(get_current_user_id),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.catalog(user_id)


@router.post("/{platform}/connect")
async def connect(
    platform: Platform,
    user_id: str = Depends(get_current_user_id),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.connect(user_id, platform)


@router.post("/{platform}/disconnect")
async def disconnect(
    platform: Platform,
    user_id: str = Depends(get_current_user_id),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.disconnect(user_id, platform)

