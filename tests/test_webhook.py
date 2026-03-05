import pytest

from app.application.services.inbox_service import InboxService
from app.application.services.webhook_service import WebhookService
from app.domain.enums import Platform
from app.infrastructure.adapters.factory import AdapterFactory


@pytest.mark.asyncio
async def test_webhook_ingestion_to_raw_event(fake_repo, fake_queue, fake_ws):
    inbox = InboxService(fake_repo, AdapterFactory())
    service = WebhookService(fake_repo, inbox, fake_queue, fake_ws)
    result = await service.receive_webhook(
        Platform.whatsapp,
        {
            "user_id": "u1",
            "messages": [
                {
                    "account_id": "a1",
                    "thread_id": "t1",
                    "from_id": "c1",
                    "from_name": "Client",
                    "text": "Hello",
                    "message_id": "m1",
                }
            ],
        },
        signature=None,
    )
    assert result["accepted"] is True
    assert len(fake_queue.jobs) == 1

