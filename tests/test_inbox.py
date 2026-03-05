import pytest
from datetime import UTC, datetime

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

