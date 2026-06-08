from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.schemas.tasks import AgentStepSummaryData, TaskAgentStepsData, TaskCreateRequest
from app.core.exceptions import AppError
from app.core.responses import success_response
from app.storage.agent_stores import AgentStepData, SQLAlchemyAgentRunStore
from app.tasks.dependencies import (
    get_agent_run_store,
    get_task_dispatcher,
    get_task_event_store,
    get_task_status_store,
)
from app.tasks.dispatcher import QueueUnavailableError, TaskQueueDispatcher
from app.tasks.event_store import TaskEventStore, TaskEventStoreUnavailableError
from app.tasks.service import (
    TaskRetryError,
    get_task_status,
    list_task_events,
    list_task_statuses,
    retry_task_request,
    submit_task_request,
)
from app.tasks.status_store import TaskStatusStore, TaskStatusStoreUnavailableError

router = APIRouter()


@router.get("/tasks")
def list_tasks(
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    status_filter: Annotated[list[str] | None, Query(alias="status")] = None,
    created_after: Annotated[datetime | None, Query()] = None,
    created_before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    try:
        task_list = list_task_statuses(
            status_store=status_store,
            statuses=status_filter,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            offset=offset,
        )
    except TaskStatusStoreUnavailableError as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task status store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc

    return success_response(
        data=task_list.model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
def create_task(
    payload: TaskCreateRequest,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    event_store: Annotated[TaskEventStore, Depends(get_task_event_store)],
    dispatcher: Annotated[TaskQueueDispatcher, Depends(get_task_dispatcher)],
) -> dict:
    try:
        accepted_task = submit_task_request(
            payload=payload,
            trace_id=request.state.trace_id,
            status_store=status_store,
            event_store=event_store,
            dispatcher=dispatcher,
        )
    except (QueueUnavailableError, TaskStatusStoreUnavailableError) as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task queue is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc
    except TaskEventStoreUnavailableError as exc:
        raise AppError(
            code="EVENT_STORE_UNAVAILABLE",
            message="task event store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc

    return success_response(
        data=accepted_task.model_dump(),
        message="accepted",
        trace_id=request.state.trace_id,
    )


@router.get("/tasks/{task_id}")
def read_task(
    task_id: str,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
) -> dict:
    try:
        task_status = get_task_status(task_id=task_id, status_store=status_store)
    except TaskStatusStoreUnavailableError as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task status store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc
    if task_status is None:
        raise AppError(
            code="TASK_NOT_FOUND",
            message="task not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id},
        )

    return success_response(
        data=task_status.model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.post("/tasks/{task_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_task(
    task_id: str,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    event_store: Annotated[TaskEventStore, Depends(get_task_event_store)],
    dispatcher: Annotated[TaskQueueDispatcher, Depends(get_task_dispatcher)],
) -> dict:
    try:
        accepted_task = retry_task_request(
            task_id=task_id,
            trace_id=request.state.trace_id,
            status_store=status_store,
            event_store=event_store,
            dispatcher=dispatcher,
        )
    except TaskRetryError as exc:
        raise AppError(
            code=exc.code,
            message=str(exc),
            status_code=_retry_error_status(exc.code),
            details=exc.details,
        ) from exc
    except QueueUnavailableError as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task retry queue is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc
    except (TaskStatusStoreUnavailableError, TaskEventStoreUnavailableError) as exc:
        raise AppError(
            code="RECOVERY_STORE_UNAVAILABLE",
            message="task recovery store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc

    return success_response(
        data=accepted_task.model_dump(),
        message="accepted",
        trace_id=request.state.trace_id,
    )


@router.get("/tasks/{task_id}/events")
def read_task_events(
    task_id: str,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    event_store: Annotated[TaskEventStore, Depends(get_task_event_store)],
) -> dict:
    try:
        task_status = get_task_status(task_id=task_id, status_store=status_store)
    except TaskStatusStoreUnavailableError as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task status store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc
    if task_status is None:
        raise AppError(
            code="TASK_NOT_FOUND",
            message="task not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id},
        )

    try:
        task_events = list_task_events(task_id=task_id, event_store=event_store)
    except TaskEventStoreUnavailableError as exc:
        raise AppError(
            code="EVENT_STORE_UNAVAILABLE",
            message="task event store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc

    return success_response(
        data=task_events.model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


@router.get("/tasks/{task_id}/steps")
def read_task_steps(
    task_id: str,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    agent_store: Annotated[SQLAlchemyAgentRunStore, Depends(get_agent_run_store)],
) -> dict:
    try:
        task_status = get_task_status(task_id=task_id, status_store=status_store)
    except TaskStatusStoreUnavailableError as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task status store is unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"reason": str(exc)},
        ) from exc
    if task_status is None:
        raise AppError(
            code="TASK_NOT_FOUND",
            message="task not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id},
        )

    steps = [_to_step_summary(step) for step in agent_store.list_steps_for_task(task_id)]
    return success_response(
        data=TaskAgentStepsData(task_id=task_id, steps=steps).model_dump(mode="json"),
        message="ok",
        trace_id=request.state.trace_id,
    )


def _to_step_summary(step: AgentStepData) -> AgentStepSummaryData:
    return AgentStepSummaryData(
        step_id=step.step_id,
        agent_run_id=step.agent_run_id,
        task_id=step.task_id,
        step_index=step.step_index,
        step_type=step.step_type,
        tool_name=step.tool_name,
        status=step.status,
        duration_ms=_duration_ms(step),
        input_summary=_input_summary(step),
        observation_summary=_truncate(step.observation),
        error_code=_error_code(step),
    )


def _duration_ms(step: AgentStepData) -> int | None:
    if step.started_at is None or step.finished_at is None:
        return None
    duration = step.finished_at - step.started_at
    return max(0, int(duration.total_seconds() * 1000))


def _input_summary(step: AgentStepData) -> str | None:
    if step.step_type == "thought":
        return "Thought recorded"
    if step.tool_name:
        return f"{step.tool_name} input keys: {', '.join(sorted(step.tool_input.keys())) or '-'}"
    if step.tool_input:
        return f"Input keys: {', '.join(sorted(step.tool_input.keys()))}"
    return None


def _error_code(step: AgentStepData) -> str | None:
    error = step.tool_output.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        if isinstance(code, str):
            return code
    return None


def _truncate(value: str | None, limit: int = 220) -> str | None:
    if not value:
        return None
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3]}..."


def _retry_error_status(code: str) -> int:
    if code == "TASK_NOT_FOUND":
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_409_CONFLICT
