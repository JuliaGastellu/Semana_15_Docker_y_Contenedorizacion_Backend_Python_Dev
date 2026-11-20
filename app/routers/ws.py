from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from app.database import async_session_factory
from app.models import Post, User
from app.realtime import manager, post_manager
from app.security import decode_token

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/posts/{post_id}")
async def post_notifications(socket: WebSocket, post_id: int, token: str = ""):
    try:
        payload = decode_token(token, "access")
        async with async_session_factory() as db:
            user = await db.get(User, int(payload["sub"]))
            post = await db.get(Post, post_id)
            if user is None or not user.is_active or post is None:
                raise ValueError("No puedo acceder")
            if post.status != "published" and user.role != "admin" and post.author_id != user.id:
                raise ValueError("No puedo acceder")
    except Exception:
        await socket.close(code=1008)
        return
    await post_manager.connect(post_id, socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        post_manager.disconnect(post_id, socket)


@router.get("/client", response_class=FileResponse)
async def client():
    return FileResponse(Path(__file__).resolve().parents[1] / "static/ws_client.html")


@router.websocket("/notifications")
async def notifications(socket: WebSocket, token: str = ""):
    try:
        payload = decode_token(token, "access")
        async with async_session_factory() as db:
            user = await db.get(User, int(payload["sub"]))
            if user is None or not user.is_active:
                raise ValueError("Usuario inválido")
            user_id = user.id
    except Exception:
        await socket.close(code=1008)
        return
    await manager.connect(user_id, socket)
    try:
        while True:
            message = await socket.receive_text()
            if message == "ping":
                await socket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, socket)
