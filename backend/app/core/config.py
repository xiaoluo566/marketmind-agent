from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketMind Agent API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    backend_cors_origins: list[str] = Field(default_factory=list)
    database_url: str = "postgresql+psycopg://marketmind:marketmind@localhost:5432/marketmind"
    redis_url: str = "redis://localhost:6379/0"
    model_provider: str = "openai-compatible"
    model_name: str = "gpt-5.4-mini"
    report_model_name: str = "gpt-5.5"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_backend_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []


@lru_cache
def get_settings() -> Settings:
    return Settings()
