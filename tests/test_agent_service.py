import pytest

from app.application.services.agent_service import AgentService


@pytest.mark.asyncio
async def test_agent_session_and_reply_flow(fake_repo):
    service = AgentService(fake_repo)

    session = await service.create_session("u1")
    reply = await service.respond("u1", session.session_id, "Hello, can you help me with pricing?")
    messages = await service.get_messages("u1", session.session_id)

    assert reply.session_id == session.session_id
    assert reply.reply_text
    assert len(reply.turns) == 2
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_agent_reply_reuses_history(fake_repo):
    service = AgentService(fake_repo)

    session = await service.create_session("u1")
    await service.respond("u1", session.session_id, "Hello")
    second = await service.respond("u1", session.session_id, "I need an invoice update")

    assert second.reply_text
    assert await fake_repo.count("agent_messages", {"session_id": session.session_id}) == 4
