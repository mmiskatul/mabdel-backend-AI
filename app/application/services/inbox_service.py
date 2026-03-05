from datetime import UTC, datetime
from typing import Any

from app.domain.enums import MessageDirection, MessageStatus, Platform
from app.domain.models import NormalizedInboundMessage, OutboundMessageRequest
from app.infrastructure.adapters.factory import AdapterFactory
from app.infrastructure.db.repositories import MongoRepository
from app.shared.errors import ForbiddenError, NotFoundError


class InboxService:
    def __init__(self, repo: MongoRepository, adapters: AdapterFactory):
        self.repo = repo
        self.adapters = adapters

    async def list_conversations(
        self,
        user_id: str,
        filter_value: str = "all",
        platform: str | None = None,
        q: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        query: dict[str, Any] = {"user_id": user_id}
        if filter_value == "unread":
            query["unread_count"] = {"$gt": 0}
        if platform:
            query["platform"] = platform
        if q:
            query["$text"] = {"$search": q}
        return await self.repo.find_many("conversations", query, limit=limit, sort=[("last_message_at", -1)])

    async def get_conversation(self, user_id: str, conversation_id: str) -> dict:
        conversation = await self.repo.find_one("conversations", {"_id": self.repo.object_id(conversation_id)})
        if not conversation:
            raise NotFoundError("Conversation not found.")
        if conversation["user_id"] != user_id:
            raise ForbiddenError()
        return conversation

    async def get_messages(self, user_id: str, conversation_id: str, limit: int = 50) -> list[dict]:
        conversation = await self.get_conversation(user_id, conversation_id)
        return await self.repo.find_many(
            "messages",
            {"user_id": user_id, "conversation_id": conversation["id"]},
            limit=limit,
            sort=[("timestamp", -1)],
        )

    async def mark_read(self, user_id: str, conversation_id: str) -> None:
        conversation = await self.get_conversation(user_id, conversation_id)
        await self.repo.update_one(
            "conversations",
            {"_id": self.repo.object_id(conversation["id"])},
            {"$set": {"unread_count": 0}},
        )

    async def update_tags(self, user_id: str, conversation_id: str, tags: list[str]) -> None:
        conversation = await self.get_conversation(user_id, conversation_id)
        await self.repo.update_one(
            "conversations",
            {"_id": self.repo.object_id(conversation["id"])},
            {"$set": {"tags": tags}},
        )

    async def queue_outbound_message(
        self,
        user_id: str,
        conversation_id: str,
        text: str,
        attachments: list[dict],
        send_as_ai: bool = False,
    ) -> dict:
        conversation = await self.get_conversation(user_id, conversation_id)
        message_id = await self.repo.insert_one(
            "messages",
            {
                "user_id": user_id,
                "platform": conversation["platform"],
                "integration_account_id": conversation["integration_account_id"],
                "conversation_id": conversation["id"],
                "direction": MessageDirection.outbound.value,
                "sender": {"external_id": user_id, "display_name": "You"},
                "text": text,
                "attachments": attachments,
                "timestamp": datetime.now(UTC),
                "status": MessageStatus.queued.value,
                "platform_message_id": None,
                "raw_event_id": None,
                "ai_meta": {
                    "generated_by_ai": send_as_ai,
                    "confidence": 0.7 if send_as_ai else 1.0,
                    "requires_human_review": not send_as_ai,
                },
            },
        )
        return {"id": message_id, "status": MessageStatus.queued.value}

    async def process_outbound_message(self, message_id: str, ws_manager) -> None:
        message = await self.repo.find_one("messages", {"_id": self.repo.object_id(message_id)})
        if not message:
            raise NotFoundError("Message not found.")
        conversation = await self.repo.find_one(
            "conversations", {"_id": self.repo.object_id(message["conversation_id"])}
        )
        integration = await self.repo.find_one(
            "integration_accounts", {"_id": self.repo.object_id(conversation["integration_account_id"])}
        )
        token = None
        if integration:
            oauth = await self.repo.find_one(
                "oauth_tokens",
                {"integration_account_id": integration["id"], "user_id": message["user_id"]},
            )
            token = oauth["access_token_enc"] if oauth else None
        adapter = self.adapters.get(Platform(message["platform"]))
        result = await adapter.send_message(
            OutboundMessageRequest(text=message["text"], attachments=message.get("attachments", [])),
            token=token,
            target={"conversation_id": conversation["id"]},
        )

        status = MessageStatus.sent.value if result.success else MessageStatus.failed.value
        await self.repo.update_one(
            "messages",
            {"_id": self.repo.object_id(message["id"])},
            {
                "$set": {
                    "status": status,
                    "platform_message_id": result.platform_message_id,
                }
            },
        )
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": message["user_id"],
                "event_type": "message_sent",
                "ref": {"type": "message", "id": message["id"]},
                "title": "Message sent",
                "subtitle": message["text"][:80],
                "created_at": datetime.now(UTC),
            },
        )
        await self.repo.insert_one(
            "audit_logs",
            {
                "user_id": message["user_id"],
                "action": "send_message",
                "entity_type": "message",
                "entity_id": message["id"],
                "details": {"status": status},
                "created_at": datetime.now(UTC),
            },
        )
        await ws_manager.emit(
            message["user_id"],
            "message.status",
            {"message_id": message["id"], "status": status},
        )

    async def process_normalized_inbound(
        self,
        user_id: str,
        raw_event_id: str,
        item: NormalizedInboundMessage,
        ws_manager,
    ) -> str:
        contact = await self.repo.find_one(
            "contacts",
            {"user_id": user_id, "platform": item.platform.value, "external_contact_id": item.external_contact_id},
        )
        if not contact:
            contact_id = await self.repo.insert_one(
                "contacts",
                {
                    "user_id": user_id,
                    "platform": item.platform.value,
                    "external_contact_id": item.external_contact_id,
                    "display_name": item.contact_name,
                    "avatar_url": None,
                    "metadata": {},
                },
            )
            contact = {"id": contact_id}

        conversation = await self.repo.find_one(
            "conversations",
            {"user_id": user_id, "platform": item.platform.value, "external_thread_id": item.external_thread_id},
        )
        if not conversation:
            conversation_id = await self.repo.insert_one(
                "conversations",
                {
                    "user_id": user_id,
                    "platform": item.platform.value,
                    "integration_account_id": None,
                    "participants": [contact["id"]],
                    "external_thread_id": item.external_thread_id,
                    "last_message_at": item.timestamp,
                    "unread_count": 0,
                    "tags": [],
                    "status": "open",
                    "automation_mode": "suggest",
                    "last_auto_reply_at": None,
                },
            )
            conversation = {"id": conversation_id, "unread_count": 0}

        message_id = await self.repo.insert_one(
            "messages",
            {
                "user_id": user_id,
                "platform": item.platform.value,
                "integration_account_id": None,
                "conversation_id": conversation["id"],
                "direction": MessageDirection.inbound.value,
                "sender": {
                    "external_id": item.external_contact_id,
                    "display_name": item.contact_name,
                    "contact_id": contact["id"],
                },
                "text": item.text,
                "attachments": item.attachments,
                "timestamp": item.timestamp,
                "status": MessageStatus.received.value,
                "platform_message_id": item.platform_message_id,
                "raw_event_id": raw_event_id,
                "ai_meta": {
                    "generated_by_ai": False,
                    "confidence": 1.0,
                    "requires_human_review": False,
                },
            },
        )
        await self.repo.update_one(
            "conversations",
            {"_id": self.repo.object_id(conversation["id"])},
            {
                "$set": {"last_message_at": item.timestamp},
                "$inc": {"unread_count": 1},
            },
        )
        await self.repo.insert_one(
            "activity_events",
            {
                "user_id": user_id,
                "event_type": "message_received",
                "ref": {"type": "message", "id": message_id},
                "title": "Message received",
                "subtitle": item.text[:80],
                "created_at": datetime.now(UTC),
            },
        )
        await ws_manager.emit(user_id, "message.new", {"message_id": message_id, "conversation_id": conversation["id"]})
        return message_id

    async def forward_message(
        self,
        user_id: str,
        message_id: str,
        to_conversation_id: str | None,
        target_platform: str | None,
        text_override: str | None = None,
    ) -> dict:
        message = await self.repo.find_one("messages", {"_id": self.repo.object_id(message_id)})
        if not message or message["user_id"] != user_id:
            raise NotFoundError("Message not found.")
        if to_conversation_id:
            return await self.queue_outbound_message(
                user_id=user_id,
                conversation_id=to_conversation_id,
                text=text_override or message["text"],
                attachments=message.get("attachments", []),
            )
        if target_platform:
            created_id = await self.repo.insert_one(
                "messages",
                {
                    "user_id": user_id,
                    "platform": target_platform,
                    "integration_account_id": None,
                    "conversation_id": None,
                    "direction": "outbound",
                    "sender": {"external_id": user_id, "display_name": "You"},
                    "text": text_override or message["text"],
                    "attachments": message.get("attachments", []),
                    "timestamp": datetime.now(UTC),
                    "status": "queued",
                    "platform_message_id": None,
                    "raw_event_id": None,
                },
            )
            return {"id": created_id, "status": "queued"}
        raise NotFoundError("Forward target is required.")

    async def search_messages(self, user_id: str, query: str, limit: int = 20) -> list[dict]:
        return await self.repo.find_many(
            "messages",
            {"user_id": user_id, "$text": {"$search": query}},
            limit=limit,
            sort=[("timestamp", -1)],
        )

    async def search_conversations(self, user_id: str, query: str, limit: int = 20) -> list[dict]:
        return await self.repo.find_many(
            "conversations",
            {"user_id": user_id, "$text": {"$search": query}},
            limit=limit,
            sort=[("last_message_at", -1)],
        )
