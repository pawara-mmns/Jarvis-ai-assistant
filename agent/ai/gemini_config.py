from dataclasses import dataclass


GEMINI_LIVE_MODEL = "gemini-3.8-live"
INPUT_AUDIO_MIME_TYPE = "audio/pcm;rate=16000"
INPUT_SAMPLE_RATE = 16_000
OUTPUT_AUDIO_MIME_TYPE = "audio/pcm;rate=24000"
OUTPUT_SAMPLE_RATE = 24_000

SYSTEM_INSTRUCTION = (
    "You are JARVIS, a helpful desktop AI assistant. Keep spoken replies concise. "
    "Understand Sinhala, English, and natural mixed speech; reply in the user's current "
    "language. Desktop controls are not enabled yet, so say so clearly if asked to control "
    "the computer. Do not repeat requests unnecessarily."
)


@dataclass(frozen=True)
class GeminiLiveConfig:
    api_key: str | None
    model: str = GEMINI_LIVE_MODEL
    max_reconnect_attempts: int = 3

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

