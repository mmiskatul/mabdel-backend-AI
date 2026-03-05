from datetime import UTC, datetime
from typing import Any

from app.domain.models import NormalizedInboundMessage, NormalizedSendResult, OutboundMessageRequest


def parse_stub_inbound(platform, payload: dict[str, Any]) -> list[NormalizedInboundMessage]:
    messages = payload.get("messages") or []
    normalized: list[NormalizedInboundMessage] = []
    for item in messages:
        normalized.append(
            NormalizedInboundMessage(
                platform=platform,
                external_account_id=str(item.get("account_id", "stub_account")),
                external_thread_id=str(item.get("thread_id", "stub_thread")),
                external_contact_id=str(item.get("from_id", "stub_contact")),
                contact_name=str(item.get("from_name", "Unknown Contact")),
                text=str(item.get("text", "")),
                timestamp=item.get("timestamp") or datetime.now(UTC),
                platform_message_id=str(item.get("message_id", f"stub_{datetime.now(UTC).timestamp()}")),
                attachments=item.get("attachments", []),
            )
        )
    return normalized


def send_stub(
    outbound: OutboundMessageRequest,
    target: dict[str, Any],
) -> NormalizedSendResult:
    _ = outbound, target
    return NormalizedSendResult(
        success=True,
        platform_message_id=f"sent_{int(datetime.now(UTC).timestamp())}",
        raw_response={"provider": "stub"},
    )

