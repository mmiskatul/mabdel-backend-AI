from abc import ABC, abstractmethod
from typing import Any


class JobQueue(ABC):
    @abstractmethod
    async def enqueue(self, name: str, payload: dict[str, Any]) -> str:
        raise NotImplementedError

