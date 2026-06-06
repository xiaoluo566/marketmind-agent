from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.schemas.reports import (
    ReportDetailData,
    ReportListData,
    ReportSectionData,
    ReportSummaryData,
)
from app.core.exceptions import AppError
from app.core.responses import success_response
from app.reporting.evidence import SQLAlchemyEvidenceChainStore
from app.storage.database import get_db_session
from app.storage.models import Report, Task

router = APIRouter()


@router.get("/reports")
def list_reports(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
    status_filter: Annotated[list[str] | None, Query(alias="status")] = None,
    task_status: Annotated[list[str] | None, Query(alias="task_status")] = None,
    created_after: Annotated[datetime | None, Query()] = None,
    created_before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    filters = _report_filters(
        statuses=status_filter,
        task_statuses=task_status,
        created_after=created_after,
        created_before=created_before,
    )
    total = session.scalar(
        select(func.count()).select_from(Report).join(Task).where(*filters)
    ) or 0
    stmt = (
        select(Report, Task.status)
        .join(Task)
        .where(*filters)
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        _to_report_summary(report, task_status=task_status_value)
        for report, task_status_value in session.execute(stmt).all()
    ]

    return success_response(
        data=ReportListData(
            items=items,
            limit=limit,
            offset=offset,
            total=int(total),
        ).model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.get("/reports/{report_id}")
def read_report(
    report_id: str,
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    report = session.get(Report, report_id)
    if report is None:
        raise _report_not_found(report_id)

    task = session.get(Task, report.task_id)
    return success_response(
        data=_to_report_detail(report, task_status=task.status if task else None).model_dump(
            mode="json"
        ),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.get("/reports/{report_id}/evidence")
def read_report_evidence(
    report_id: str,
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    report = session.get(Report, report_id)
    if report is None:
        raise _report_not_found(report_id)

    store = SQLAlchemyEvidenceChainStore(
        session_factory=sessionmaker(
            bind=session.get_bind(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    )
    chain = store.resolve(task_id=report.task_id, evidence_refs=list(report.evidence_refs or []))
    return success_response(
        data={
            "report_id": report.id,
            **chain.model_dump(mode="json"),
        },
        message="ok",
        trace_id=request.state.trace_id,
    )


def _report_not_found(report_id: str) -> AppError:
    return AppError(
        code="REPORT_NOT_FOUND",
        message="report not found",
        status_code=status.HTTP_404_NOT_FOUND,
        details={"report_id": report_id},
    )


def _report_filters(
    *,
    statuses: list[str] | None,
    task_statuses: list[str] | None,
    created_after: datetime | None,
    created_before: datetime | None,
):
    filters = []
    if statuses:
        filters.append(Report.status.in_(statuses))
    if task_statuses:
        filters.append(Task.status.in_(task_statuses))
    if created_after:
        filters.append(Report.created_at >= created_after)
    if created_before:
        filters.append(Report.created_at <= created_before)
    return filters


def _to_report_summary(report: Report, *, task_status: str | None) -> ReportSummaryData:
    risk_score = _risk_score(report)
    return ReportSummaryData(
        report_id=report.id,
        task_id=report.task_id,
        task_status=task_status,
        title=report.title,
        summary=report.summary or "",
        status=report.status,
        risk_level=_risk_level(risk_score),
        risk_score=risk_score,
        evidence_count=len(report.evidence_refs or []),
        created_at=report.created_at,
        updated_at=report.updated_at,
        schema_version=report.schema_version,
    )


def _to_report_detail(report: Report, *, task_status: str | None) -> ReportDetailData:
    summary = _to_report_summary(report, task_status=task_status)
    return ReportDetailData(
        **summary.model_dump(),
        sections=_report_sections(report),
        content_markdown=report.content_markdown or "",
        evidence_refs=list(report.evidence_refs or []),
    )


def _report_sections(report: Report) -> list[ReportSectionData]:
    content_json = dict(report.content_json or {})
    sections = content_json.get("sections")
    if not isinstance(sections, list):
        return []
    return [_section_to_data(section) for section in sections if isinstance(section, dict)]


def _section_to_data(section: dict) -> ReportSectionData:
    return ReportSectionData(
        title=str(section.get("heading") or section.get("title") or "Untitled section"),
        body=str(section.get("claim") or section.get("body") or ""),
        evidence_ids=[
            str(evidence_ref)
            for evidence_ref in section.get("evidence_refs", section.get("evidence_ids", []))
        ],
    )


def _risk_score(report: Report) -> int:
    scorecard = _scorecard(report)
    score = scorecard.get("overall_risk_score")
    if isinstance(score, int):
        return max(0, min(100, score))
    return 0


def _risk_level(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _scorecard(report: Report) -> dict:
    content_json = dict(report.content_json or {})
    metadata = content_json.get("metadata", {})
    if not isinstance(metadata, dict):
        return {}
    scorecard = metadata.get("analysis_scorecard", {})
    return scorecard if isinstance(scorecard, dict) else {}
