from __future__ import annotations

import secrets
from datetime import UTC, datetime, time, timedelta


class CalendarStub:
    async def connect(self, user_id: str) -> dict:
        return {
            "user_id": user_id,
            "provider": "google_calendar_stub",
            "oauth_url": "https://calendar.example/connect/google",
            "status": "connected",
        }

    async def seed_events(self, user_id: str) -> list[dict]:
        now = datetime.now(UTC)
        tomorrow = (now + timedelta(days=1)).date()
        start_one = datetime.combine(tomorrow, time(hour=11, minute=0), tzinfo=UTC)
        start_two = datetime.combine(tomorrow, time(hour=15, minute=0), tzinfo=UTC)
        return [
            {
                "user_id": user_id,
                "provider": "google_calendar_stub",
                "external_event_id": "seed_1",
                "title": "Sales sync",
                "starts_at": start_one,
                "ends_at": start_one + timedelta(minutes=30),
                "meeting_link": None,
                "participants": [],
                "status": "confirmed",
                "created_by": "system",
                "metadata": {"seeded": True},
            },
            {
                "user_id": user_id,
                "provider": "google_calendar_stub",
                "external_event_id": "seed_2",
                "title": "Operations review",
                "starts_at": start_two,
                "ends_at": start_two + timedelta(minutes=60),
                "meeting_link": None,
                "participants": [],
                "status": "confirmed",
                "created_by": "system",
                "metadata": {"seeded": True},
            },
        ]

    async def create_meeting(self, user_id: str, title: str, start_at: datetime, end_at: datetime) -> dict:
        code = f"{secrets.token_hex(2)}-{secrets.token_hex(2)}-{secrets.token_hex(2)}"
        return {
            "user_id": user_id,
            "provider": "google_calendar_stub",
            "external_event_id": f"meeting_{int(start_at.timestamp())}",
            "title": title,
            "starts_at": start_at,
            "ends_at": end_at,
            "meeting_link": f"https://meet.google.com/{code}",
            "participants": [],
            "status": "confirmed",
            "created_by": "user",
            "metadata": {"provider_mode": "stub"},
        }
