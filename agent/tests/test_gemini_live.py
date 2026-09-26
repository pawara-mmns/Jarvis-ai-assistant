import asyncio
import base64
from types import SimpleNamespace
from typing import Any

import pytest
from websockets.exceptions import ConnectionClosedOK
from websockets.frames import Close

from agent.ai.gemini_config import GEMINI_LIVE_MODEL, GeminiLiveConfig, SYSTEM_INSTRUCTION
from agent.ai.gemini_events import translate_live_event
from agent.ai.live_messages import AudioChunk, parse_client_message
from agent.ai.live_session import GeminiLiveService, LiveSessionState, LiveSessionStateMachine
from agent.core.config import settings
from agent.main import app


def turn_complete_response() -> SimpleNamespace:
    return SimpleNamespace(
        server_content=SimpleNamespace(
            input_transcription=None,
            output_transcription=None,
            model_turn=None,
            interrupted=False,
            turn_complete=True,
        ),
        data=None,
    )


def normal_close() -> ConnectionClosedOK:
    close = Close(1000, "OK")
    return ConnectionClosedOK(close, close, True)


class FakeLiveSession:
    def __init__(self) -> None:
        self.responses: asyncio.Queue[list[object] | Exception] = asyncio.Queue()
        self.audio: list[bytes] = []
        self.audio_ends = 0
        self.receive_calls = 0

    async def receive(self):
        self.receive_calls += 1
        result = await self.responses.get()
        if isinstance(result, Exception):
            raise result
        for response in result:
            yield response

    async def send_realtime_input(
        self, *, audio: object | None = None, audio_stream_end: bool | None = None
    ) -> None:
        if audio is not None:
            self.audio.append(audio.data)
        if audio_stream_end:
            self.audio_ends += 1


class FakeLiveConnection:
    def __init__(
        self,
        session: FakeLiveSession,
        exit_error: Exception | None = None,
    ) -> None:
        self.session = session
        self.exit_error = exit_error
        self.exit_count = 0

    async def __aenter__(self) -> FakeLiveSession:
        return self.session

    async def __aexit__(self, *_: object) -> None:
        self.exit_count += 1
        if self.exit_error:
            raise self.exit_error


class FakeLiveApi:
    def __init__(self, connection: FakeLiveConnection) -> None:
        self.connection = connection
        self.connect_calls = 0

    def connect(self, **_: object) -> FakeLiveConnection:
        self.connect_calls += 1
        return self.connection


class FakeAsyncClient:
    def __init__(self, connection: FakeLiveConnection) -> None:
        self.live = FakeLiveApi(connection)
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeClient:
    def __init__(self, connection: FakeLiveConnection) -> None:
        self.aio = FakeAsyncClient(connection)


async def wait_until(predicate: Any, timeout: float = 1) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError("condition was not reached before timeout")
        await asyncio.sleep(0)


def test_gemini_configuration_is_explicit_and_concise() -> None:
    assert GEMINI_LIVE_MODEL == "gemini-3.8-live"
    assert not GeminiLiveConfig(api_key="  ").is_configured
    assert GeminiLiveConfig(api_key="configured").is_configured
    assert len(SYSTEM_INSTRUCTION) < 400
    assert "Sinhala" in SYSTEM_INSTRUCTION and "English" in SYSTEM_INSTRUCTION
    assert "thinking_level" not in SYSTEM_INSTRUCTION


def test_live_message_parses_pcm_and_rejects_odd_samples() -> None:
    message = parse_client_message(
        {
            "type": "audio.chunk",
            "data": base64.b64encode(b"\x01\x02").decode("ascii"),
            "mimeType": "audio/pcm;rate=16000",
        }
    )
    assert isinstance(message, AudioChunk)
    assert message.audio_bytes() == b"\x01\x02"
    with pytest.raises(ValueError):
        parse_client_message(
            {
                "type": "audio.chunk",
                "data": base64.b64encode(b"\x01").decode("ascii"),
                "mimeType": "audio/pcm;rate=16000",
            }
        )


def test_session_state_machine_accepts_only_valid_transitions() -> None:
    lifecycle = LiveSessionStateMachine()
    lifecycle.transition(LiveSessionState.CONNECTING)
    lifecycle.transition(LiveSessionState.READY)
    lifecycle.transition(LiveSessionState.ACTIVE)
    lifecycle.transition(LiveSessionState.READY)
    lifecycle.transition(LiveSessionState.CLOSING)
    lifecycle.transition(LiveSessionState.DISCONNECTED)
    with pytest.raises(ValueError):
        lifecycle.transition(LiveSessionState.ACTIVE)


def test_missing_api_key_is_safe_and_does_not_connect() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        service = GeminiLiveService(GeminiLiveConfig(api_key=None), emit)
        assert not await service.start()
        assert service.state == LiveSessionState.ERROR
        await service.close()

    asyncio.run(run())
    assert events[0] == {
        "type": "session.error",
        "code": "not_configured",
        "message": "Set GEMINI_API_KEY in .env",
        "reconnectable": False,
    }


def test_one_live_connection_handles_multiple_complete_turns() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        session = FakeLiveSession()
        connection = FakeLiveConnection(session)
        client = FakeClient(connection)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test"),
            emit,
            client_factory=lambda _: client,
        )

        assert await service.start()
        assert client.aio.live.connect_calls == 1

        assert await service.send_audio(b"\x01\x02")
        assert await service.end_audio()
        await wait_until(lambda: len(session.audio) == 1 and session.audio_ends == 1)
        await session.responses.put([turn_complete_response()])
        await wait_until(lambda: sum(event["type"] == "turn.complete" for event in events) == 1)
        assert service.state == LiveSessionState.READY
        await wait_until(lambda: session.receive_calls >= 2)

        assert await service.send_audio(b"\x03\x04")
        assert await service.end_audio()
        await wait_until(lambda: len(session.audio) == 2 and session.audio_ends == 2)
        await session.responses.put([turn_complete_response()])
        await wait_until(lambda: sum(event["type"] == "turn.complete" for event in events) == 2)

        assert client.aio.live.connect_calls == 1
        assert connection.exit_count == 0
        assert service.state == LiveSessionState.READY

        await service.close()
        assert connection.exit_count == 1
        assert service.state == LiveSessionState.DISCONNECTED
        assert not any(event["type"] == "session.error" for event in events)

    asyncio.run(run())


def test_explicit_disconnect_suppresses_normal_connection_close() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        session = FakeLiveSession()
        connection = FakeLiveConnection(session, exit_error=normal_close())
        client = FakeClient(connection)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test"),
            emit,
            client_factory=lambda _: client,
        )

        assert await service.start()
        await service.close()

        assert service.state == LiveSessionState.DISCONNECTED
        assert connection.exit_count == 1
        assert client.aio.closed
        assert not any(event["type"] == "session.error" for event in events)

    asyncio.run(run())


def test_unexpected_normal_close_errors_and_blocks_future_audio() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        session = FakeLiveSession()
        connection = FakeLiveConnection(session)
        client = FakeClient(connection)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test", max_reconnect_attempts=0),
            emit,
            client_factory=lambda _: client,
        )

        assert await service.start()
        await session.responses.put(normal_close())
        await wait_until(lambda: service.state == LiveSessionState.ERROR)

        audio_count = len(session.audio)
        assert not await service.send_audio(b"\x05\x06")
        await asyncio.sleep(0)
        assert len(session.audio) == audio_count
        assert any(
            event["type"] == "session.error" and event["code"] == "connection_failed"
            for event in events
        )

        await service.close()
        assert service.state == LiveSessionState.DISCONNECTED

    asyncio.run(run())


def test_sdk_event_translation_emits_transcripts_audio_and_lifecycle() -> None:
    content = SimpleNamespace(
        input_transcription=SimpleNamespace(text="හෙලෝ Jarvis"),
        output_transcription=SimpleNamespace(text="Hello!"),
        model_turn=None,
        interrupted=True,
        turn_complete=True,
    )
    response = SimpleNamespace(server_content=content, data=b"\x00\x01")
    events = translate_live_event(response)
    assert [event["type"] for event in events] == [
        "transcript.input",
        "transcript.output",
        "audio.output",
        "session.interrupted",
        "turn.complete",
    ]
    assert events[2]["mimeType"] == "audio/pcm;rate=24000"


@pytest.mark.filterwarnings("ignore:Using `httpx` with `starlette.testclient` is deprecated")
def test_websocket_reports_missing_key_without_crashing_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    monkeypatch.setattr(settings, "gemini_api_key", None)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/live") as websocket:
            assert websocket.receive_json() == {"type": "session.connected"}
            websocket.send_json(
                {"type": "session.start", "bridgeToken": settings.live_bridge_token}
            )
            assert websocket.receive_json() == {
                "type": "session.error",
                "code": "not_configured",
                "message": "Set GEMINI_API_KEY in .env",
                "reconnectable": False,
            }
