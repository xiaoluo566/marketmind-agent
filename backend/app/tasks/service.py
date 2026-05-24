from app.api.schemas.tasks import TaskAcceptedData, TaskCreateRequest
from app.core.ids import new_prefixed_id
from app.storage.statuses import TaskStatus


def accept_task_request(payload: TaskCreateRequest, trace_id: str) -> TaskAcceptedData:
    _ = payload
    return TaskAcceptedData(
        task_id=new_prefixed_id("tsk"),
        status=TaskStatus.RECEIVED.value,
        trace_id=trace_id,
    )
