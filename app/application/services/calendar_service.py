from app.infrastructure.calendar.stub import CalendarStub


class CalendarService:
    def __init__(self, calendar_stub: CalendarStub):
        self.calendar = calendar_stub

    async def connect(self, user_id: str) -> dict:
        return await self.calendar.connect(user_id)

    async def upcoming(self, user_id: str, days: int = 7) -> list[dict]:
        return await self.calendar.upcoming_events(user_id, days)

