import pytest
from app.core.config import Settings
from app.rag.embeddings import (
    EMBEDDING_PROVIDER_BAD_RESPONSE,
    EMBEDDING_PROVIDER_RATE_LIMITED,
    EMBEDDING_PROVIDER_UNCONFIGURED,
    DeterministicEmbeddingProvider,
    EmbeddingProviderError,
    OpenAICompatibleEmbeddingProvider,
    build_embedding_provider,
)


def test_embedding_settings_default_to_offline_fake_provider() -> None:
    settings = Settings()

    assert settings.embedding_provider == "fake"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536
    assert settings.embedding_api_base_url == "https://api.openai.com/v1"
    assert settings.embedding_api_key is None
    assert settings.embedding_request_timeout_seconds == 15.0
    assert settings.embedding_provider_fallback_enabled is False


def test_build_embedding_provider_uses_deterministic_provider_for_local_default() -> None:
    settings = Settings(embedding_provider="fake", embedding_dimensions=16)

    provider = build_embedding_provider(settings)

    assert isinstance(provider, DeterministicEmbeddingProvider)
    assert provider.dimensions == 16
    assert provider.model_name == "text-embedding-3-small"


def test_openai_compatible_provider_requires_api_key_before_any_request() -> None:
    settings = Settings(embedding_provider="openai-compatible", embedding_api_key=None)

    with pytest.raises(EmbeddingProviderError) as exc_info:
        build_embedding_provider(settings)

    assert exc_info.value.code == EMBEDDING_PROVIDER_UNCONFIGURED


def test_openai_compatible_provider_parses_valid_embedding_response() -> None:
    def fake_client(payload: dict, headers: dict, timeout_seconds: float) -> dict:
        assert payload["model"] == "text-embedding-3-small"
        assert payload["input"] == ["质量差", "物流慢"]
        assert payload["dimensions"] == 3
        assert headers["Authorization"] == "Bearer test-key"
        assert timeout_seconds == 8.0
        return {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]},
            ]
        }

    provider = OpenAICompatibleEmbeddingProvider(
        api_base_url="https://example.test/v1",
        api_key="test-key",
        model_name="text-embedding-3-small",
        dimensions=3,
        timeout_seconds=8.0,
        client=fake_client,
    )

    assert provider.embed_texts(["质量差", "物流慢"]) == [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]


def test_openai_compatible_provider_rejects_bad_response_shape() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        api_base_url="https://example.test/v1",
        api_key="test-key",
        model_name="text-embedding-3-small",
        dimensions=3,
        client=lambda _payload, _headers, _timeout_seconds: {"data": [{"embedding": [0.1]}]},
    )

    with pytest.raises(EmbeddingProviderError) as exc_info:
        provider.embed_texts(["质量差"])

    assert exc_info.value.code == EMBEDDING_PROVIDER_BAD_RESPONSE


def test_openai_compatible_provider_classifies_rate_limit_errors() -> None:
    def fake_client(_payload: dict, _headers: dict, _timeout_seconds: float) -> dict:
        raise EmbeddingProviderError(
            code=EMBEDDING_PROVIDER_RATE_LIMITED,
            message="embedding provider rate limited",
        )

    provider = OpenAICompatibleEmbeddingProvider(
        api_base_url="https://example.test/v1",
        api_key="test-key",
        model_name="text-embedding-3-small",
        dimensions=3,
        client=fake_client,
    )

    with pytest.raises(EmbeddingProviderError) as exc_info:
        provider.embed_texts(["质量差"])

    assert exc_info.value.code == EMBEDDING_PROVIDER_RATE_LIMITED
