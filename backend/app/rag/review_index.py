from __future__ import annotations

import math
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.rag.embeddings import EmbeddingProvider
from app.rag.text import split_review_text
from app.storage.models import Review, ReviewChunk, Task


@dataclass(frozen=True, slots=True)
class ReviewChunkIndexResult:
    task_id: str
    review_count: int
    chunk_count: int
    embedding_model: str
    embedding_dimensions: int


@dataclass(frozen=True, slots=True)
class ReviewSearchResult:
    chunk_id: str
    review_id: str
    review_external_id: str | None
    content: str
    similarity: float
    source_url: str | None
    rating: float | None
    metadata: dict


class SQLAlchemyReviewChunkStore:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        embedding_model: str = "text-embedding-3-small",
        embedding_dimensions: int = 1536,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_model = embedding_model
        self._embedding_dimensions = embedding_dimensions

    def index_task_reviews(
        self,
        *,
        task_id: str,
        embedding_provider: EmbeddingProvider,
        max_chars: int = 500,
    ) -> ReviewChunkIndexResult:
        self._ensure_embedding_contract(embedding_provider)
        with self._session_scope() as session:
            with session.begin():
                if session.get(Task, task_id) is None:
                    raise ValueError(f"task {task_id} does not exist")

                reviews = session.scalars(
                    select(Review).where(Review.task_id == task_id).order_by(Review.id.asc())
                ).all()
                chunk_specs = []
                for review in reviews:
                    chunks = split_review_text(review.content, max_chars=max_chars)
                    for chunk in chunks:
                        chunk_specs.append((review, chunk.chunk_index, chunk.content))

                embeddings = embedding_provider.embed_texts(
                    [content for _, _, content in chunk_specs]
                )
                for (review, chunk_index, content), embedding in zip(
                    chunk_specs,
                    embeddings,
                    strict=True,
                ):
                    self._upsert_chunk(
                        session,
                        review=review,
                        chunk_index=chunk_index,
                        content=content,
                        embedding=embedding,
                    )
                session.flush()
                return ReviewChunkIndexResult(
                    task_id=task_id,
                    review_count=len(reviews),
                    chunk_count=len(chunk_specs),
                    embedding_model=self._embedding_model,
                    embedding_dimensions=self._embedding_dimensions,
                )

    def search_similar_reviews(
        self,
        *,
        task_id: str,
        query: str,
        embedding_provider: EmbeddingProvider,
        top_k: int = 5,
    ) -> list[ReviewSearchResult]:
        self._ensure_embedding_contract(embedding_provider)
        query_embedding = embedding_provider.embed_texts([query])[0]
        with self._session_scope() as session:
            rows = session.execute(
                select(ReviewChunk, Review)
                .join(Review, Review.id == ReviewChunk.review_id)
                .where(
                    ReviewChunk.task_id == task_id,
                    ReviewChunk.embedding_model == self._embedding_model,
                    ReviewChunk.embedding_dimensions == self._embedding_dimensions,
                )
            ).all()
            scored = [
                (
                    _cosine_similarity(query_embedding, _coerce_embedding(chunk.embedding)),
                    chunk,
                    review,
                )
                for chunk, review in rows
                if chunk.embedding is not None
            ]
            scored.sort(key=lambda item: item[0], reverse=True)
            return [
                ReviewSearchResult(
                    chunk_id=chunk.id,
                    review_id=review.id,
                    review_external_id=review.external_id,
                    content=chunk.content,
                    similarity=similarity,
                    source_url=review.source_url,
                    rating=review.rating,
                    metadata=dict(chunk.metadata_ or {}),
                )
                for similarity, chunk, review in scored[: max(0, top_k)]
            ]

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _upsert_chunk(
        self,
        session: Session,
        *,
        review: Review,
        chunk_index: int,
        content: str,
        embedding: list[float],
    ) -> ReviewChunk:
        stmt = select(ReviewChunk).where(
            ReviewChunk.review_id == review.id,
            ReviewChunk.task_id == review.task_id,
            ReviewChunk.chunk_index == chunk_index,
            ReviewChunk.embedding_model == self._embedding_model,
            ReviewChunk.embedding_dimensions == self._embedding_dimensions,
        )
        chunk = session.scalars(stmt).first()
        metadata = {
            "review_external_id": review.external_id,
            "source_url": review.source_url,
            "rating": review.rating,
            "source_type": review.source_type,
        }
        if chunk is None:
            chunk = ReviewChunk(
                review_id=review.id,
                task_id=review.task_id,
                chunk_index=chunk_index,
                content=content,
                embedding=embedding,
                embedding_model=self._embedding_model,
                embedding_dimensions=self._embedding_dimensions,
                metadata_=metadata,
            )
            session.add(chunk)
            session.flush()
            return chunk

        chunk.content = content
        chunk.embedding = embedding
        chunk.metadata_ = metadata
        return chunk

    def _ensure_embedding_contract(self, embedding_provider: EmbeddingProvider) -> None:
        if embedding_provider.dimensions != self._embedding_dimensions:
            raise ValueError(
                "embedding dimensions mismatch: "
                f"store={self._embedding_dimensions}, provider={embedding_provider.dimensions}"
            )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    similarity = numerator / (left_norm * right_norm)
    return max(0.0, min(1.0, similarity))


def _coerce_embedding(value) -> list[float]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return [float(item) for item in value.tolist()]
    return [float(item) for item in value]
