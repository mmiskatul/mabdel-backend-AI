from typing import ClassVar

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class MongoClientManager:
    """Singleton-style Mongo client manager."""

    _client: ClassVar[AsyncIOMotorClient | None] = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.mongodb_uri)
        return cls._client

    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        return cls.get_client()[settings.mongodb_db_name]

    @classmethod
    def close_client(cls) -> None:
        if cls._client is not None:
            cls._client.close()
            cls._client = None

