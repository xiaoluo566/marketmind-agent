from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import AnyUrl, BaseModel, Field

from app.agent.tools.registry import ToolRegistry
from app.agent.tools.schemas import ToolArtifact, ToolInvocationContext, ToolSpec
from app.crawler import CrawlErrorCode, CrawlRequest, crawl_product_page
from app.crawler.schemas import CrawlReview


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


def build_default_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(build_crawl_product_tool_spec())
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
