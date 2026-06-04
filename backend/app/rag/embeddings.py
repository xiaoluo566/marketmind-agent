from __future__ import annotations

import math
import re
from hashlib import blake2b
from typing import Protocol


class EmbeddingProvider(Protocol):
    dimensions: int
    model_name: str

    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


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


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]{1,2}", text.lower())
    return [word for word in words if word.strip()]
