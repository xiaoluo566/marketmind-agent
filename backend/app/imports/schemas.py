from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReviewImportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


class ReviewImportRequest(BaseModel):
    format: ReviewImportFormat
    content: str = Field(min_length=1)
    product_title: str = Field(min_length=1, max_length=240)
    source_url: str | None = Field(default=None, max_length=2048)

    @field_validator("content", "product_title", "source_url")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        return normalized


class ReviewImportRowError(BaseModel):
    row_number: int
    field: str
    message: str


class ReviewImportResult(BaseModel):
    format: ReviewImportFormat
    task_id: str
    product_id: str
    imported_count: int
    duplicate_count: int
    error_count: int
    errors: list[ReviewImportRowError]
    review_external_ids: list[str]


class ParsedReviewRow(BaseModel):
    row_number: int
    external_id: str
    product_title: str
    content: str
    rating: float | None = None
    author: str | None = None
    published_at: str | None = None
    source_url: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

