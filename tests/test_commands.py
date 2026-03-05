import pytest

from app.application.services.command_service import CommandService


class StubInbox:
    async def queue_outbound_message(self, user_id, conversation_id, text, attachments, send_as_ai=False):
        _ = user_id, conversation_id, text, attachments, send_as_ai
        return {"id": "m1", "status": "queued"}


class StubDocuments:
    async def cancel_invoice(self, user_id, document_id):
        _ = user_id, document_id
        return {"id": document_id, "status": "cancelled"}

    async def patch_invoice(self, user_id, document_id, patch):
        _ = user_id, patch
        return {"id": document_id}


class StubAgent:
    async def conversation_summary(self, user_id, conversation_id):
        _ = user_id, conversation_id
        class Summary:
            def model_dump(self):
                return {"summary": "ok"}

        return Summary()


@pytest.mark.asyncio
async def test_command_history_and_rerun(fake_repo, fake_queue):
    service = CommandService(
        fake_repo,
        {"queue": fake_queue, "inbox": StubInbox(), "documents": StubDocuments(), "agent": StubAgent()},
    )
    draft = await service.interpret("u1", "send message", {"conversation_id": "c1", "text": "hello"})
    result = await service.execute("u1", draft["execute_token"])
    assert result["run_id"]

    history = await service.history("u1")
    assert len(history) >= 1

