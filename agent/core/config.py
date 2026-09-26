from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    agent_host: Literal["127.0.0.1"] = Field(
        default="127.0.0.1", validation_alias="JARVIS_AGENT_HOST"
    )
    agent_port: int = Field(
        default=8765, ge=1024, le=65535, validation_alias="JARVIS_AGENT_PORT"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", validation_alias="JARVIS_LOG_LEVEL"
    )
    gemini_api_key: SecretStr | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    live_bridge_token: str = Field(default="development-local-token-not-for-production", validation_alias="JARVIS_LIVE_TOKEN")


settings = Settings()
