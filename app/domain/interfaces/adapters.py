from abc import ABC, abstractmethod
from typing import Any

from app.domain.models import NormalizedInboundMessage, NormalizedSendResult, OutboundMessageRequest


class PlatformAdapter(ABC):
    @abstractmethod
    async def parse_webhook_event(self, payload: dict[str, Any]) -> list[NormalizedInboundMessage]:
        raise NotImplementedError

    @abstractmethod
    async def send_message(
        self,
        outbound: OutboundMessageRequest,
        token: str | None,
        target: dict[str, Any],
    ) -> NormalizedSendResult:
        raise NotImplementedError

