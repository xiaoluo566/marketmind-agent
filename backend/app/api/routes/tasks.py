from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.schemas.tasks import TaskCreateRequest
from app.core.exceptions import AppError
from app.core.responses import success_response
from app.tasks.dependencies import get_task_dispatcher, get_task_status_store
from app.tasks.dispatcher import QueueUnavailableError, TaskQueueDispatcher
from app.tasks.service import get_task_status, submit_task_request
from app.tasks.status_store import TaskStatusStore, TaskStatusStoreUnavailableError

router = APIRouter()


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
def create_task(
    payload: TaskCreateRequest,
    request: Request,
    status_store: Annotated[TaskStatusStore, Depends(get_task_status_store)],
    dispatcher: Annotated[TaskQueueDispatcher, Depends(get_task_dispatcher)],
) -> dict:
    try:
        accepted_task = submit_task_request(
            payload=payload,
            trace_id=request.state.trace_id,
            status_store=status_store,
            dispatcher=dispatcher,
        )
    except (QueueUnavailableError, TaskStatusStoreUnavailableError) as exc:
        raise AppError(
            code="QUEUE_UNAVAILABLE",
            message="task queue is unavailable",
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
