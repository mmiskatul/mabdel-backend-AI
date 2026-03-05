import hashlib
import hmac
from datetime import UTC, datetime

from app.domain.enums import Platform
from app.application.services.inbox_service import InboxService
from app.infrastructure.db.repositories import MongoRepository
from app.shared.config import get_settings
from app.shared.errors import AppError


class WebhookService:
    def __init__(self, repo: MongoRepository, inbox_service: InboxService, queue, ws_manager):
        self.repo = repo
        self.inbox_service = inbox_service
        self.queue = queue
        self.ws_manager = ws_manager

    async def receive_webhook(
        self,
        platform: Platform,
        payload: dict,
        signature: str | None,
    ) -> dict:
        signature_valid = self.verify_signature(payload, signature)
        raw_event_id = await self.repo.insert_one(
            "raw_events",
            {
                "platform": platform.value,
                "integration_account_id": payload.get("integration_account_id"),
                "user_id": payload.get("user_id"),
                "payload": payload,
                "received_at": datetime.now(UTC),
                "signature_valid": signature_valid,
            },
        )
        await self.queue.enqueue("process_inbound", {"raw_event_id": raw_event_id})
        return {"accepted": True, "raw_event_id": raw_event_id, "signature_valid": signature_valid}

    async def process_inbound(self, raw_event_id: str) -> None:
        raw_event = await self.repo.find_one("raw_events", {"_id": self.repo.object_id(raw_event_id)})
        if not raw_event:
            raise AppError("Raw event not found.", 404)

        platform = Platform(raw_event["platform"])
        adapter = self.inbox_service.adapters.get(platform)
        normalized_messages = await adapter.parse_webhook_event(raw_event["payload"])
        user_id = raw_event.get("user_id") or await self._resolve_user_id(raw_event)
        if not user_id:
            return
        for item in normalized_messages:
            message_id = await self.inbox_service.process_normalized_inbound(
                user_id,
                raw_event_id,
                item,
                self.ws_manager,
            )
            await self.queue.enqueue("agent_decide", {"message_id": message_id})
        await self.repo.insert_one(
            "audit_logs",
            {
                "user_id": user_id,
                "action": "process_inbound",
                "entity_type": "raw_event",
                "entity_id": raw_event_id,
                "details": {"messages": len(normalized_messages)},
                "created_at": datetime.now(UTC),
            },
        )

    async def _resolve_user_id(self, raw_event: dict) -> str | None:
        integration_account_id = raw_event.get("integration_account_id")
        if not integration_account_id:
            return None
        account = await self.repo.find_one("integration_accounts", {"_id": self.repo.object_id(integration_account_id)})
        return account["user_id"] if account else None

    @staticmethod
    def verify_signature(payload: dict, signature: str | None) -> bool:
        if signature is None:
            return False
        settings = get_settings()
        digest = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            str(payload).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, digest)
