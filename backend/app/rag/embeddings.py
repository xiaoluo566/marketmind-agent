from __future__ import annotations

import json
import math
import re
import socket
from hashlib import blake2b
from typing import Any, Protocol
from urllib import error, request

from app.core.config import Settings

EMBEDDING_PROVIDER_UNCONFIGURED = "EMBEDDING_PROVIDER_UNCONFIGURED"
EMBEDDING_PROVIDER_TIMEOUT = "EMBEDDING_PROVIDER_TIMEOUT"
EMBEDDING_PROVIDER_RATE_LIMITED = "EMBEDDING_PROVIDER_RATE_LIMITED"
EMBEDDING_PROVIDER_BAD_RESPONSE = "EMBEDDING_PROVIDER_BAD_RESPONSE"


class EmbeddingProvider(Protocol):
    dimensions: int
    model_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingProviderError(RuntimeError):
    def __init__(self, *, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class DeterministicEmbeddingProvider:
    def __init__(
        self,
        *,
        dimensions: int = 1536,
        model_name: str = "fake-deterministic-embedding",
    ) -> None:
        self.dimensions = dimensions
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = _tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        api_base_url: str,
        api_key: str | None,
        model_name: str,
        dimensions: int,
        timeout_seconds: float = 15.0,
        client: Any | None = None,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.dimensions = dimensions
        self.timeout_seconds = timeout_seconds
        self._client = client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self.api_key:
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_UNCONFIGURED,
                message="embedding provider api key is not configured",
            )

        payload = {
            "model": self.model_name,
            "input": texts,
            "dimensions": self.dimensions,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = self._request_embeddings(payload=payload, headers=headers)
        return self._parse_embeddings_response(response, expected_count=len(texts))

    def _request_embeddings(self, *, payload: dict[str, Any], headers: dict[str, str]) -> dict:
        try:
            if self._client is not None:
                return self._client(payload, headers, self.timeout_seconds)
            return _post_json(
                url=f"{self.api_base_url}/embeddings",
                payload=payload,
                headers=headers,
                timeout_seconds=self.timeout_seconds,
            )
        except EmbeddingProviderError:
            raise
        except TimeoutError as exc:
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_TIMEOUT,
                message="embedding provider request timed out",
            ) from exc
        except error.HTTPError as exc:
            if exc.code == 429:
                raise EmbeddingProviderError(
                    code=EMBEDDING_PROVIDER_RATE_LIMITED,
                    message="embedding provider rate limited the request",
                ) from exc
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                message="embedding provider returned an HTTP error",
                details={"status_code": exc.code},
            ) from exc
        except error.URLError as exc:
            if isinstance(exc.reason, TimeoutError | socket.timeout):
                raise EmbeddingProviderError(
                    code=EMBEDDING_PROVIDER_TIMEOUT,
                    message="embedding provider request timed out",
                ) from exc
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                message="embedding provider request failed",
                details={"reason": str(exc.reason)},
            ) from exc
        except Exception as exc:
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                message="embedding provider request failed",
            ) from exc

    def _parse_embeddings_response(
        self,
        response: dict,
        *,
        expected_count: int,
    ) -> list[list[float]]:
        data = response.get("data")
        if not isinstance(data, list) or len(data) != expected_count:
            raise EmbeddingProviderError(
                code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                message="embedding provider response count does not match input count",
            )

        embeddings: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict) or "embedding" not in item:
                raise EmbeddingProviderError(
                    code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                    message="embedding provider response item is malformed",
                )
            raw_embedding = item["embedding"]
            if not isinstance(raw_embedding, list) or len(raw_embedding) != self.dimensions:
                raise EmbeddingProviderError(
                    code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                    message="embedding provider response dimension does not match settings",
                )
            try:
                embeddings.append([float(value) for value in raw_embedding])
            except (TypeError, ValueError) as exc:
                raise EmbeddingProviderError(
                    code=EMBEDDING_PROVIDER_BAD_RESPONSE,
                    message="embedding provider response contains non-numeric values",
                ) from exc
        return embeddings


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "fake":
        return DeterministicEmbeddingProvider(
            dimensions=settings.embedding_dimensions,
            model_name=settings.embedding_model,
        )
    if settings.embedding_provider != "openai-compatible":
        raise EmbeddingProviderError(
            code=EMBEDDING_PROVIDER_UNCONFIGURED,
            message=f"unsupported embedding provider: {settings.embedding_provider}",
        )
    if not settings.embedding_api_key:
        if settings.embedding_provider_fallback_enabled:
            return DeterministicEmbeddingProvider(
                dimensions=settings.embedding_dimensions,
                model_name=f"{settings.embedding_model}:deterministic-fallback",
            )
        raise EmbeddingProviderError(
            code=EMBEDDING_PROVIDER_UNCONFIGURED,
            message="embedding provider api key is not configured",
        )
    return OpenAICompatibleEmbeddingProvider(
        api_base_url=settings.embedding_api_base_url,
        api_key=settings.embedding_api_key,
        model_name=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        timeout_seconds=settings.embedding_request_timeout_seconds,
    )


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]{1,2}", text.lower())
    return [word for word in words if word.strip()]


def _post_json(
    *,
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: float,
) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise EmbeddingProviderError(
            code=EMBEDDING_PROVIDER_BAD_RESPONSE,
            message="embedding provider response root is not an object",
        )
    return parsed
