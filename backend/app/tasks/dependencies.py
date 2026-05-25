from functools import lru_cache

from app.core.config import get_settings
from app.tasks.dispatcher import CeleryTaskDispatcher, TaskQueueDispatcher
from app.tasks.event_store import RedisTaskEventStore, TaskEventStore
from app.tasks.status_store import RedisTaskStatusStore, TaskStatusStore


@lru_cache
def get_task_status_store() -> TaskStatusStore:
    settings = get_settings()
    return RedisTaskStatusStore(
        redis_url=settings.task_status_redis_url,
        ttl_seconds=settings.task_status_ttl_seconds,
    )


@lru_cache
def get_task_event_store() -> TaskEventStore:
    settings = get_settings()
    return RedisTaskEventStore(
        redis_url=settings.task_status_redis_url,
        ttl_seconds=settings.task_status_ttl_seconds,
    )


@lru_cache
def get_task_dispatcher() -> TaskQueueDispatcher:
    return CeleryTaskDispatcher()
