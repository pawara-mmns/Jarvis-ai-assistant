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
    search_url_template: str = Field(
        default="https://www.google.com/search?q={query}",
        validation_alias="JARVIS_SEARCH_URL_TEMPLATE",
    )
    folder_roots: str = Field(default="", validation_alias="JARVIS_FOLDER_ROOTS")
    folder_index_max_depth: int = Field(
        default=3, ge=1, le=6, validation_alias="JARVIS_FOLDER_INDEX_MAX_DEPTH"
    )
    resolver_refresh_seconds: int = Field(
        default=300, ge=30, le=86_400, validation_alias="JARVIS_RESOLVER_REFRESH_SECONDS"
    )
    user_aliases_path: str = Field(
        default="config/user-aliases.json", validation_alias="JARVIS_USER_ALIASES_PATH"
    )


settings = Settings()
