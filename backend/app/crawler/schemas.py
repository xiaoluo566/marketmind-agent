from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, Field

from app.crawler.errors import CrawlErrorCode


class CrawlRequest(BaseModel):
    task_id: str | None = None
    url: AnyUrl
    html: str | None = None
    fixture_path: str | None = None
    artifact_dir: str | None = None
    save_html_artifact: bool = False
    capture_screenshot: bool = False
    source_type: Literal["public_url", "html_fixture"] = "public_url"
    timeout_ms: int = Field(default=15_000, ge=1_000, le=60_000)
    user_agent: str | None = None


class CrawlArtifact(BaseModel):
    artifact_type: str
    path: str
    mime_type: str | None = None
    checksum: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrawlReview(BaseModel):
    external_id: str | None = None
    content: str
    rating: float | None = None
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrawlResult(BaseModel):
    url: str
    source_type: str
    title: str | None = None
    price: float | None = None
    rating: float | None = None
    extracted_text: str
    html: str | None = None
    screenshot_path: str | None = None
    artifacts: list[CrawlArtifact] = Field(default_factory=list)
    reviews: list[CrawlReview] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrawlFailure(BaseModel):
    url: str
    source_type: str
    error_code: CrawlErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
