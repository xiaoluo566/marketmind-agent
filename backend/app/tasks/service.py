from datetime import datetime

from app.api.schemas.tasks import (
    TaskAcceptedData,
    TaskCreateRequest,
    TaskEventData,
    TaskEventsData,
    TaskListData,
    TaskStatusData,
)
from app.core.ids import new_prefixed_id
from app.storage.statuses import TaskStatus
from app.tasks.dispatcher import QueueUnavailableError, TaskQueueDispatcher
from app.tasks.event_store import TaskEventStore
from app.tasks.recovery import (
    RecoveryDecision,
    build_retry_options,
    build_retry_payload,
    find_resume_checkpoint,
    plan_retry,
    retry_count_from_options,
)
from app.tasks.status_store import TaskStatusStore, utc_now


class TaskRetryError(RuntimeError):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


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
                "finished_at": utc_now(),
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


def retry_task_request(
    *,
    task_id: str,
    trace_id: str,
    status_store: TaskStatusStore,
    event_store: TaskEventStore,
    dispatcher: TaskQueueDispatcher,
    max_attempts: int = 3,
) -> TaskAcceptedData:
    task = status_store.get(task_id)
    if task is None:
        raise TaskRetryError(
            code="TASK_NOT_FOUND",
            message="task not found",
            details={"task_id": task_id},
        )
    if task.status != TaskStatus.FAILED.value:
        raise TaskRetryError(
            code="TASK_NOT_RETRYABLE",
            message="only failed tasks can be retried",
            details={"task_id": task_id, "status": task.status},
        )

    retry_count = retry_count_from_options(task.options)
    retry_plan = plan_retry(
        error_code=task.error_code,
        retry_count=retry_count,
        max_attempts=max_attempts,
    )
    if retry_plan.decision == RecoveryDecision.NOT_RETRYABLE:
        raise TaskRetryError(
            code="TASK_NOT_RETRYABLE",
            message="task failure is not retryable",
            details={
                "task_id": task_id,
                "error_code": task.error_code,
                "reason": retry_plan.reason,
            },
        )
    if retry_plan.decision == RecoveryDecision.LIMIT_REACHED:
        raise TaskRetryError(
            code="TASK_RETRY_LIMIT_REACHED",
            message="task retry limit reached",
            details={
                "task_id": task_id,
                "error_code": task.error_code,
                "retry_count": retry_plan.retry_count,
                "max_attempts": retry_plan.max_attempts,
            },
        )

    existing_events = event_store.list_for_task(task_id)
    checkpoint = find_resume_checkpoint(existing_events)
    recovery_options = build_retry_options(
        task=task,
        plan=retry_plan,
        checkpoint=checkpoint,
    )
    waiting_task = task.model_copy(
        deep=True,
        update={
            "status": TaskStatus.WAITING_RETRY.value,
            "options": recovery_options,
            "updated_at": utc_now(),
        },
    )
    status_store.save(waiting_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.WAITING_RETRY.value,
            event_type="retry",
            message="task waiting retry",
            payload={
                "retry_count": retry_plan.next_retry_count,
                "max_attempts": retry_plan.max_attempts,
                "backoff_seconds": retry_plan.backoff_seconds,
                "last_error_code": task.error_code,
                "resume_from_event_id": checkpoint.event_id,
            },
            trace_id=trace_id,
        )
    )

    retry_payload = build_retry_payload(waiting_task)
    try:
        dispatch_result = dispatcher.enqueue(
            task_id=task_id,
            payload=retry_payload,
            trace_id=trace_id,
        )
    except QueueUnavailableError as exc:
        failed_task = waiting_task.model_copy(
            update={
                "status": TaskStatus.FAILED.value,
                "error_code": "QUEUE_UNAVAILABLE",
                "error_message": "task retry queue is unavailable",
                "finished_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        status_store.save(failed_task)
        event_store.append(
            build_task_event(
                task_id=task_id,
                status=TaskStatus.FAILED.value,
                event_type="retry_error",
                message="task retry queue unavailable",
                payload={"error_code": "QUEUE_UNAVAILABLE", "reason": str(exc)},
                trace_id=trace_id,
            )
        )
        raise

    queued_task = waiting_task.model_copy(
        update={
            "status": TaskStatus.QUEUED.value,
            "queue_task_id": dispatch_result.queue_task_id,
            "error_code": None,
            "error_message": None,
            "finished_at": None,
            "updated_at": utc_now(),
        }
    )
    status_store.save(queued_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            event_type="retry",
            message="task requeued",
            payload={
                "queue_task_id": dispatch_result.queue_task_id,
                "retry_count": retry_plan.next_retry_count,
                "resume_from_event_id": checkpoint.event_id,
            },
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


def list_task_statuses(
    *,
    status_store: TaskStatusStore,
    statuses: list[str] | None,
    created_after: datetime | None,
    created_before: datetime | None,
    limit: int,
    offset: int,
) -> TaskListData:
    items, total = status_store.list(
        statuses=statuses,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset,
    )
    return TaskListData(items=items, limit=limit, offset=offset, total=total)


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
    "TaskRetryError",
    "build_task_event",
    "get_task_status",
    "list_task_events",
    "list_task_statuses",
    "retry_task_request",
    "submit_task_request",
]
