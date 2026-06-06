from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError

from app.api.schemas.tasks import TaskStatusData


def utc_now() -> datetime:
    return datetime.now(UTC)


class TaskStatusStore(Protocol):
    def create(self, task: TaskStatusData) -> TaskStatusData: ...

    def save(self, task: TaskStatusData) -> TaskStatusData: ...

    def get(self, task_id: str) -> TaskStatusData | None: ...

    def list(
        self,
        *,
        statuses: list[str] | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskStatusData], int]: ...


class TaskStatusStoreUnavailableError(RuntimeError):
    pass


class InMemoryTaskStatusStore:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskStatusData] = {}

    def create(self, task: TaskStatusData) -> TaskStatusData:
        return self.save(task)

    def save(self, task: TaskStatusData) -> TaskStatusData:
        next_task = task.model_copy(deep=True)
        self._tasks[next_task.task_id] = next_task
        return next_task.model_copy(deep=True)

    def get(self, task_id: str) -> TaskStatusData | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return task.model_copy(deep=True)

    def items(self) -> Iterable[TaskStatusData]:
        return [task.model_copy(deep=True) for task in self._tasks.values()]

    def list(
        self,
        *,
        statuses: list[str] | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskStatusData], int]:
        filtered = [
            task
            for task in self.items()
            if _matches_task_filters(
                task,
                statuses=statuses,
                created_after=created_after,
                created_before=created_before,
            )
        ]
        filtered.sort(key=lambda task: (task.created_at, task.task_id), reverse=True)
        return filtered[offset : offset + limit], len(filtered)


class RedisTaskStatusStore:
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int,
        key_prefix: str = "marketmind:task",
    ) -> None:
        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def create(self, task: TaskStatusData) -> TaskStatusData:
        return self.save(task)

    def save(self, task: TaskStatusData) -> TaskStatusData:
        key = self._key(task.task_id)
        try:
            self._client.set(key, task.model_dump_json(), ex=self._ttl_seconds)
        except RedisError as exc:
            raise TaskStatusStoreUnavailableError(str(exc)) from exc
        return task

    def get(self, task_id: str) -> TaskStatusData | None:
        try:
            raw_task = self._client.get(self._key(task_id))
        except RedisError as exc:
            raise TaskStatusStoreUnavailableError(str(exc)) from exc
        if raw_task is None:
            return None
        return TaskStatusData.model_validate_json(raw_task)

    def list(
        self,
        *,
        statuses: list[str] | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskStatusData], int]:
        raise TaskStatusStoreUnavailableError("redis status store does not support history listing")

    def _key(self, task_id: str) -> str:
        return f"{self._key_prefix}:{task_id}"


def _matches_task_filters(
    task: TaskStatusData,
    *,
    statuses: list[str] | None,
    created_after: datetime | None,
    created_before: datetime | None,
) -> bool:
    if statuses and task.status not in statuses:
        return False
    if created_after and task.created_at < created_after:
        return False
    if created_before and task.created_at > created_before:
        return False
    return True
