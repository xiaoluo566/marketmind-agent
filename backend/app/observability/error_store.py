from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import new_prefixed_id
from app.observability.sanitization import sanitize_details
from app.storage.models import ErrorLog, utc_now


class ErrorLayer(StrEnum):
    API = "api"
    QUEUE = "queue"
    WORKER = "worker"
    AGENT = "agent"
    CRAWLER = "crawler"
    RAG = "rag"
    REPORT = "report"
    DATABASE = "database"


class ErrorLogData(BaseModel):
    error_id: str = Field(default_factory=lambda: new_prefixed_id("err"))
    task_id: str | None = None
    trace_id: str | None = None
    layer: ErrorLayer
    error_code: str
    message: str
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ErrorLogStore(Protocol):
    def append(self, error: ErrorLogData) -> ErrorLogData: ...

    def list_for_task(self, task_id: str) -> list[ErrorLogData]: ...

    def list_for_trace(self, trace_id: str) -> list[ErrorLogData]: ...


class InMemoryErrorLogStore:
    def __init__(self) -> None:
        self._logs: dict[str, ErrorLogData] = {}

    def append(self, error: ErrorLogData) -> ErrorLogData:
        sanitized = error.model_copy(update={"details": sanitize_details(error.details)})
        self._logs[sanitized.error_id] = sanitized
        return sanitized

    def list_for_task(self, task_id: str) -> list[ErrorLogData]:
        return sorted(
            [log for log in self._logs.values() if log.task_id == task_id],
            key=lambda log: (log.created_at, log.error_id),
        )

    def list_for_trace(self, trace_id: str) -> list[ErrorLogData]:
        return sorted(
            [log for log in self._logs.values() if log.trace_id == trace_id],
            key=lambda log: (log.created_at, log.error_id),
        )


class SQLAlchemyErrorLogStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def append(self, error: ErrorLogData) -> ErrorLogData:
        sanitized = error.model_copy(update={"details": sanitize_details(error.details)})
        with self._session_scope() as session:
            with session.begin():
                row = ErrorLog(
                    id=sanitized.error_id,
                    task_id=sanitized.task_id,
                    trace_id=sanitized.trace_id,
                    layer=sanitized.layer.value,
                    error_code=sanitized.error_code,
                    message=sanitized.message,
                    details=sanitized.details,
                    created_at=sanitized.created_at,
                )
                session.add(row)
                session.flush()
                return self._to_data(row)

    def list_for_task(self, task_id: str) -> list[ErrorLogData]:
        with self._session_scope() as session:
            stmt = (
                select(ErrorLog)
                .where(ErrorLog.task_id == task_id)
                .order_by(ErrorLog.created_at.asc(), ErrorLog.id.asc())
            )
            return [self._to_data(row) for row in session.scalars(stmt).all()]

    def list_for_trace(self, trace_id: str) -> list[ErrorLogData]:
        with self._session_scope() as session:
            stmt = (
                select(ErrorLog)
                .where(ErrorLog.trace_id == trace_id)
                .order_by(ErrorLog.created_at.asc(), ErrorLog.id.asc())
            )
            return [self._to_data(row) for row in session.scalars(stmt).all()]

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _to_data(self, row: ErrorLog) -> ErrorLogData:
        return ErrorLogData(
            error_id=row.id,
            task_id=row.task_id,
            trace_id=row.trace_id,
            layer=ErrorLayer(row.layer),
            error_code=row.error_code,
            message=row.message,
            details=dict(row.details or {}),
            created_at=row.created_at,
        )
