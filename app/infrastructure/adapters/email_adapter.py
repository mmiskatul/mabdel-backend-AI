from typing import Any

from app.domain.enums import Platform
from app.domain.interfaces.adapters import PlatformAdapter
from app.domain.models import NormalizedInboundMessage, NormalizedSendResult, OutboundMessageRequest
from app.infrastructure.adapters.base_adapter import parse_stub_inbound, send_stub


class EmailAdapter(PlatformAdapter):
    async def parse_webhook_event(self, payload: dict[str, Any]) -> list[NormalizedInboundMessage]:
        source = payload.get("provider", "gmail")
        platform = Platform.email_outlook if source == "outlook" else Platform.email_gmail
        return parse_stub_inbound(platform, payload)

    async def send_message(
        self,
        outbound: OutboundMessageRequest,
        token: str | None,
        target: dict[str, Any],
    ) -> NormalizedSendResult:
        _ = token
        return send_stub(outbound, target)

