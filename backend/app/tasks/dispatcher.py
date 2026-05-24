from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class QueueDispatchResult:
    queue_task_id: str


class QueueUnavailableError(RuntimeError):
    pass


class TaskQueueDispatcher(Protocol):
    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult: ...


class CeleryTaskDispatcher:
    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        from app.worker.tasks import process_research_task

        try:
            result = process_research_task.apply_async(
                kwargs={
                    "task_id": task_id,
                    "payload": payload,
                    "trace_id": trace_id,
                }
            )
        except Exception as exc:
            raise QueueUnavailableError(str(exc)) from exc

        return QueueDispatchResult(queue_task_id=result.id)
