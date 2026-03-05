from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Repository(ABC):
    @abstractmethod
    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def find_one(self, collection: str, query: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    async def find_many(
        self,
        collection: str,
        query: dict[str, Any],
        limit: int = 50,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def update_one(
        self,
        collection: str,
        query: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count(self, collection: str, query: dict[str, Any]) -> int:
        raise NotImplementedError


class SessionRepository(ABC):
    @abstractmethod
    async def store_refresh_token(self, user_id: str, token_hash: str, expires_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_refresh_token(self, token_hash: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def is_refresh_token_active(self, token_hash: str) -> bool:
        raise NotImplementedError

