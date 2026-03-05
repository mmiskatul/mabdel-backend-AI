from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.websocket.manager import ws_manager
from app.shared.security import decode_token

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    payload = decode_token(token)
    user_id = str(payload["sub"])
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, websocket)

