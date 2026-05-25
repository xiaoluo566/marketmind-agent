from __future__ import annotations

from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError

from app.api.schemas.tasks import TaskEventData


class TaskEventStore(Protocol):
    def append(self, event: TaskEventData) -> TaskEventData: ...

    def list_for_task(self, task_id: str) -> list[TaskEventData]: ...


class TaskEventStoreUnavailableError(RuntimeError):
    pass


class InMemoryTaskEventStore:
    def __init__(self) -> None:
        self._events: dict[str, list[TaskEventData]] = {}

    def append(self, event: TaskEventData) -> TaskEventData:
        next_event = event.model_copy(deep=True)
        self._events.setdefault(next_event.task_id, []).append(next_event)
        return next_event.model_copy(deep=True)

    def list_for_task(self, task_id: str) -> list[TaskEventData]:
        return [event.model_copy(deep=True) for event in self._events.get(task_id, [])]


class RedisTaskEventStore:
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int,
        key_prefix: str = "marketmind:task-events",
    ) -> None:
        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def append(self, event: TaskEventData) -> TaskEventData:
        key = self._key(event.task_id)
        try:
            self._client.rpush(key, event.model_dump_json())
            self._client.expire(key, self._ttl_seconds)
        except RedisError as exc:
            raise TaskEventStoreUnavailableError(str(exc)) from exc
        return event

    def list_for_task(self, task_id: str) -> list[TaskEventData]:
        try:
            raw_events = self._client.lrange(self._key(task_id), 0, -1)
        except RedisError as exc:
            raise TaskEventStoreUnavailableError(str(exc)) from exc
        return [TaskEventData.model_validate_json(raw_event) for raw_event in raw_events]

    def _key(self, task_id: str) -> str:
        return f"{self._key_prefix}:{task_id}"
