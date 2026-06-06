from functools import lru_cache

from app.core.config import get_settings
from app.observability.error_store import ErrorLogStore, SQLAlchemyErrorLogStore
from app.storage.agent_stores import SQLAlchemyAgentRunStore
from app.storage.crawl_stores import SQLAlchemyCrawlResultStore
from app.storage.database import SessionLocal
from app.storage.task_stores import (
    MirroredTaskEventStore,
    MirroredTaskStatusStore,
    SQLAlchemyTaskEventStore,
    SQLAlchemyTaskStatusStore,
)
from app.tasks.dispatcher import CeleryTaskDispatcher, TaskQueueDispatcher
from app.tasks.event_store import RedisTaskEventStore, TaskEventStore
from app.tasks.status_store import RedisTaskStatusStore, TaskStatusStore


@lru_cache
def get_task_status_store() -> TaskStatusStore:
    settings = get_settings()
    redis_store = RedisTaskStatusStore(
        redis_url=settings.task_status_redis_url,
        ttl_seconds=settings.task_status_ttl_seconds,
    )
    database_store = SQLAlchemyTaskStatusStore(
        session_factory=SessionLocal,
        default_user_id=settings.default_local_user_id,
        default_user_email=settings.default_local_user_email,
        default_project_id=settings.default_local_project_id,
        default_project_name=settings.default_local_project_name,
    )
    return MirroredTaskStatusStore(primary=redis_store, secondary=database_store)


@lru_cache
def get_task_event_store() -> TaskEventStore:
    settings = get_settings()
    redis_store = RedisTaskEventStore(
        redis_url=settings.task_status_redis_url,
        ttl_seconds=settings.task_status_ttl_seconds,
    )
    database_store = SQLAlchemyTaskEventStore(session_factory=SessionLocal)
    return MirroredTaskEventStore(primary=redis_store, secondary=database_store)


@lru_cache
def get_task_dispatcher() -> TaskQueueDispatcher:
    return CeleryTaskDispatcher()


@lru_cache
def get_crawl_result_store() -> SQLAlchemyCrawlResultStore:
    return SQLAlchemyCrawlResultStore(session_factory=SessionLocal)


@lru_cache
def get_agent_run_store() -> SQLAlchemyAgentRunStore:
    return SQLAlchemyAgentRunStore(session_factory=SessionLocal)


@lru_cache
def get_error_log_store() -> ErrorLogStore:
    return SQLAlchemyErrorLogStore(session_factory=SessionLocal)
