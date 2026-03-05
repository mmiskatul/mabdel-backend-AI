from datetime import UTC, datetime, timedelta


class CalendarStub:
    async def connect(self, user_id: str) -> dict:
        return {"user_id": user_id, "oauth_url": "https://calendar.example/connect"}

    async def upcoming_events(self, user_id: str, days: int = 7) -> list[dict]:
        now = datetime.now(UTC)
        return [
            {
                "id": "event_1",
                "user_id": user_id,
                "title": "Client Follow-up",
                "starts_at": (now + timedelta(days=1)).isoformat(),
                "location": "Virtual",
            }
        ]

