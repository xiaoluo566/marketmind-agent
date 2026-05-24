from fastapi import APIRouter, Request, status

from app.api.schemas.tasks import TaskCreateRequest
from app.core.responses import success_response
from app.tasks.service import accept_task_request

router = APIRouter()


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
def create_task(payload: TaskCreateRequest, request: Request) -> dict:
    accepted_task = accept_task_request(payload=payload, trace_id=request.state.trace_id)
    return success_response(
        data=accepted_task.model_dump(),
        message="accepted",
        trace_id=request.state.trace_id,
    )
