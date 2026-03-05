import pytest
from datetime import UTC, datetime

from app.application.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_agent_draft_reply(fake_repo):
    service = AgentService(fake_repo)
    conv_id = await fake_repo.insert_one(
        "conversations",
        {"user_id": "u1", "automation_mode": "suggest", "last_auto_reply_at": None},
    )
    await fake_repo.insert_one(
        "messages",
        {
            "user_id": "u1",
            "conversation_id": conv_id,
            "text": "Can you send pricing?",
            "timestamp": datetime.now(UTC),
        },
    )
    draft = await service.draft_reply("u1", conv_id)
    assert draft.reply_text
    assert draft.requires_human_review is True

