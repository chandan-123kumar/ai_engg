from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.websocket.manager import manager

router = APIRouter()

@router.websocket("/ws/queue")
async def queue_ws(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
