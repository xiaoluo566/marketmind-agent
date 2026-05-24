from app.api.schemas.tasks import TaskStatusData
from app.core.config import get_settings
from app.storage.statuses import TaskStatus
from app.tasks.status_store import RedisTaskStatusStore, utc_now
from app.worker.celery_app import celery_app


def _status_store() -> RedisTaskStatusStore:
    settings = get_settings()
    return RedisTaskStatusStore(
        redis_url=settings.task_status_redis_url,
        ttl_seconds=settings.task_status_ttl_seconds,
    )


@celery_app.task(name="marketmind.tasks.process_research_task")
def process_research_task(task_id: str, payload: dict, trace_id: str) -> dict:
    store = _status_store()
    current_task = store.get(task_id)
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
            "updated_at": utc_now(),
        }
    )
    store.save(running_task)

    completed_task = running_task.model_copy(
        update={
            "status": TaskStatus.COMPLETED.value,
            "updated_at": utc_now(),
        }
    )
    store.save(completed_task)

    return {
        "task_id": task_id,
        "status": completed_task.status,
        "trace_id": trace_id,
        "target": completed_task.target,
    }
