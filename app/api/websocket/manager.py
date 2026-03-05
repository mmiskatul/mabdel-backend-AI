from collections import defaultdict
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[user_id].append(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        if websocket in self.connections[user_id]:
            self.connections[user_id].remove(websocket)

    async def emit(self, user_id: str, event: str, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self.connections.get(user_id, []):
            try:
                await ws.send_json({"event": event, "data": payload})
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)


ws_manager = WebSocketManager()

