from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.service_factory import get_dashboard_service
from app.application.services.dashboard_service import DashboardService

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/widgets")
async def widgets(
    user_id: str = Depends(get_current_user_id),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_dashboard(user_id)

