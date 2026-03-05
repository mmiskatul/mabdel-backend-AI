from typing import Any

from app.domain.enums import Platform
from app.domain.interfaces.adapters import PlatformAdapter
from app.domain.models import NormalizedInboundMessage, NormalizedSendResult, OutboundMessageRequest
from app.infrastructure.adapters.base_adapter import parse_stub_inbound, send_stub


class SmsAdapter(PlatformAdapter):
    async def parse_webhook_event(self, payload: dict[str, Any]) -> list[NormalizedInboundMessage]:
        return parse_stub_inbound(Platform.sms, payload)

    async def send_message(
        self,
        outbound: OutboundMessageRequest,
        token: str | None,
        target: dict[str, Any],
    ) -> NormalizedSendResult:
        _ = token
        return send_stub(outbound, target)

