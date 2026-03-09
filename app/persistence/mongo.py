from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.shared.config import get_settings


class MongoManager:
    _client: AsyncIOMotorClient | None = None

    @classmethod
    def client(cls) -> AsyncIOMotorClient:
        if cls._client is None:
            settings = get_settings()
            cls._client = AsyncIOMotorClient(settings.mongodb_uri, tz_aware=True)
        return cls._client

    @classmethod
    def db(cls) -> AsyncIOMotorDatabase:
        settings = get_settings()
        return cls.client()[settings.mongodb_db_name]

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            cls._client.close()
            cls._client = None


def clean_mongo_document(document: dict[str, Any]) -> dict[str, Any]:
    if "_id" in document:
        document["id"] = str(document.pop("_id"))
    return document
