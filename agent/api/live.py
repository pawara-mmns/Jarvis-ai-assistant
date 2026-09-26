import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from agent.ai.gemini_config import GeminiLiveConfig
from agent.ai.live_messages import AudioChunk, AudioEnd, SessionStart, SessionStop, parse_client_message
from agent.ai.live_session import GeminiLiveService
from agent.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["live"])


@router.websocket("/ws/live")
async def live_voice(websocket: WebSocket) -> None:
    await websocket.accept()
    send_lock = asyncio.Lock()

    async def emit(event: dict[str, object]) -> None:
        async with send_lock:
            await websocket.send_json(event)

    service = GeminiLiveService(
        GeminiLiveConfig(api_key=settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None),
        emit,
    )
    await emit({"type": "session.connected"})
    authenticated = False

    try:
        while True:
            raw_message = await websocket.receive_json()
            try:
                message = parse_client_message(raw_message)
            except ValidationError:
                await emit(
                    {
                        "type": "session.error",
                        "code": "invalid_message",
                        "message": "The local live message was invalid.",
                        "reconnectable": False,
                    }
                )
                continue

            if isinstance(message, SessionStart):
                if message.bridge_token != settings.live_bridge_token:
                    await emit(
                        {
                            "type": "session.error",
                            "code": "unauthorized",
                            "message": "The local live connection was not authorized.",
                            "reconnectable": False,
                        }
                    )
                    await websocket.close(code=1008)
                    return
                authenticated = True
                await service.start()
            elif not authenticated:
                await emit(
                    {
                        "type": "session.error",
                        "code": "session_not_started",
                        "message": "Start the AI session before sending audio.",
                        "reconnectable": False,
                    }
                )
            elif isinstance(message, AudioChunk):
                await service.send_audio(message.audio_bytes())
            elif isinstance(message, AudioEnd):
                await service.end_audio()
            elif isinstance(message, SessionStop):
                await service.close()
                await websocket.close(code=1000)
                return
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Local Live WebSocket failed")
        try:
            await emit(
                {
                    "type": "session.error",
                    "code": "local_transport_failed",
                    "message": "The local AI audio connection failed.",
                    "reconnectable": True,
                }
            )
        except Exception:
            pass
    finally:
        await service.close()
