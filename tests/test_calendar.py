import pytest
from datetime import UTC, datetime, timedelta

from app.application.services.calendar_service import CalendarService
from app.application.services.inbox_service import InboxService
from app.infrastructure.adapters.factory import AdapterFactory
from app.infrastructure.calendar.stub import CalendarStub


@pytest.mark.asyncio
async def test_calendar_availability_and_meeting_creation(fake_repo, fake_queue, fake_ws):
    inbox = InboxService(fake_repo, AdapterFactory())
    service = CalendarService(fake_repo, CalendarStub(), inbox, fake_queue, fake_ws)
    conversation_id = await fake_repo.insert_one(
        "conversations",
        {
            "user_id": "u1",
            "platform": "whatsapp",
            "integration_account_id": None,
            "participants": [],
            "external_thread_id": "thread-1",
            "last_message_at": datetime.now(UTC),
            "unread_count": 0,
            "tags": [],
            "status": "open",
            "automation_mode": "manual",
            "last_auto_reply_at": None,
        },
    )

    await service.connect("u1")
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    window_start = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
    window_end = tomorrow.replace(hour=17, minute=0, second=0, microsecond=0)

    slots = await service.availability("u1", window_start, window_end, duration_minutes=30)
    assert slots

    meeting = await service.create_meeting(
        user_id="u1",
        conversation_id=conversation_id,
        title="Client sync",
        start_at=window_start,
        duration_minutes=30,
        agenda="Review next steps",
        send_message_to_client=True,
    )

    assert meeting["meeting_link"].startswith("https://meet.google.com/")
    assert meeting["queued_message"]["status"] == "queued"
    assert len(fake_queue.jobs) == 1
    assert await fake_repo.count("calendar_events", {"user_id": "u1"}) >= 3
