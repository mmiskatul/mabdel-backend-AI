from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.agent.models import RealtimeAgentEvent, RealtimeUserMessage
from app.api.deps import get_current_user_id, get_repo, validate_access_token
from app.api.service_factory import get_agent_service
from app.application.services.agent_service import AgentService
from app.shared.errors import AppError

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/sessions")
async def create_session(
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.create_session(user_id)


@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    service: AgentService = Depends(get_agent_service),
):
    return await service.get_messages(user_id, session_id)


@router.websocket("/ws/{session_id}")
async def agent_realtime_socket(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
):
    try:
        user_id = validate_access_token(token)
    except AppError:
        await websocket.close(code=4401)
        return

    service = AgentService(get_repo())
    if session_id == "new":
        created = await service.create_session(user_id)
        session_id = created.session_id

    await websocket.accept()
    await websocket.send_json(
        RealtimeAgentEvent(type="session_ready", session_id=session_id, detail="connected").model_dump()
    )

    try:
        while True:
            raw_payload = await websocket.receive_json()
            try:
                payload = RealtimeUserMessage.model_validate(raw_payload)
            except ValidationError as exc:
                await websocket.send_json(
                    RealtimeAgentEvent(
                        type="error",
                        session_id=session_id,
                        detail=exc.errors()[0]["msg"],
                    ).model_dump()
                )
                continue

            await websocket.send_json(
                RealtimeAgentEvent(
                    type="agent_status",
                    session_id=session_id,
                    stage="processing",
                ).model_dump()
            )
            try:
                reply = await service.respond(user_id, session_id, payload.text)
            except AppError as exc:
                await websocket.send_json(
                    RealtimeAgentEvent(type="error", session_id=session_id, detail=exc.message).model_dump()
                )
                continue
            await websocket.send_json(
                RealtimeAgentEvent(
                    type="assistant_message",
                    session_id=session_id,
                    text=reply.reply_text,
                ).model_dump()
            )
    except WebSocketDisconnect:
        return
