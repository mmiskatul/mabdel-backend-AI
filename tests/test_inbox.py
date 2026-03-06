import pytest
from datetime import UTC, datetime

from app.application.services.agent_service import AgentService
from app.application.services.inbox_service import InboxService
from app.infrastructure.adapters.factory import AdapterFactory


@pytest.mark.asyncio
async def test_create_and_send_message(fake_repo):
    service = InboxService(fake_repo, AdapterFactory())
    conv_id = await fake_repo.insert_one(
        "conversations",
        {
            "user_id": "u1",
            "platform": "whatsapp",
            "integration_account_id": None,
            "participants": [],
            "external_thread_id": "t1",
            "last_message_at": datetime.now(UTC),
            "unread_count": 0,
            "tags": [],
            "status": "open",
            "automation_mode": "manual",
            "last_auto_reply_at": None,
        },
    )
    created = await service.queue_outbound_message("u1", conv_id, "hello", [], False)
    assert created["status"] == "queued"


@pytest.mark.asyncio
async def test_sent_message_creates_followup_payload(fake_repo, fake_ws):
    inbox = InboxService(fake_repo, AdapterFactory())
    agent = AgentService(fake_repo)
    conv_id = await fake_repo.insert_one(
        "conversations",
        {
            "user_id": "u1",
            "platform": "whatsapp",
            "integration_account_id": None,
            "participants": [],
            "external_thread_id": "t1",
            "last_message_at": datetime.now(UTC),
            "unread_count": 0,
            "tags": [],
            "status": "open",
            "automation_mode": "manual",
            "last_auto_reply_at": None,
        },
    )
    await fake_repo.insert_one(
        "messages",
        {
            "user_id": "u1",
            "platform": "whatsapp",
            "integration_account_id": None,
            "conversation_id": conv_id,
            "direction": "inbound",
            "sender": {"external_id": "c1", "display_name": "Client"},
            "text": "Can we meet tomorrow?",
            "attachments": [],
            "timestamp": datetime.now(UTC),
            "status": "received",
            "platform_message_id": "pm_1",
            "raw_event_id": "re_1",
            "ai_meta": {"generated_by_ai": False, "confidence": 1.0, "requires_human_review": False},
        },
    )
    created = await inbox.queue_outbound_message("u1", conv_id, "Yes, let's do it.", [], True)
    result = await inbox.process_outbound_message(created["id"], fake_ws)
    assert result["status"] == "sent"

    followup = await agent.post_send_followup("u1", conv_id, created["id"])
    assert "summary" in followup
    assert "suggested_reply" in followup
    assert await fake_repo.count("internal_messages", {"kind": "ai_followup"}) == 1
