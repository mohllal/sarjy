"""Agent settings validated from the environment at startup."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Prefer repo-root .env when the worker is started from agent/
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(min_length=1, default="development")

    livekit_url: str = Field(min_length=1)
    livekit_api_key: str = Field(min_length=1)
    livekit_api_secret: str = Field(min_length=1)
    livekit_agent_name: str = Field(min_length=1, default="sarjy")

    backend_api_base_url: str = Field(min_length=1, default="http://localhost:8000")
    conversation_history_limit: int = Field(default=20, ge=1, le=100)

    openweather_api_key: str = Field(min_length=1)

    system_prompt_version: str = Field(min_length=1, default="1.3.0")
    greeting_prompt_version: str = Field(min_length=1, default="1.0.0")


@lru_cache
def get_settings() -> Settings:
    return Settings()
