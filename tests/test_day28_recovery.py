from __future__ import annotations

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.statuses import TaskStatus
from app.tasks.dependencies import get_task_dispatcher, get_task_event_store, get_task_status_store
from app.tasks.dispatcher import QueueDispatchResult, QueueUnavailableError
from app.tasks.event_store import InMemoryTaskEventStore
from app.tasks.recovery import (
    RecoveryDecision,
    RetryErrorClassification,
    classify_retry_error,
    plan_retry,
)
from app.tasks.service import build_task_event
from app.tasks.status_store import InMemoryTaskStatusStore, utc_now
from app.worker.tasks import run_research_task
from fastapi.testclient import TestClient


class CapturingDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        self.calls.append({"task_id": task_id, "payload": payload, "trace_id": trace_id})
        return QueueDispatchResult(queue_task_id=f"retry_{len(self.calls)}")


class FailingRetryDispatcher:
    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        raise QueueUnavailableError("broker unavailable during retry")


def test_retry_error_classification_marks_recoverable_and_terminal_errors() -> None:
    assert classify_retry_error("PAGE_TIMEOUT") == RetryErrorClassification.RETRYABLE
    assert classify_retry_error("NETWORK_ERROR") == RetryErrorClassification.RETRYABLE
    assert classify_retry_error("ACCESS_BLOCKED") == RetryErrorClassification.RETRYABLE
    assert classify_retry_error("CRAWL_PERSISTENCE_FAILED") == RetryErrorClassification.RETRYABLE
    assert classify_retry_error("DOM_NOT_FOUND") == RetryErrorClassification.NOT_RETRYABLE
    assert classify_retry_error("PARSER_ERROR") == RetryErrorClassification.NOT_RETRYABLE
    assert classify_retry_error(None) == RetryErrorClassification.UNKNOWN


def test_plan_retry_uses_attempt_limit_and_exponential_backoff() -> None:
    first = plan_retry(error_code="ACCESS_BLOCKED", retry_count=0, max_attempts=3)
    third = plan_retry(error_code="ACCESS_BLOCKED", retry_count=2, max_attempts=3)
    blocked = plan_retry(error_code="ACCESS_BLOCKED", retry_count=3, max_attempts=3)
    not_retryable = plan_retry(error_code="DOM_NOT_FOUND", retry_count=0, max_attempts=3)

    assert first.decision == RecoveryDecision.RETRY
    assert first.next_retry_count == 1
    assert first.backoff_seconds == 30
    assert third.decision == RecoveryDecision.RETRY
    assert third.next_retry_count == 3
    assert third.backoff_seconds == 120
    assert blocked.decision == RecoveryDecision.LIMIT_REACHED
    assert not_retryable.decision == RecoveryDecision.NOT_RETRYABLE


def test_retry_api_moves_failed_task_to_waiting_retry_then_queues_existing_task() -> None:
    client, status_store, event_store, dispatcher = build_retry_client()
    failed_task = seed_failed_task(status_store=status_store, event_store=event_store)

    response = client.post(
        f"/api/tasks/{failed_task.task_id}/retry",
        headers={"X-Trace-Id": "trc_retry_request"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["data"]["task_id"] == failed_task.task_id
    assert body["data"]["status"] == TaskStatus.QUEUED.value
    assert body["data"]["queue_task_id"] == "retry_1"

    stored = status_store.get(failed_task.task_id)
    assert stored is not None
    assert stored.status == TaskStatus.QUEUED.value
    assert stored.queue_task_id == "retry_1"
    assert stored.error_code is None
    assert stored.options["recovery"]["retry_count"] == 1
    assert stored.options["recovery"]["last_error_code"] == "ACCESS_BLOCKED"
    assert stored.options["recovery"]["resume_from_event_id"] == "evt_crawl_started"

    assert dispatcher.calls == [
        {
            "task_id": failed_task.task_id,
            "payload": {
                "target": failed_task.target,
                "mode": failed_task.mode,
                "priority": failed_task.priority,
                "source_type": failed_task.source_type,
                "options": stored.options,
            },
            "trace_id": "trc_retry_request",
        }
    ]
    assert [event.message for event in event_store.list_for_task(failed_task.task_id)] == [
        "task running",
        "crawl started",
        "crawl failed",
        "task waiting retry",
        "task requeued",
    ]


def test_retry_api_rejects_not_retryable_or_limit_reached_tasks() -> None:
    client, status_store, event_store, _ = build_retry_client()
    not_retryable = seed_failed_task(
        status_store=status_store,
        event_store=event_store,
        task_id="tsk_not_retryable",
        error_code="DOM_NOT_FOUND",
    )
    limit_reached = seed_failed_task(
        status_store=status_store,
        event_store=event_store,
        task_id="tsk_limit",
        error_code="ACCESS_BLOCKED",
        options={"recovery": {"retry_count": 3}},
    )

    first_response = client.post(f"/api/tasks/{not_retryable.task_id}/retry")
    second_response = client.post(f"/api/tasks/{limit_reached.task_id}/retry")

    assert first_response.status_code == 409
    assert first_response.json()["error"]["code"] == "TASK_NOT_RETRYABLE"
    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == "TASK_RETRY_LIMIT_REACHED"


def test_retry_api_keeps_task_failed_when_requeue_fails() -> None:
    status_store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    failed_task = seed_failed_task(status_store=status_store, event_store=event_store)
    client, _, _, _ = build_retry_client(
        status_store=status_store,
        event_store=event_store,
        dispatcher=FailingRetryDispatcher(),
    )

    response = client.post(f"/api/tasks/{failed_task.task_id}/retry")

    assert response.status_code == 503
    stored = status_store.get(failed_task.task_id)
    assert stored is not None
    assert stored.status == TaskStatus.FAILED.value
    assert stored.error_code == "QUEUE_UNAVAILABLE"
    assert [event.message for event in event_store.list_for_task(failed_task.task_id)][-1] == (
        "task retry queue unavailable"
    )


def test_worker_records_recovery_resume_event_before_retry_run(tmp_path) -> None:
    status_store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    task = TaskStatusData(
        task_id="tsk_retry_worker",
        status=TaskStatus.QUEUED.value,
        trace_id="trc_retry_worker",
        target="https://example.com/products/retry",
        mode="competitive_research",
        priority="normal",
        source_type="public_url",
        options={
            "artifact_dir": str(tmp_path),
            "fixture_html": "<html><body><h1>Recovered Product</h1><p>$19.99</p></body></html>",
            "recovery": {
                "retry_count": 1,
                "resume_from_event_id": "evt_crawl_started",
                "last_error_code": "ACCESS_BLOCKED",
            },
        },
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    status_store.create(task)

    result = run_research_task(
        task_id=task.task_id,
        payload={
            "target": task.target,
            "mode": task.mode,
            "priority": task.priority,
            "source_type": task.source_type,
            "options": task.options,
        },
        trace_id=task.trace_id,
        status_store=status_store,
        event_store=event_store,
    )

    assert result["status"] == TaskStatus.COMPLETED.value
    events = event_store.list_for_task(task.task_id)
    assert events[0].message == "task recovery resumed"
    assert events[0].payload["retry_count"] == 1
    assert events[0].payload["resume_from_event_id"] == "evt_crawl_started"


def test_day28_docs_record_recovery_scope_and_boundaries() -> None:
    assert "backend/app/tasks/recovery.py" in read_project_file("doc/roadmap/day-28.md")
    assert "POST /api/tasks/{task_id}/retry" in read_project_file("doc/roadmap/day-28.md")
    assert "Day 28 开发记录" in read_project_file("doc/supporting/development-log.md")
    assert "Day 28 做失败重试" in read_project_file(
        "doc/supporting/interview-defense-dossier.md"
    )
    assert "Day 28 Retry / Resume 测试边界" in read_project_file(
        "doc/supporting/testing-strategy.md"
    )


def build_retry_client(
    *,
    status_store: InMemoryTaskStatusStore | None = None,
    event_store: InMemoryTaskEventStore | None = None,
    dispatcher: CapturingDispatcher | FailingRetryDispatcher | None = None,
):
    app = create_app()
    task_store = status_store or InMemoryTaskStatusStore()
    task_event_store = event_store or InMemoryTaskEventStore()
    task_dispatcher = dispatcher or CapturingDispatcher()
    app.dependency_overrides[get_task_status_store] = lambda: task_store
    app.dependency_overrides[get_task_event_store] = lambda: task_event_store
    app.dependency_overrides[get_task_dispatcher] = lambda: task_dispatcher
    return TestClient(app), task_store, task_event_store, task_dispatcher


def seed_failed_task(
    *,
    status_store: InMemoryTaskStatusStore,
    event_store: InMemoryTaskEventStore,
    task_id: str = "tsk_failed_retryable",
    error_code: str = "ACCESS_BLOCKED",
    options: dict | None = None,
) -> TaskStatusData:
    task = TaskStatusData(
        task_id=task_id,
        status=TaskStatus.FAILED.value,
        trace_id="trc_failed_retryable",
        target="https://example.com/products/retryable",
        mode="competitive_research",
        priority="normal",
        source_type="public_url",
        options=options or {},
        error_code=error_code,
        error_message="crawler failed",
        started_at=utc_now(),
        finished_at=utc_now(),
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    status_store.create(task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            event_type="status",
            message="task running",
            payload={},
            trace_id=task.trace_id,
        ).model_copy(update={"event_id": "evt_running"})
    )
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            event_type="crawler",
            message="crawl started",
            payload={},
            trace_id=task.trace_id,
        ).model_copy(update={"event_id": "evt_crawl_started"})
    )
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.FAILED.value,
            event_type="crawler_error",
            message="crawl failed",
            payload={"error_code": error_code},
            trace_id=task.trace_id,
        ).model_copy(update={"event_id": "evt_crawl_failed"})
    )
    return task


def read_project_file(relative_path: str) -> str:
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")
