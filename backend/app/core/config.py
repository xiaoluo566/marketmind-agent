from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MarketMind Comment Intelligence API"
    app_version: str = "0.1.0"
    app_env: str = "local"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    backend_cors_origins: list[str] = Field(default_factory=list)
    database_url: str = "postgresql+psycopg://marketmind:marketmind@localhost:5432/marketmind"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    task_status_redis_url: str = "redis://localhost:6379/3"
    task_status_ttl_seconds: int = 86_400
    crawler_artifact_dir: str = "data/artifacts/crawler"
    crawler_save_html_artifact: bool = True
    crawler_capture_screenshot: bool = False
    default_local_user_id: str = "usr_local"
    default_local_user_email: str | None = None
    default_local_project_id: str = "prj_default"
    default_local_project_name: str = "Default Project"
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
