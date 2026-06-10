from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.ids import new_prefixed_id
from app.imports.schemas import (
    ParsedReviewRow,
    ReviewImportFormat,
    ReviewImportRequest,
    ReviewImportResult,
    ReviewImportRowError,
)
from app.storage.models import Product, Project, Review, Task, User
from app.storage.statuses import TaskStatus


@dataclass(frozen=True, slots=True)
class _ParsedImport:
    rows: list[ParsedReviewRow]
    errors: list[ReviewImportRowError]


def import_reviews(
    *,
    session: Session,
    payload: ReviewImportRequest,
    trace_id: str,
) -> ReviewImportResult:
    parsed = _parse_payload(payload)
    task = _create_completed_import_task(
        session=session,
        payload=payload,
        trace_id=trace_id,
        parsed=parsed,
    )
    product = Product(
        task_id=task.id,
        title=payload.product_title,
        source_url=payload.source_url,
        raw_payload={"import_format": payload.format.value},
    )
    session.add(product)
    session.flush()

    seen_external_ids: set[str] = set()
    duplicate_count = 0
    imported_external_ids: list[str] = []
    for row in parsed.rows:
        if row.external_id in seen_external_ids:
            duplicate_count += 1
            continue
        seen_external_ids.add(row.external_id)
        review = Review(
            product_id=product.id,
            task_id=task.id,
            external_id=row.external_id,
            source_url=row.source_url or payload.source_url,
            source_type="manual_upload",
            rating=row.rating,
            content=row.content,
            author_hash=_hash_author(row.author),
            published_at=_parse_datetime(row.published_at),
            raw_payload={
                "row_number": row.row_number,
                "product_title": row.product_title,
                "import_format": payload.format.value,
                "source": "manual_upload",
                **row.raw_payload,
            },
        )
        session.add(review)
        imported_external_ids.append(row.external_id)

    session.flush()
    task.options = {
        **dict(task.options or {}),
        "product_id": product.id,
        "imported_count": len(imported_external_ids),
        "duplicate_count": duplicate_count,
        "error_count": len(parsed.errors),
    }
    session.flush()
    return ReviewImportResult(
        format=payload.format,
        task_id=task.id,
        product_id=product.id,
        imported_count=len(imported_external_ids),
        duplicate_count=duplicate_count,
        error_count=len(parsed.errors),
        errors=parsed.errors,
        review_external_ids=imported_external_ids,
    )


def _parse_payload(payload: ReviewImportRequest) -> _ParsedImport:
    if payload.format == ReviewImportFormat.CSV:
        return _parse_csv(payload)
    if payload.format == ReviewImportFormat.JSON:
        return _parse_json(payload)
    raise AppError(
        code="REVIEW_IMPORT_INVALID_FORMAT",
        message="unsupported review import format",
        status_code=400,
        details={"format": payload.format},
    )


def _parse_csv(payload: ReviewImportRequest) -> _ParsedImport:
    reader = csv.DictReader(io.StringIO(payload.content))
    rows: list[ParsedReviewRow] = []
    errors: list[ReviewImportRowError] = []
    for row_number, raw_row in enumerate(reader, start=2):
        normalized = {
            str(key or "").strip(): (value or "").strip()
            for key, value in raw_row.items()
        }
        parsed = _coerce_review_row(
            raw_row=normalized,
            row_number=row_number,
            fallback_product_title=payload.product_title,
            fallback_source_url=payload.source_url,
        )
        if isinstance(parsed, ReviewImportRowError):
            errors.append(parsed)
            continue
        rows.append(parsed)
    return _ParsedImport(rows=rows, errors=errors)


def _parse_json(payload: ReviewImportRequest) -> _ParsedImport:
    try:
        document = json.loads(payload.content)
    except json.JSONDecodeError as exc:
        raise AppError(
            code="REVIEW_IMPORT_INVALID_PAYLOAD",
            message="invalid json review import payload",
            status_code=400,
            details={"reason": str(exc)},
        ) from exc

    if isinstance(document, list):
        reviews = document
        product_title = payload.product_title
        source_url = payload.source_url
    elif isinstance(document, dict):
        reviews = document.get("reviews")
        product_title = str(document.get("product_title") or payload.product_title).strip()
        source_url = str(document.get("source_url") or payload.source_url or "").strip() or None
    else:
        raise AppError(
            code="REVIEW_IMPORT_INVALID_PAYLOAD",
            message="json review import payload must be an object or array",
            status_code=400,
        )

    if not isinstance(reviews, list):
        raise AppError(
            code="REVIEW_IMPORT_INVALID_PAYLOAD",
            message="json review import payload must include a reviews array",
            status_code=400,
        )

    rows: list[ParsedReviewRow] = []
    errors: list[ReviewImportRowError] = []
    for row_number, item in enumerate(reviews, start=1):
        if not isinstance(item, dict):
            errors.append(
                ReviewImportRowError(
                    row_number=row_number,
                    field="review",
                    message="review row must be an object",
                )
            )
            continue
        parsed = _coerce_review_row(
            raw_row=item,
            row_number=row_number,
            fallback_product_title=product_title,
            fallback_source_url=source_url,
        )
        if isinstance(parsed, ReviewImportRowError):
            errors.append(parsed)
            continue
        rows.append(parsed)
    return _ParsedImport(rows=rows, errors=errors)


def _coerce_review_row(
    *,
    raw_row: dict[str, Any],
    row_number: int,
    fallback_product_title: str,
    fallback_source_url: str | None,
) -> ParsedReviewRow | ReviewImportRowError:
    content = _clean(raw_row.get("content") or raw_row.get("review") or raw_row.get("text"))
    if not content:
        return ReviewImportRowError(
            row_number=row_number,
            field="content",
            message="content is required",
        )

    rating = _parse_rating(raw_row.get("rating") or raw_row.get("stars"))
    if isinstance(rating, ReviewImportRowError):
        return rating.model_copy(update={"row_number": row_number})

    author = _clean(raw_row.get("author") or raw_row.get("user") or raw_row.get("buyer"))
    published_at = _clean(raw_row.get("published_at") or raw_row.get("date"))
    source_url = _clean(raw_row.get("source_url") or raw_row.get("url")) or fallback_source_url
    external_id = _external_id(raw_row=raw_row, content=content, rating=rating, author=author)
    return ParsedReviewRow(
        row_number=row_number,
        external_id=external_id,
        product_title=_clean(raw_row.get("product_title")) or fallback_product_title,
        content=content,
        rating=rating,
        author=author,
        published_at=published_at,
        source_url=source_url,
        raw_payload={str(key): value for key, value in raw_row.items()},
    )


def _create_completed_import_task(
    *,
    session: Session,
    payload: ReviewImportRequest,
    trace_id: str,
    parsed: _ParsedImport,
) -> Task:
    settings = get_settings()
    _ensure_default_workspace(session)
    now = datetime.now(UTC)
    task = Task(
        id=new_prefixed_id("tsk"),
        user_id=settings.default_local_user_id,
        project_id=settings.default_local_project_id,
        target=payload.source_url or f"manual_upload://{payload.product_title}",
        mode="review_import",
        status=TaskStatus.COMPLETED.value,
        priority="normal",
        source_type="manual_upload",
        trace_id=trace_id,
        started_at=now,
        finished_at=now,
        options={
            "format": payload.format.value,
            "row_count": len(parsed.rows),
            "error_count": len(parsed.errors),
        },
        created_at=now,
        updated_at=now,
    )
    session.add(task)
    session.flush()
    return task


def _ensure_default_workspace(session: Session) -> None:
    settings = get_settings()
    user = session.get(User, settings.default_local_user_id)
    if user is None:
        session.add(
            User(
                id=settings.default_local_user_id,
                email=settings.default_local_user_email,
                display_name="Local User",
                role="local",
            )
        )
        session.flush()
    project = session.get(Project, settings.default_local_project_id)
    if project is None:
        session.add(
            Project(
                id=settings.default_local_project_id,
                user_id=settings.default_local_user_id,
                name=settings.default_local_project_name,
                description="Local development project",
                settings={},
            )
        )
        session.flush()


def _parse_rating(value: Any) -> float | None | ReviewImportRowError:
    if value is None or value == "":
        return None
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return ReviewImportRowError(
            row_number=0,
            field="rating",
            message="rating must be a number",
        )
    if rating < 0 or rating > 5:
        return ReviewImportRowError(
            row_number=0,
            field="rating",
            message="rating must be between 0 and 5",
        )
    return rating


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _external_id(
    *,
    raw_row: dict[str, Any],
    content: str,
    rating: float | None,
    author: str | None,
) -> str:
    explicit = _clean(raw_row.get("review_id") or raw_row.get("external_id") or raw_row.get("id"))
    if explicit:
        return explicit
    fingerprint = hashlib.sha256(f"{content}|{rating}|{author}".encode()).hexdigest()[:24]
    return f"hash_{fingerprint}"


def _hash_author(author: str | None) -> str | None:
    if not author:
        return None
    return hashlib.sha256(author.encode("utf-8")).hexdigest()


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
