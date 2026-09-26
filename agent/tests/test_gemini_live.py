import asyncio
import base64
from types import SimpleNamespace

import pytest

from agent.ai.gemini_config import GEMINI_LIVE_MODEL, GeminiLiveConfig, SYSTEM_INSTRUCTION
from agent.ai.gemini_events import translate_live_event
from agent.ai.live_messages import AudioChunk, parse_client_message
from agent.ai.live_session import GeminiLiveService, LiveSessionState, LiveSessionStateMachine
from agent.core.config import settings
from agent.main import app


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
def test_websocket_reports_missing_key_without_crashing_backend() -> None:
    from fastapi.testclient import TestClient

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
