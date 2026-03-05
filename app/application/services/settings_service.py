from datetime import UTC, datetime

from app.infrastructure.db.repositories import MongoRepository


class SettingsService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    async def get_or_create(self, user_id: str) -> dict:
        settings = await self.repo.find_one("user_settings", {"user_id": user_id})
        if settings:
            return settings
        settings_id = await self.repo.insert_one(
            "user_settings",
            {
                "user_id": user_id,
                "busy_mode": False,
                "work_hours": {"start": "09:00", "end": "18:00"},
                "notification_prefs": {"push": True, "email": True},
                "auto_reply_mode": False,
                "calling_agent_enabled": False,
                "updated_at": datetime.now(UTC),
            },
        )
        return await self.repo.find_one("user_settings", {"_id": self.repo.object_id(settings_id)})

    async def update(self, user_id: str, patch: dict) -> dict:
        await self.repo.update_one(
            "user_settings",
            {"user_id": user_id},
            {"$set": {**patch, "updated_at": datetime.now(UTC)}},
            upsert=True,
        )
        return await self.get_or_create(user_id)

