from app.infrastructure.db.repositories import MongoRepository


class DashboardService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    async def get_dashboard(self, user_id: str) -> dict:
        user = await self.repo.find_one("users", {"_id": self.repo.object_id(user_id)})
        unread_total = await self.repo.count("conversations", {"user_id": user_id, "unread_count": {"$gt": 0}})
        conversations = await self.repo.find_many(
            "conversations",
            {"user_id": user_id},
            limit=3,
            sort=[("last_message_at", -1)],
        )
        contacts_count = await self.repo.count("contacts", {"user_id": user_id})
        contacts_preview = await self.repo.find_many("contacts", {"user_id": user_id}, limit=3)
        integrations = await self.repo.find_many("integration_accounts", {"user_id": user_id}, limit=12)
        docs = await self.repo.aggregate(
            "documents",
            [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": "$doc_type", "count": {"$sum": 1}}},
            ],
        )
        calls_count = await self.repo.count("calls", {"user_id": user_id})
        calls_preview = await self.repo.find_many("calls", {"user_id": user_id}, limit=3, sort=[("created_at", -1)])
        activity = await self.repo.find_many("activity_events", {"user_id": user_id}, limit=5, sort=[("created_at", -1)])
        return {
            "greeting_name": (user or {}).get("name", "User"),
            "unread_total_count": unread_total,
            "unified_conversations_preview": conversations,
            "contacts_count": contacts_count,
            "contacts_preview": contacts_preview,
            "upcoming_calendar_event": {
                "title": "No connected calendar",
                "starts_at": None,
            },
            "integrations_connected": integrations,
            "documents_shortcuts": docs,
            "call_analytics": {
                "total_calls": calls_count,
                "minutes_saved": calls_count * 3,
                "last_calls_preview": calls_preview,
            },
            "recent_activity_preview": activity,
        }

