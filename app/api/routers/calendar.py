from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import CreateMeetingBody
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


@router.get("/availability")
async def calendar_availability(
    date_from: str,
    date_to: str,
    duration_minutes: int = 30,
    user_id: str = Depends(get_current_user_id),
    service: CalendarService = Depends(get_calendar_service),
):
    from datetime import datetime

    return await service.availability(
        user_id,
        datetime.fromisoformat(date_from),
        datetime.fromisoformat(date_to),
        duration_minutes,
    )


@router.post("/meetings")
async def create_meeting(
    body: CreateMeetingBody,
    user_id: str = Depends(get_current_user_id),
    service: CalendarService = Depends(get_calendar_service),
):
    return await service.create_meeting(
        user_id=user_id,
        conversation_id=body.conversation_id,
        title=body.title,
        start_at=body.start_at,
        duration_minutes=body.duration_minutes,
        agenda=body.agenda,
        send_message_to_client=body.send_message_to_client,
    )
