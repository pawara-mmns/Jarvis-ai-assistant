import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum
import logging
from typing import Any, Literal

from google import genai
from google.genai import types
from websockets.exceptions import ConnectionClosedOK

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
ClientFactory = Callable[[str], Any]
AudioCommand = tuple[Literal["audio", "end"], bytes | None]


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

    def __init__(
        self,
        config: GeminiLiveConfig,
        emit: EmitEvent,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self.config = config
        self.emit = emit
        self.lifecycle = LiveSessionStateMachine()
        self._client_factory = client_factory or (lambda api_key: genai.Client(api_key=api_key))
        self._client: Any = None
        self._session: Any = None
        self._session_open = False
        self._supervisor: asyncio.Task[None] | None = None
        self._ready = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._audio_queue: asyncio.Queue[AudioCommand] = asyncio.Queue(maxsize=256)
        self._closing = False

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

        api_key = self.config.api_key
        assert api_key is not None
        self._closing = False
        self._session_open = False
        self._ready.clear()
        self._stop_event.clear()
        self._discard_queued_audio()
        self.lifecycle.transition(LiveSessionState.CONNECTING)
        await self.emit({"type": "session.state", "state": "connecting"})
        self._client = self._client_factory(api_key)
        self._supervisor = asyncio.create_task(self._run(), name="gemini-live-session")
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=15)
        except TimeoutError:
            if self.state != LiveSessionState.ERROR:
                await self._stop_supervisor()
                await self._fail("connection_timeout", "Gemini Live connection timed out.", True)
        return self.state in {LiveSessionState.READY, LiveSessionState.ACTIVE}

    async def send_audio(self, pcm16: bytes) -> bool:
        if not pcm16 or not self._can_send():
            return False
        queued = self._queue_audio(("audio", pcm16))
        if queued and self.state == LiveSessionState.READY:
            self.lifecycle.transition(LiveSessionState.ACTIVE)
        return queued

    async def end_audio(self) -> bool:
        if not self._can_send():
            return False
        return self._queue_audio(("end", None))

    async def close(self) -> None:
        if self.state == LiveSessionState.DISCONNECTED:
            return
        self._closing = True
        self._session_open = False
        if self.state != LiveSessionState.CLOSING:
            self.lifecycle.transition(LiveSessionState.CLOSING)
        self._stop_event.set()
        self._discard_queued_audio()
        await self._stop_supervisor()
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
                        self._session_open = True
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
                        await self._run_connected_session(session)
                    self._session_open = False
                    self._session = None
                    if self._closing:
                        return
                    raise ConnectionError("Gemini Live session closed unexpectedly")
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    self._session_open = False
                    self._session = None
                    self._discard_queued_audio()
                    if self._closing:
                        if not isinstance(error, ConnectionClosedOK):
                            logger.debug("Gemini session closed during shutdown", exc_info=True)
                        return
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
            self._session_open = False
            self._session = None

    async def _run_connected_session(self, session: Any) -> None:
        receiver = asyncio.create_task(self._receive_loop(session), name="gemini-live-receiver")
        sender = asyncio.create_task(self._send_loop(session), name="gemini-live-sender")
        stopper = asyncio.create_task(self._stop_event.wait(), name="gemini-live-stopper")
        tasks = {receiver, sender, stopper}
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            if stopper in done:
                return
            for task in done:
                if task is stopper:
                    continue
                error = task.exception()
                if error is not None:
                    raise error
                raise ConnectionError("Gemini Live worker stopped unexpectedly")
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _receive_loop(self, session: Any) -> None:
        while not self._stop_event.is_set() and session is self._session:
            received_response = False
            async for response in session.receive():
                received_response = True
                events = translate_live_event(response)
                for event in events:
                    await self.emit(event)
                if any(event["type"] == "turn.complete" for event in events):
                    if self.state == LiveSessionState.ACTIVE:
                        self.lifecycle.transition(LiveSessionState.READY)
            if self._stop_event.is_set():
                return
            if not received_response:
                raise ConnectionError("Gemini Live receive stream ended unexpectedly")
            # receive() completes after one model turn; yield and wait for the next turn.
            await asyncio.sleep(0)

    async def _send_loop(self, session: Any) -> None:
        while not self._stop_event.is_set() and session is self._session:
            command, audio = await self._audio_queue.get()
            try:
                if command == "audio" and audio:
                    await session.send_realtime_input(
                        audio=types.Blob(data=audio, mime_type=INPUT_AUDIO_MIME_TYPE)
                    )
                elif command == "end":
                    await session.send_realtime_input(audio_stream_end=True)
            finally:
                self._audio_queue.task_done()

    def _can_send(self) -> bool:
        return bool(
            not self._closing
            and self._session_open
            and self._session is not None
            and self._supervisor is not None
            and not self._supervisor.done()
            and self.state in {LiveSessionState.READY, LiveSessionState.ACTIVE}
        )

    def _queue_audio(self, command: AudioCommand) -> bool:
        try:
            self._audio_queue.put_nowait(command)
            return True
        except asyncio.QueueFull:
            logger.warning("Gemini audio queue is full; dropping an input chunk")
            return False

    def _discard_queued_audio(self) -> None:
        while True:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.task_done()
            except asyncio.QueueEmpty:
                return

    async def _stop_supervisor(self) -> None:
        task = self._supervisor
        self._supervisor = None
        if task is None or task is asyncio.current_task():
            return
        try:
            await asyncio.wait_for(task, timeout=2)
        except TimeoutError:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

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
