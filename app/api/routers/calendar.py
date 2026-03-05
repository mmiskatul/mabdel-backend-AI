from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.service_factory import get_calendar_service
from app.application.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/connect")
async def calendar_connect(
    user_id: str = Depends(get_current_user_id),
    service: CalendarService = Depends(get_calendar_service),
):
    return await service.connect(user_id)


@router.get("/events/upcoming")
async def upcoming_events(
    days: int = 7,
    user_id: str = Depends(get_current_user_id),
    service: CalendarService = Depends(get_calendar_service),
):
    return await service.upcoming(user_id, days)

