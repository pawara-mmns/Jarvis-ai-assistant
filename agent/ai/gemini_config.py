from dataclasses import dataclass


GEMINI_LIVE_MODEL = "gemini-3.8-live"
INPUT_AUDIO_MIME_TYPE = "audio/pcm;rate=16000"
INPUT_SAMPLE_RATE = 16_000
OUTPUT_AUDIO_MIME_TYPE = "audio/pcm;rate=24000"
OUTPUT_SAMPLE_RATE = 24_000

SYSTEM_INSTRUCTION = (
    "You are JARVIS, a concise desktop assistant. Understand Sinhala, English, and mixed speech; "
    "reply in the user's language. Use desktop tools when needed. Tool results are authoritative: "
    "never claim success early or invent results. If a result is ambiguous, ask which listed "
    "candidate to use, then call the tool with that candidate. Explain failures briefly. SAFE tools "
    "need no permission."
)


@dataclass(frozen=True)
class GeminiLiveConfig:
    api_key: str | None
    model: str = GEMINI_LIVE_MODEL
    max_reconnect_attempts: int = 3

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())
