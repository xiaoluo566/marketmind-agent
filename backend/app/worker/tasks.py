from app.api.schemas.tasks import TaskStatusData
from app.storage.statuses import TaskStatus
from app.tasks.dependencies import get_task_event_store, get_task_status_store
from app.tasks.event_store import TaskEventStore
from app.tasks.service import build_task_event
from app.tasks.status_store import TaskStatusStore, utc_now
from app.worker.celery_app import celery_app


@celery_app.task(name="marketmind.tasks.process_research_task")
def process_research_task(task_id: str, payload: dict, trace_id: str) -> dict:
    return run_research_task(
        task_id=task_id,
        payload=payload,
        trace_id=trace_id,
        status_store=get_task_status_store(),
        event_store=get_task_event_store(),
    )


def run_research_task(
    task_id: str,
    payload: dict,
    trace_id: str,
    status_store: TaskStatusStore,
    event_store: TaskEventStore,
) -> dict:
    current_task = status_store.get(task_id)
    if current_task is None:
        current_task = TaskStatusData(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            trace_id=trace_id,
            target=str(payload.get("target", "")),
            mode=str(payload.get("mode", "")),
            priority=str(payload.get("priority", "")),
            source_type=str(payload.get("source_type", "")),
            options=dict(payload.get("options") or {}),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    running_task = current_task.model_copy(
        update={
            "status": TaskStatus.RUNNING.value,
            "started_at": current_task.started_at or utc_now(),
            "updated_at": utc_now(),
        }
    )
    status_store.save(running_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            event_type="status",
            message="task running",
            payload={},
            trace_id=trace_id,
        )
    )

    completed_task = running_task.model_copy(
        update={
            "status": TaskStatus.COMPLETED.value,
            "finished_at": utc_now(),
            "updated_at": utc_now(),
        }
    )
    status_store.save(completed_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.COMPLETED.value,
            event_type="status",
            message="task completed",
            payload={"target": completed_task.target},
            trace_id=trace_id,
        )
    )

    return {
        "task_id": task_id,
        "status": completed_task.status,
        "trace_id": trace_id,
        "target": completed_task.target,
    }
