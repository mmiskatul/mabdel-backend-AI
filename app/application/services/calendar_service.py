from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from app.application.services.inbox_service import InboxService
from app.infrastructure.calendar.stub import CalendarStub
from app.infrastructure.db.repositories import MongoRepository
from app.shared.errors import AppError


class CalendarService:
    def __init__(self, repo: MongoRepository, calendar_provider: CalendarStub, inbox: InboxService, queue, ws_manager):
        self.repo = repo
        self.calendar = calendar_provider
        self.inbox = inbox
        self.queue = queue
        self.ws_manager = ws_manager

    async def connect(self, user_id: str) -> dict:
        connection = await self.calendar.connect(user_id)
        existing = await self.repo.find_one("calendar_connections", {"user_id": user_id})
        now = datetime.now(UTC)
        payload = {
            "user_id": user_id,
            "provider": connection["provider"],
            "status": connection["status"],
            "oauth_url": connection["oauth_url"],
            "connected_at": now,
            "updated_at": now,
        }
        if existing:
            await self.repo.update_one(
                "calendar_connections",
                {"_id": self.repo.object_id(existing["id"])},
                {"$set": payload},
            )
            connection_id = existing["id"]
        else:
            connection_id = await self.repo.insert_one("calendar_connections", payload)
            for event in await self.calendar.seed_events(user_id):
                await self.repo.insert_one("calendar_events", event | {"created_at": now, "updated_at": now})
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": "calendar_connected",
                "ref": {"type": "calendar_connection", "id": connection_id},
                "title": "Calendar connected",
                "subtitle": connection["provider"],
                "created_at": now,
            },
        )
        return {"connection_id": connection_id, **connection}

    async def upcoming(self, user_id: str, days: int = 7) -> list[dict]:
        await self._ensure_connected(user_id)
        now = datetime.now(UTC)
        events = await self.repo.find_many(
            "calendar_events",
            {"user_id": user_id},
            limit=200,
            sort=[("starts_at", 1)],
        )
        horizon = now + timedelta(days=days)
        return [
            event
            for event in events
            if self._to_utc(event["starts_at"]) >= now and self._to_utc(event["starts_at"]) <= horizon
        ]

    async def availability(
        self,
        user_id: str,
        date_from: datetime,
        date_to: datetime,
        duration_minutes: int = 30,
    ) -> list[dict]:
        await self._ensure_connected(user_id)
        start_range = self._to_utc(date_from)
        end_range = self._to_utc(date_to)
        if start_range >= end_range:
            raise AppError("date_from must be earlier than date_to.", 400)

        busy_events = await self.repo.find_many("calendar_events", {"user_id": user_id}, limit=500, sort=[("starts_at", 1)])
        busy_windows = [
            (self._to_utc(event["starts_at"]), self._to_utc(event["ends_at"]))
            for event in busy_events
            if self._overlaps(self._to_utc(event["starts_at"]), self._to_utc(event["ends_at"]), start_range, end_range)
        ]

        slots: list[dict] = []
        duration = timedelta(minutes=duration_minutes)
        day_cursor = start_range.date()
        while day_cursor <= end_range.date():
            day_start = datetime.combine(day_cursor, time(hour=9, minute=0), tzinfo=UTC)
            day_end = datetime.combine(day_cursor, time(hour=17, minute=0), tzinfo=UTC)
            slot_start = max(day_start, start_range)
            latest_start = min(day_end, end_range) - duration
            while slot_start <= latest_start:
                slot_end = slot_start + duration
                if not any(self._overlaps(slot_start, slot_end, busy_start, busy_end) for busy_start, busy_end in busy_windows):
                    slots.append(
                        {
                            "starts_at": slot_start.isoformat(),
                            "ends_at": slot_end.isoformat(),
                            "duration_minutes": duration_minutes,
                        }
                    )
                slot_start += duration
            day_cursor += timedelta(days=1)
        return slots

    async def create_meeting(
        self,
        user_id: str,
        conversation_id: str,
        title: str,
        start_at: datetime,
        duration_minutes: int,
        agenda: str | None = None,
        send_message_to_client: bool = True,
    ) -> dict:
        await self._ensure_connected(user_id)
        conversation = await self.inbox.get_conversation(user_id, conversation_id)
        start_utc = self._to_utc(start_at)
        end_utc = start_utc + timedelta(minutes=duration_minutes)
        meeting = await self.calendar.create_meeting(user_id, title, start_utc, end_utc)
        now = datetime.now(UTC)
        event_id = await self.repo.insert_one(
            "calendar_events",
            {
                **meeting,
                "conversation_id": conversation["id"],
                "agenda": agenda,
                "created_at": now,
                "updated_at": now,
            },
        )

        outbound_message = None
        if send_message_to_client:
            message_text = self._meeting_message(title, start_utc, duration_minutes, meeting["meeting_link"], agenda)
            outbound_message = await self.inbox.queue_outbound_message(
                user_id=user_id,
                conversation_id=conversation["id"],
                text=message_text,
                attachments=[],
                send_as_ai=True,
            )
            await self.queue.enqueue("send_message", {"message_id": outbound_message["id"]})

        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": "meeting_created",
                "ref": {"type": "calendar_event", "id": event_id},
                "title": title,
                "subtitle": start_utc.isoformat(),
                "created_at": now,
            },
        )
        await self.ws_manager.emit(
            user_id,
            "activity.new",
            {
                "event_type": "meeting_created",
                "calendar_event_id": event_id,
                "conversation_id": conversation["id"],
            },
        )
        return {
            "id": event_id,
            "meeting_link": meeting["meeting_link"],
            "starts_at": start_utc.isoformat(),
            "ends_at": end_utc.isoformat(),
            "queued_message": outbound_message,
        }

    async def _ensure_connected(self, user_id: str) -> dict:
        connection = await self.repo.find_one("calendar_connections", {"user_id": user_id})
        if not connection:
            await self.connect(user_id)
            connection = await self.repo.find_one("calendar_connections", {"user_id": user_id})
        if not connection:
            raise AppError("Calendar connection could not be initialized.", 500)
        return connection

    @staticmethod
    def _meeting_message(
        title: str,
        start_at: datetime,
        duration_minutes: int,
        meeting_link: str,
        agenda: str | None,
    ) -> str:
        agenda_line = f"\nAgenda: {agenda}" if agenda else ""
        return (
            f"I've scheduled \"{title}\" for {start_at.strftime('%Y-%m-%d %H:%M UTC')} "
            f"for {duration_minutes} minutes.\nJoin here: {meeting_link}{agenda_line}"
        )

    @staticmethod
    def _to_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _overlaps(start_one: datetime, end_one: datetime, start_two: datetime, end_two: datetime) -> bool:
        return start_one < end_two and start_two < end_one
