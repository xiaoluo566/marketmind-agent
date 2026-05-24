from app.api.schemas.tasks import TaskAcceptedData, TaskCreateRequest, TaskStatusData
from app.core.ids import new_prefixed_id
from app.storage.statuses import TaskStatus
from app.tasks.dispatcher import QueueUnavailableError, TaskQueueDispatcher
from app.tasks.status_store import TaskStatusStore, utc_now


def submit_task_request(
    payload: TaskCreateRequest,
    trace_id: str,
    status_store: TaskStatusStore,
    dispatcher: TaskQueueDispatcher,
) -> TaskAcceptedData:
    task_id = new_prefixed_id("tsk")
    created_at = utc_now()
    task_status = TaskStatusData(
        task_id=task_id,
        status=TaskStatus.RECEIVED.value,
        trace_id=trace_id,
        target=payload.target,
        mode=payload.mode.value,
        priority=payload.priority.value,
        source_type=payload.source_type.value,
        options=payload.options,
        created_at=created_at,
        updated_at=created_at,
    )
    status_store.create(task_status)

    dispatch_result = dispatcher.enqueue(
        task_id=task_id,
        payload=payload.model_dump(mode="json"),
        trace_id=trace_id,
    )
    queued_task = task_status.model_copy(
        update={
            "status": TaskStatus.QUEUED.value,
            "queue_task_id": dispatch_result.queue_task_id,
            "updated_at": utc_now(),
        }
    )
    status_store.save(queued_task)

    return TaskAcceptedData(
        task_id=task_id,
        status=queued_task.status,
        trace_id=trace_id,
        queue_task_id=dispatch_result.queue_task_id,
    )


def get_task_status(task_id: str, status_store: TaskStatusStore) -> TaskStatusData | None:
    return status_store.get(task_id)


__all__ = [
    "QueueUnavailableError",
    "get_task_status",
    "submit_task_request",
]
