from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from app.domain.interfaces.repositories import Repository, SessionRepository
from app.infrastructure.db.mongo import MongoManager, clean_mongo_document


class MongoRepository(Repository):
    def __init__(self):
        self.db = MongoManager.db()

    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def find_one(self, collection: str, query: dict[str, Any]) -> dict[str, Any] | None:
        doc = await self.db[collection].find_one(query)
        return clean_mongo_document(doc) if doc else None

    async def find_many(
        self,
        collection: str,
        query: dict[str, Any],
        limit: int = 50,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        cursor = self.db[collection].find(query).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        docs = await cursor.to_list(length=limit)
        return [clean_mongo_document(d) for d in docs]

    async def update_one(
        self,
        collection: str,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> None:
        await self.db[collection].update_one(query, update, upsert=upsert)

    async def count(self, collection: str, query: dict[str, Any]) -> int:
        return await self.db[collection].count_documents(query)

    async def aggregate(self, collection: str, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
        docs = await self.db[collection].aggregate(pipeline).to_list(length=200)
        return [clean_mongo_document(d) for d in docs]

    @staticmethod
    def object_id(value: str) -> ObjectId:
        return ObjectId(value)


class MongoSessionRepository(SessionRepository):
    def __init__(self):
        self.db = MongoManager.db()

    async def store_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> None:
        await self.db["refresh_tokens"].insert_one(
            {
                "user_id": user_id,
                "token_hash": token_hash,
                "expires_at": expires_at,
                "revoked_at": None,
                "created_at": datetime.now(UTC),
            }
        )

    async def revoke_refresh_token(self, token_hash: str) -> None:
        await self.db["refresh_tokens"].update_one(
            {"token_hash": token_hash},
            {"$set": {"revoked_at": datetime.now(UTC)}},
        )

    async def is_refresh_token_active(self, token_hash: str) -> bool:
        now = datetime.now(UTC)
        doc = await self.db["refresh_tokens"].find_one(
            {"token_hash": token_hash, "revoked_at": None, "expires_at": {"$gt": now}}
        )
        return doc is not None

