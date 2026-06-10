from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.responses import success_response
from app.observability.error_store import ErrorLogData, ErrorLogStore
from app.observability.llmops_summary import summarize_llmops
from app.storage.database import get_db_session

router = APIRouter(prefix="/observability")


class ErrorLogItem(BaseModel):
    error_id: str
    task_id: str | None
    trace_id: str | None
    layer: str
    error_code: str
    message: str
    details: dict = Field(default_factory=dict)
    created_at: str


class ErrorLogListData(BaseModel):
    items: list[ErrorLogItem]
    limit: int
    total: int


@router.get("/errors")
def list_error_logs(
    request: Request,
    trace_id: Annotated[str | None, Query()] = None,
    task_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict:
    if not trace_id and not task_id:
        raise AppError(
            code="OBSERVABILITY_FILTER_REQUIRED",
            message="trace_id or task_id is required",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={},
        )

    store = _error_store_from_request(request)
    all_logs = _query_error_logs(store=store, trace_id=trace_id, task_id=task_id)
    logs = all_logs[:limit]
    data = ErrorLogListData(
        items=[_to_item(log) for log in logs],
        limit=limit,
        total=len(all_logs),
    )
    return success_response(
        data=data.model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.get("/llmops-summary")
def read_llmops_summary(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    return success_response(
        data=summarize_llmops(session),
        message="ok",
        trace_id=request.state.trace_id,
    )


def _query_error_logs(
    *,
    store: ErrorLogStore,
    trace_id: str | None,
    task_id: str | None,
) -> list[ErrorLogData]:
    if trace_id:
        logs = store.list_for_trace(trace_id)
        if task_id:
            return [log for log in logs if log.task_id == task_id]
        return logs
    if task_id:
        return store.list_for_task(task_id)
    return []


def _to_item(log: ErrorLogData) -> ErrorLogItem:
    return ErrorLogItem(
        error_id=log.error_id,
        task_id=log.task_id,
        trace_id=log.trace_id,
        layer=log.layer.value,
        error_code=log.error_code,
        message=log.message,
        details=log.details,
        created_at=log.created_at.isoformat(),
    )


def _error_store_from_request(request: Request) -> ErrorLogStore:
    store = getattr(request.app.state, "error_log_store", None)
    if store is not None:
        return store
    return request.app.state.error_log_store_factory()
