from __future__ import annotations

from app.persistence.repositories import MongoRepository
from app.shared.errors import AppError, NotFoundError
from app.users.models import UserRecord


class UserService:
    def __init__(self, repo: MongoRepository):
        self.repo = repo

    async def list_users(self, month: str | None = None, status: str | None = None) -> list[UserRecord]:
        query: dict[str, str] = {"role": "customer"}
        if month:
            query["registered_month"] = month
        if status:
            query["status"] = status

        users = await self.repo.find_many("users", query, limit=500, sort=[("created_at", -1)])
        records: list[UserRecord] = []
        for user in users:
            registered_month = user.get("registered_month")
            if not registered_month and user.get("created_at"):
                registered_month = user["created_at"].strftime("%Y-%m")
            records.append(
                UserRecord(
                    id=user["id"],
                    email=user["email"],
                    name=user.get("name", ""),
                    role=user.get("role", "customer"),
                    status=user.get("status", "unblocked"),
                    registered_month=registered_month or "unknown",
                    created_at=user.get("created_at"),
                )
            )
        return records

    async def update_status(self, user_id: str, status: str) -> UserRecord:
        existing = await self.repo.find_one("users", {"_id": self.repo.object_id(user_id)})
        if not existing:
            raise NotFoundError("User not found")
        if existing.get("role") != "customer":
            raise AppError("Only customer accounts can be blocked or unblocked.", 400)

        await self.repo.update_one(
            "users",
            {"_id": self.repo.object_id(user_id)},
            {"$set": {"status": status}},
        )
        updated = await self.repo.find_one("users", {"_id": self.repo.object_id(user_id)})
        registered_month = updated.get("registered_month")
        if not registered_month and updated.get("created_at"):
            registered_month = updated["created_at"].strftime("%Y-%m")
        return UserRecord(
            id=updated["id"],
            email=updated["email"],
            name=updated.get("name", ""),
            role=updated.get("role", "customer"),
            status=updated.get("status", "unblocked"),
            registered_month=registered_month or "unknown",
            created_at=updated.get("created_at"),
        )
