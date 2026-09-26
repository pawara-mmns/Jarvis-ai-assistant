import base64
from collections.abc import Iterable
from typing import Any

from agent.ai.gemini_config import OUTPUT_AUDIO_MIME_TYPE


def _text(value: object) -> str | None:
    text = getattr(value, "text", None)
    return text if isinstance(text, str) and text else None


def _audio_parts(server_content: object) -> Iterable[tuple[bytes, str]]:
    model_turn = getattr(server_content, "model_turn", None)
    for part in getattr(model_turn, "parts", None) or ():
        inline_data = getattr(part, "inline_data", None)
        data = getattr(inline_data, "data", None)
        if not isinstance(data, bytes) or not data:
            continue
        mime_type = getattr(inline_data, "mime_type", None)
        yield data, mime_type if isinstance(mime_type, str) else OUTPUT_AUDIO_MIME_TYPE


def translate_live_event(response: Any) -> list[dict[str, object]]:
    """Translate SDK responses into the small public localhost protocol."""
    events: list[dict[str, object]] = []
    server_content = getattr(response, "server_content", None)
    if server_content is None:
        return events

    input_text = _text(getattr(server_content, "input_transcription", None))
    if input_text:
        events.append({"type": "transcript.input", "text": input_text, "final": False})

    output_text = _text(getattr(server_content, "output_transcription", None))
    if output_text:
        events.append({"type": "transcript.output", "text": output_text, "final": False})

    response_data = getattr(response, "data", None)
    audio_parts = list(_audio_parts(server_content))
    if isinstance(response_data, bytes) and response_data:
        audio_parts = [(response_data, OUTPUT_AUDIO_MIME_TYPE)]
    for data, mime_type in audio_parts:
        events.append(
            {
                "type": "audio.output",
                "data": base64.b64encode(data).decode("ascii"),
                "mimeType": mime_type,
            }
        )

    if getattr(server_content, "interrupted", False) is True:
        events.append({"type": "session.interrupted"})
    if getattr(server_content, "turn_complete", False) is True:
        events.append({"type": "turn.complete"})
    return events

