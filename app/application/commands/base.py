from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    def __init__(self, user_id: str, payload: dict[str, Any]):
        self.user_id = user_id
        self.payload = payload

    @abstractmethod
    async def execute(self, services: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

