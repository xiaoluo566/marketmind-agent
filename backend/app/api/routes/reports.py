from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import AppError
from app.core.responses import success_response
from app.reporting.evidence import SQLAlchemyEvidenceChainStore
from app.storage.database import get_db_session
from app.storage.models import Report

router = APIRouter()


@router.get("/reports/{report_id}/evidence")
def read_report_evidence(
    report_id: str,
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    report = session.get(Report, report_id)
    if report is None:
        raise AppError(
            code="REPORT_NOT_FOUND",
            message="report not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"report_id": report_id},
        )

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
