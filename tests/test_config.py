from app.core.config import Settings


def test_model_defaults_match_day2_decisions() -> None:
    settings = Settings()

    assert settings.model_provider == "openai-compatible"
    assert settings.model_name == "gpt-5.4-mini"
    assert settings.report_model_name == "gpt-5.5"
    assert settings.embedding_provider == "fake"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536
    assert settings.embedding_api_base_url == "https://api.openai.com/v1"
    assert settings.embedding_api_key is None
    assert settings.embedding_provider_fallback_enabled is False


def test_async_task_defaults_match_day5_queue_plan() -> None:
    settings = Settings()

    assert settings.celery_broker_url == "redis://localhost:6379/1"
    assert settings.celery_result_backend == "redis://localhost:6379/2"
    assert settings.task_status_redis_url == "redis://localhost:6379/3"
    assert settings.task_status_ttl_seconds == 86_400
