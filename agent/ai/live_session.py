import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum
import logging
from typing import Any

from google import genai
from google.genai import types

from agent.ai.gemini_config import (
    GeminiLiveConfig,
    INPUT_AUDIO_MIME_TYPE,
    INPUT_SAMPLE_RATE,
    OUTPUT_SAMPLE_RATE,
    SYSTEM_INSTRUCTION,
)
from agent.ai.gemini_events import translate_live_event

logger = logging.getLogger(__name__)
EmitEvent = Callable[[dict[str, object]], Awaitable[None]]


class LiveSessionState(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    READY = "ready"
    ACTIVE = "active"
    RECONNECTING = "reconnecting"
    CLOSING = "closing"
    ERROR = "error"


class LiveSessionStateMachine:
    _allowed = {
        LiveSessionState.DISCONNECTED: {LiveSessionState.CONNECTING},
        LiveSessionState.CONNECTING: {
            LiveSessionState.READY,
            LiveSessionState.ERROR,
            LiveSessionState.CLOSING,
        },
        LiveSessionState.READY: {
            LiveSessionState.ACTIVE,
            LiveSessionState.RECONNECTING,
            LiveSessionState.CLOSING,
            LiveSessionState.ERROR,
        },
        LiveSessionState.ACTIVE: {
            LiveSessionState.READY,
            LiveSessionState.RECONNECTING,
            LiveSessionState.CLOSING,
            LiveSessionState.ERROR,
        },
        LiveSessionState.RECONNECTING: {
            LiveSessionState.READY,
            LiveSessionState.ERROR,
            LiveSessionState.CLOSING,
        },
        LiveSessionState.CLOSING: {LiveSessionState.DISCONNECTED},
        LiveSessionState.ERROR: {LiveSessionState.CONNECTING, LiveSessionState.CLOSING},
    }

    def __init__(self) -> None:
        self.state = LiveSessionState.DISCONNECTED

    def transition(self, next_state: LiveSessionState) -> None:
        if next_state == self.state:
            return
        if next_state not in self._allowed[self.state]:
            raise ValueError(f"invalid live session transition: {self.state} -> {next_state}")
        self.state = next_state


class GeminiLiveService:
    _reconnect_delays = (0.5, 1.5, 3.0)

    def __init__(self, config: GeminiLiveConfig, emit: EmitEvent) -> None:
        self.config = config
        self.emit = emit
        self.lifecycle = LiveSessionStateMachine()
        self._client: genai.Client | None = None
        self._session: Any = None
        self._supervisor: asyncio.Task[None] | None = None
        self._ready = asyncio.Event()
        self._closing = False
        self._send_lock = asyncio.Lock()

    @property
    def state(self) -> LiveSessionState:
        return self.lifecycle.state

    async def start(self) -> bool:
        if self.state in {
            LiveSessionState.CONNECTING,
            LiveSessionState.READY,
            LiveSessionState.ACTIVE,
            LiveSessionState.RECONNECTING,
        }:
            return True
        if not self.config.is_configured:
            self.lifecycle.transition(LiveSessionState.CONNECTING)
            self.lifecycle.transition(LiveSessionState.ERROR)
            await self.emit(
                {
                    "type": "session.error",
                    "code": "not_configured",
                    "message": "Set GEMINI_API_KEY in .env",
                    "reconnectable": False,
                }
            )
            return False

        self._closing = False
        self._ready.clear()
        self.lifecycle.transition(LiveSessionState.CONNECTING)
        await self.emit({"type": "session.state", "state": "connecting"})
        self._client = genai.Client(api_key=self.config.api_key)
        self._supervisor = asyncio.create_task(self._run(), name="gemini-live-session")
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=15)
        except TimeoutError:
            if self.state != LiveSessionState.ERROR:
                if self._supervisor:
                    self._supervisor.cancel()
                    await asyncio.gather(self._supervisor, return_exceptions=True)
                await self._fail("connection_timeout", "Gemini Live connection timed out.", True)
        return self.state in {LiveSessionState.READY, LiveSessionState.ACTIVE}

    async def send_audio(self, pcm16: bytes) -> None:
        if not pcm16 or self._session is None or self.state not in {
            LiveSessionState.READY,
            LiveSessionState.ACTIVE,
        }:
            return
        if self.state == LiveSessionState.READY:
            self.lifecycle.transition(LiveSessionState.ACTIVE)
        async with self._send_lock:
            await self._session.send_realtime_input(
                audio=types.Blob(data=pcm16, mime_type=INPUT_AUDIO_MIME_TYPE)
            )

    async def end_audio(self) -> None:
        if self._session is None or self.state not in {
            LiveSessionState.READY,
            LiveSessionState.ACTIVE,
        }:
            return
        async with self._send_lock:
            await self._session.send_realtime_input(audio_stream_end=True)

    async def close(self) -> None:
        if self.state == LiveSessionState.DISCONNECTED:
            return
        self._closing = True
        if self.state != LiveSessionState.CLOSING:
            self.lifecycle.transition(LiveSessionState.CLOSING)
        task = self._supervisor
        self._supervisor = None
        if task and task is not asyncio.current_task():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        self._session = None
        await self._close_client()
        self.lifecycle.transition(LiveSessionState.DISCONNECTED)
        await self.emit({"type": "session.closed"})

    async def _run(self) -> None:
        attempts = 0
        try:
            while not self._closing:
                try:
                    assert self._client is not None
                    config = types.LiveConnectConfig(
                        response_modalities=["AUDIO"],
                        input_audio_transcription=types.AudioTranscriptionConfig(),
                        output_audio_transcription=types.AudioTranscriptionConfig(),
                        system_instruction=SYSTEM_INSTRUCTION,
                    )
                    async with self._client.aio.live.connect(
                        model=self.config.model, config=config
                    ) as session:
                        self._session = session
                        self.lifecycle.transition(LiveSessionState.READY)
                        self._ready.set()
                        await self.emit(
                            {
                                "type": "session.ready",
                                "model": self.config.model,
                                "inputSampleRate": INPUT_SAMPLE_RATE,
                                "outputSampleRate": OUTPUT_SAMPLE_RATE,
                            }
                        )
                        attempts = 0
                        async for response in session.receive():
                            events = translate_live_event(response)
                            for event in events:
                                await self.emit(event)
                            if any(
                                event["type"] == "turn.complete"
                                for event in events
                            ) and self.state == LiveSessionState.ACTIVE:
                                self.lifecycle.transition(LiveSessionState.READY)
                    if not self._closing:
                        raise ConnectionError("Gemini Live session closed unexpectedly")
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self._session = None
                    code, message, reconnectable = self._safe_error(error)
                    if not reconnectable or attempts >= self.config.max_reconnect_attempts:
                        await self._fail(code, message, reconnectable)
                        return
                    if self.state in {LiveSessionState.READY, LiveSessionState.ACTIVE}:
                        self.lifecycle.transition(LiveSessionState.RECONNECTING)
                    attempts += 1
                    await self.emit(
                        {
                            "type": "session.state",
                            "state": "reconnecting",
                            "attempt": attempts,
                        }
                    )
                    await asyncio.sleep(self._reconnect_delays[attempts - 1])
        except asyncio.CancelledError:
            pass
        finally:
            self._session = None

    async def _fail(self, code: str, message: str, reconnectable: bool) -> None:
        if self.state != LiveSessionState.ERROR:
            self.lifecycle.transition(LiveSessionState.ERROR)
        self._ready.set()
        logger.warning("Gemini Live session failed: %s", code)
        await self.emit(
            {
                "type": "session.error",
                "code": code,
                "message": message,
                "reconnectable": reconnectable,
            }
        )
        await self._close_client()

    @staticmethod
    def _safe_error(error: Exception) -> tuple[str, str, bool]:
        detail = str(error).lower()
        if any(term in detail for term in ("api key", "unauthenticated", "permission denied", "401")):
            return "authentication_failed", "Gemini authentication failed. Check GEMINI_API_KEY.", False
        return "connection_failed", "Gemini Live connection was lost.", True

    async def _close_client(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        try:
            await client.aio.aclose()
        except Exception:
            logger.debug("Gemini client cleanup failed", exc_info=True)
