"""Socket.IO server for real-time feed updates."""
import socketio
import logging

logger = logging.getLogger("live_hive")

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


async def emit_new_post(post_data: dict, author_id: str):
    """Broadcast a NEW_POST event to all connected clients."""
    await sio.emit("NEW_POST", {
        "post": post_data,
        "author_id": author_id,
    })
