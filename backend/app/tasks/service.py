from app.api.schemas.tasks import (
    TaskAcceptedData,
    TaskCreateRequest,
    TaskEventData,
    TaskEventsData,
    TaskStatusData,
)
from app.core.ids import new_prefixed_id
from app.storage.statuses import TaskStatus
from app.tasks.dispatcher import QueueUnavailableError, TaskQueueDispatcher
from app.tasks.event_store import TaskEventStore
from app.tasks.status_store import TaskStatusStore, utc_now


def submit_task_request(
    payload: TaskCreateRequest,
    trace_id: str,
    status_store: TaskStatusStore,
    event_store: TaskEventStore,
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
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.RECEIVED.value,
            event_type="status",
            message="task received",
            payload={
                "target": payload.target,
                "mode": payload.mode.value,
                "priority": payload.priority.value,
                "source_type": payload.source_type.value,
            },
            trace_id=trace_id,
        )
    )

    try:
        dispatch_result = dispatcher.enqueue(
            task_id=task_id,
            payload=payload.model_dump(mode="json"),
            trace_id=trace_id,
        )
    except QueueUnavailableError as exc:
        failed_task = task_status.model_copy(
            update={
                "status": TaskStatus.FAILED.value,
                "error_code": "QUEUE_UNAVAILABLE",
                "error_message": "task queue is unavailable",
                "updated_at": utc_now(),
            }
        )
        status_store.save(failed_task)
        event_store.append(
            build_task_event(
                task_id=task_id,
                status=TaskStatus.FAILED.value,
                event_type="error",
                message="task queue is unavailable",
                payload={"error_code": "QUEUE_UNAVAILABLE", "reason": str(exc)},
                trace_id=trace_id,
            )
        )
        raise QueueUnavailableError(str(exc)) from exc

    queued_task = task_status.model_copy(
        update={
            "status": TaskStatus.QUEUED.value,
            "queue_task_id": dispatch_result.queue_task_id,
            "updated_at": utc_now(),
        }
    )
    status_store.save(queued_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            event_type="status",
            message="task queued",
            payload={"queue_task_id": dispatch_result.queue_task_id},
            trace_id=trace_id,
        )
    )

    return TaskAcceptedData(
        task_id=task_id,
        status=queued_task.status,
        trace_id=trace_id,
        queue_task_id=dispatch_result.queue_task_id,
    )


def get_task_status(task_id: str, status_store: TaskStatusStore) -> TaskStatusData | None:
    return status_store.get(task_id)


def list_task_events(task_id: str, event_store: TaskEventStore) -> TaskEventsData:
    return TaskEventsData(task_id=task_id, events=event_store.list_for_task(task_id))


def build_task_event(
    task_id: str,
    status: str,
    event_type: str,
    message: str,
    payload: dict,
    trace_id: str | None,
) -> TaskEventData:
    return TaskEventData(
        event_id=new_prefixed_id("evt"),
        task_id=task_id,
        status=status,
        event_type=event_type,
        message=message,
        payload=payload,
        trace_id=trace_id,
        created_at=utc_now(),
    )


__all__ = [
    "QueueUnavailableError",
    "build_task_event",
    "get_task_status",
    "list_task_events",
    "submit_task_request",
]
