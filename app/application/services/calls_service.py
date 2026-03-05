from datetime import UTC, datetime

from app.infrastructure.db.repositories import MongoRepository
from app.shared.errors import NotFoundError


class CallsService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    async def list_calls(self, user_id: str, filter_value: str = "all") -> list[dict]:
        query = {"user_id": user_id}
        if filter_value != "all":
            query["status"] = filter_value
        return await self.repo.find_many("calls", query, limit=100, sort=[("created_at", -1)])

    async def get_call(self, user_id: str, call_id: str) -> dict:
        call = await self.repo.find_one("calls", {"_id": self.repo.object_id(call_id), "user_id": user_id})
        if not call:
            raise NotFoundError("Call not found.")
        return call

    async def mark_callback(self, user_id: str, call_id: str) -> dict:
        await self.repo.update_one(
            "calls",
            {"_id": self.repo.object_id(call_id), "user_id": user_id},
            {"$set": {"status": "callback_needed"}},
        )
        return await self.get_call(user_id, call_id)

    async def monthly_stats(self, user_id: str) -> dict:
        calls = await self.repo.find_many("calls", {"user_id": user_id}, limit=200)
        total = len(calls)
        total_seconds = sum(int(item.get("total_seconds", 0) or 0) for item in calls)
        return {
            "total_calls": total,
            "total_seconds": total_seconds,
            "total_minutes": round(total_seconds / 60, 2),
            "missed": len([c for c in calls if c.get("status") == "missed"]),
            "callback_needed": len([c for c in calls if c.get("status") == "callback_needed"]),
        }

    async def upload_recording(self, user_id: str, call_id: str, recording_url: str) -> dict:
        await self.repo.update_one(
            "calls",
            {"_id": self.repo.object_id(call_id), "user_id": user_id},
            {"$set": {"recording_url": recording_url, "updated_at": datetime.now(UTC)}},
        )
        return await self.get_call(user_id, call_id)

    async def transcribe(self, user_id: str, call_id: str) -> dict:
        await self.repo.update_one(
            "calls",
            {"_id": self.repo.object_id(call_id), "user_id": user_id},
            {"$set": {"transcript_text": "Transcription stub output.", "updated_at": datetime.now(UTC)}},
        )
        return await self.get_call(user_id, call_id)

    async def summarize(self, user_id: str, call_id: str) -> dict:
        await self.repo.update_one(
            "calls",
            {"_id": self.repo.object_id(call_id), "user_id": user_id},
            {
                "$set": {
                    "ai_summary": "Call summary stub.",
                    "ai_ready": True,
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        return await self.get_call(user_id, call_id)

