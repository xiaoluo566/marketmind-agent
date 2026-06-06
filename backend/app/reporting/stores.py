from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.reporting.schemas import StructuredReport
from app.storage.models import Report, Task


@dataclass(frozen=True, slots=True)
class ReportRecord:
    report_id: str
    task_id: str
    title: str
    status: str
    summary: str
    content_markdown: str
    evidence_refs: list[str]
    schema_version: str


class SQLAlchemyReportStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save_report(self, report: StructuredReport) -> ReportRecord:
        with self._session_scope() as session:
            with session.begin():
                self._ensure_task_exists(session, report.task_id)
                row = Report(
                    task_id=report.task_id,
                    title=report.title,
                    status=report.status,
                    summary=report.summary,
                    content_markdown=report.to_markdown(),
                    content_json=report.model_dump(mode="json"),
                    evidence_refs=list(report.evidence_refs),
                    schema_version=report.schema_version,
                )
                session.add(row)
                session.flush()
                return self._to_record(row)

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _ensure_task_exists(self, session: Session, task_id: str) -> None:
        if session.get(Task, task_id) is None:
            raise ValueError(f"task {task_id} does not exist")

    def _to_record(self, row: Report) -> ReportRecord:
        return ReportRecord(
            report_id=row.id,
            task_id=row.task_id,
            title=row.title,
            status=row.status,
            summary=row.summary or "",
            content_markdown=row.content_markdown or "",
            evidence_refs=list(row.evidence_refs or []),
            schema_version=row.schema_version,
        )
