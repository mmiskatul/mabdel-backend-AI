from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id, get_queue
from app.api.schemas import ForwardBody, OutboundMessageBody, TagsBody
from app.api.service_factory import get_inbox_service
from app.application.services.inbox_service import InboxService

router = APIRouter(tags=["conversations"])


@router.get("/conversations")
async def list_conversations(
    filter: str = Query(default="all"),
    platform: str | None = None,
    q: str | None = None,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    return await service.list_conversations(user_id, filter_value=filter, platform=platform, q=q, limit=limit)


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    return await service.get_conversation(user_id, conversation_id)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    limit: int = 50,
    before: str | None = None,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    _ = before
    return await service.get_messages(user_id, conversation_id, limit=limit)


@router.post("/conversations/{conversation_id}/mark_read")
async def mark_read(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    await service.mark_read(user_id, conversation_id)
    return {"ok": True}


@router.post("/conversations/{conversation_id}/tags")
async def update_tags(
    conversation_id: str,
    body: TagsBody,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    await service.update_tags(user_id, conversation_id, body.tags)
    return {"ok": True}


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: OutboundMessageBody,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
    queue=Depends(get_queue),
):
    created = await service.queue_outbound_message(
        user_id,
        conversation_id,
        body.text,
        body.attachments,
        send_as_ai=body.send_as_ai,
    )
    await queue.enqueue("send_message", {"message_id": created["id"]})
    return created


@router.post("/messages/{message_id}/forward")
async def forward_message(
    message_id: str,
    body: ForwardBody,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    return await service.forward_message(
        user_id,
        message_id,
        to_conversation_id=body.to_conversation_id,
        target_platform=body.target_platform,
        text_override=body.text,
    )


@router.get("/search/messages")
async def search_messages(
    q: str,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    return await service.search_messages(user_id, q)


@router.get("/search/conversations")
async def search_conversations(
    q: str,
    user_id: str = Depends(get_current_user_id),
    service: InboxService = Depends(get_inbox_service),
):
    return await service.search_conversations(user_id, q)

