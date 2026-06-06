from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import AnyUrl, BaseModel, Field

from app.agent.tools.registry import ToolRegistry
from app.agent.tools.schemas import ToolArtifact, ToolInvocationContext, ToolSpec
from app.crawler import CrawlErrorCode, CrawlRequest, crawl_product_page
from app.crawler.schemas import CrawlReview
from app.rag.embeddings import EmbeddingProvider
from app.rag.review_index import SQLAlchemyReviewChunkStore


class CrawlProductToolInput(BaseModel):
    url: AnyUrl
    task_id: str | None = None
    source_type: Literal["public_url", "html_fixture"] = "public_url"
    html: str | None = None
    fixture_path: str | None = None
    artifact_dir: str | None = None
    save_html_artifact: bool = True
    capture_screenshot: bool = False
    timeout_ms: int = Field(default=15_000, ge=1_000, le=60_000)
    user_agent: str | None = None


class CrawlProductToolOutput(BaseModel):
    url: str
    source_type: str
    title: str | None = None
    price: float | None = None
    rating: float | None = None
    extracted_text_preview: str
    reviews: list[CrawlReview] = Field(default_factory=list)
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SearchReviewsFilter(BaseModel):
    rating_lte: float | None = Field(default=None, ge=0, le=5)
    rating_gte: float | None = Field(default=None, ge=0, le=5)
    source_type: str | None = None


class ReviewEvidenceChunk(BaseModel):
    chunk_id: str
    review_id: str
    review_external_id: str | None = None
    content: str
    similarity: float = Field(ge=0, le=1)
    source_url: str | None = None
    rating: float | None = None
    evidence_ref: str
    metadata: dict = Field(default_factory=dict)


class SearchReviewsToolInput(BaseModel):
    query: str = Field(min_length=1)
    task_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.0, ge=0, le=1)
    filters: SearchReviewsFilter = Field(default_factory=SearchReviewsFilter)


class SearchReviewsToolOutput(BaseModel):
    query: str
    task_id: str
    results: list[ReviewEvidenceChunk] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    no_results_reason: str | None = None
    metadata: dict = Field(default_factory=dict)


def build_default_tool_registry(
    *,
    review_chunk_store: SQLAlchemyReviewChunkStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(build_crawl_product_tool_spec())
    if review_chunk_store is not None and embedding_provider is not None:
        registry.register(
            build_search_reviews_tool_spec(
                review_chunk_store=review_chunk_store,
                embedding_provider=embedding_provider,
            )
        )
    return registry


def build_crawl_product_tool_spec() -> ToolSpec:
    return ToolSpec(
        name="crawl_product_tool",
        description="Fetch a public product page or fixture HTML and extract product evidence.",
        input_schema=CrawlProductToolInput,
        output_schema=CrawlProductToolOutput,
        handler=run_crawl_product_tool,
        version="v1",
        idempotent=True,
        retryable=True,
        timeout_ms=60_000,
        error_codes=tuple(code.value for code in CrawlErrorCode),
    )


def run_crawl_product_tool(
    payload: CrawlProductToolInput,
    context: ToolInvocationContext,
) -> CrawlProductToolOutput:
    request = CrawlRequest(
        task_id=payload.task_id or context.task_id,
        url=payload.url,
        source_type=payload.source_type,
        html=payload.html,
        fixture_path=payload.fixture_path,
        artifact_dir=payload.artifact_dir,
        save_html_artifact=payload.save_html_artifact,
        capture_screenshot=payload.capture_screenshot,
        timeout_ms=payload.timeout_ms,
        user_agent=payload.user_agent,
    )
    result = asyncio.run(crawl_product_page(request))
    return CrawlProductToolOutput(
        url=result.url,
        source_type=result.source_type,
        title=result.title,
        price=result.price,
        rating=result.rating,
        extracted_text_preview=result.extracted_text[:500],
        reviews=result.reviews,
        artifacts=[
            ToolArtifact(
                artifact_type=artifact.artifact_type,
                path=artifact.path,
                mime_type=artifact.mime_type,
                checksum=artifact.checksum,
                metadata=artifact.metadata,
            )
            for artifact in result.artifacts
        ],
        metadata={
            **result.metadata,
            "fetched_at": result.fetched_at.isoformat(),
        },
    )


def build_search_reviews_tool_spec(
    *,
    review_chunk_store: SQLAlchemyReviewChunkStore,
    embedding_provider: EmbeddingProvider,
) -> ToolSpec:
    def handler(
        payload: SearchReviewsToolInput,
        context: ToolInvocationContext,
    ) -> SearchReviewsToolOutput:
        return run_search_reviews_tool(
            payload,
            context,
            review_chunk_store=review_chunk_store,
            embedding_provider=embedding_provider,
        )

    return ToolSpec(
        name="search_reviews_tool",
        description="Search indexed review chunks for evidence related to a product risk query.",
        input_schema=SearchReviewsToolInput,
        output_schema=SearchReviewsToolOutput,
        handler=handler,
        version="v1",
        idempotent=True,
        retryable=False,
        timeout_ms=15_000,
        error_codes=(
            "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD",
            "REVIEW_INDEX_UNAVAILABLE",
        ),
    )


def run_search_reviews_tool(
    payload: SearchReviewsToolInput,
    context: ToolInvocationContext,
    *,
    review_chunk_store: SQLAlchemyReviewChunkStore,
    embedding_provider: EmbeddingProvider,
) -> SearchReviewsToolOutput:
    task_id = payload.task_id or context.task_id
    raw_results = review_chunk_store.search_similar_reviews(
        task_id=task_id,
        query=payload.query,
        embedding_provider=embedding_provider,
        top_k=payload.top_k,
    )
    filtered_results = [
        result
        for result in raw_results
        if result.similarity >= payload.min_similarity
        and _matches_rating_filter(result.rating, payload.filters)
        and _matches_source_type(result.metadata, payload.filters)
    ]
    evidence_chunks = [
        ReviewEvidenceChunk(
            chunk_id=result.chunk_id,
            review_id=result.review_id,
            review_external_id=result.review_external_id,
            content=result.content,
            similarity=result.similarity,
            source_url=result.source_url,
            rating=result.rating,
            evidence_ref=f"chunk:{result.chunk_id}",
            metadata=result.metadata,
        )
        for result in filtered_results
    ]
    evidence_refs = [chunk.evidence_ref for chunk in evidence_chunks]
    no_results_reason = None
    if not evidence_chunks:
        no_results_reason = "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD"

    return SearchReviewsToolOutput(
        query=payload.query,
        task_id=task_id,
        results=evidence_chunks,
        evidence_refs=evidence_refs,
        no_results_reason=no_results_reason,
        metadata={
            "top_k": payload.top_k,
            "min_similarity": payload.min_similarity,
            "embedding_model": embedding_provider.model_name,
            "embedding_dimensions": embedding_provider.dimensions,
            "filters": payload.filters.model_dump(mode="json"),
        },
    )


def _matches_rating_filter(rating: float | None, filters: SearchReviewsFilter) -> bool:
    if filters.rating_lte is not None and (rating is None or rating > filters.rating_lte):
        return False
    if filters.rating_gte is not None and (rating is None or rating < filters.rating_gte):
        return False
    return True


def _matches_source_type(metadata: dict, filters: SearchReviewsFilter) -> bool:
    if filters.source_type is None:
        return True
    return metadata.get("source_type") == filters.source_type
