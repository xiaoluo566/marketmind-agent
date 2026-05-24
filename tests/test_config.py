from app.core.config import Settings


def test_model_defaults_match_day2_decisions() -> None:
    settings = Settings()

    assert settings.model_provider == "openai-compatible"
    assert settings.model_name == "gpt-5.4-mini"
    assert settings.report_model_name == "gpt-5.5"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536
