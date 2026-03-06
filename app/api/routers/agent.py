from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.api.schemas import SmartFlowBody
from app.api.service_factory import get_agent_service
from app.application.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/conversations/{conversation_id}/summary")
async def summary(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.conversation_summary(user_id, conversation_id)


@router.post("/conversations/{conversation_id}/draft_reply")
async def draft_reply(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.draft_reply(user_id, conversation_id)


@router.post("/inbound/{message_id}/decide")
async def decide_inbound(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.decide_inbound(message_id, user_id=user_id)


@router.post("/smartflow/ask")
async def smartflow_ask(
    body: SmartFlowBody,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.smartflow_ask(user_id, body.text)
