import base64
import binascii
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator


MAX_AUDIO_CHUNK_BYTES = 64 * 1024


class LiveMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SessionStart(LiveMessage):
    type: Literal["session.start"]
    bridge_token: str = Field(alias="bridgeToken", min_length=32)


class AudioChunk(LiveMessage):
    type: Literal["audio.chunk"]
    data: str
    mime_type: Literal["audio/pcm;rate=16000"] = Field(alias="mimeType")

    @field_validator("data")
    @classmethod
    def validate_audio_data(cls, value: str) -> str:
        try:
            decoded = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("audio data must be valid base64") from error
        if not decoded or len(decoded) > MAX_AUDIO_CHUNK_BYTES:
            raise ValueError("audio chunk size is invalid")
        if len(decoded) % 2:
            raise ValueError("PCM16 audio must contain whole samples")
        return value

    def audio_bytes(self) -> bytes:
        return base64.b64decode(self.data, validate=True)


class AudioEnd(LiveMessage):
    type: Literal["audio.end"]


class SessionStop(LiveMessage):
    type: Literal["session.stop"]


ClientLiveMessage = Annotated[
    SessionStart | AudioChunk | AudioEnd | SessionStop,
    Field(discriminator="type"),
]
client_message_adapter = TypeAdapter(ClientLiveMessage)


def parse_client_message(value: object) -> ClientLiveMessage:
    return client_message_adapter.validate_python(value)

