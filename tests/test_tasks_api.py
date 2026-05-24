from app.main import create_app
from app.storage.statuses import TaskStatus
from app.tasks.dependencies import get_task_dispatcher, get_task_status_store
from app.tasks.dispatcher import QueueDispatchResult, QueueUnavailableError
from app.tasks.status_store import InMemoryTaskStatusStore, TaskStatusStoreUnavailableError
from fastapi.testclient import TestClient


class FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        self.calls.append(
            {
                "task_id": task_id,
                "payload": payload,
                "trace_id": trace_id,
            }
        )
        return QueueDispatchResult(queue_task_id=f"celery_{task_id}")


class FailingDispatcher:
    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        raise QueueUnavailableError("redis broker is unavailable")


class FailingStatusStore(InMemoryTaskStatusStore):
    def create(self, task):
        raise TaskStatusStoreUnavailableError("redis status store is unavailable")


def build_client(
    store: InMemoryTaskStatusStore | None = None,
    dispatcher: FakeDispatcher | FailingDispatcher | None = None,
) -> tuple[TestClient, InMemoryTaskStatusStore, FakeDispatcher | FailingDispatcher]:
    app = create_app()
    task_store = store or InMemoryTaskStatusStore()
    task_dispatcher = dispatcher or FakeDispatcher()
    app.dependency_overrides[get_task_status_store] = lambda: task_store
    app.dependency_overrides[get_task_dispatcher] = lambda: task_dispatcher
    return TestClient(app), task_store, task_dispatcher


def test_create_task_returns_accepted_envelope() -> None:
    client, store, dispatcher = build_client()

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_day4_task"},
        json={
            "target": "https://example.com/products/portable-espresso-maker",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "use_rag": True,
                "export_format": "markdown",
            },
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "accepted"
    assert body["trace_id"] == "trc_day4_task"
    assert response.headers["X-Trace-Id"] == "trc_day4_task"
    assert body["data"]["task_id"].startswith("tsk_")
    assert body["data"]["status"] == "queued"
    assert body["data"]["trace_id"] == "trc_day4_task"
    assert body["data"]["queue_task_id"].startswith("celery_tsk_")

    task_id = body["data"]["task_id"]
    stored_task = store.get(task_id)
    assert stored_task is not None
    assert stored_task.status == TaskStatus.QUEUED.value
    assert stored_task.queue_task_id == body["data"]["queue_task_id"]
    assert isinstance(dispatcher, FakeDispatcher)
    assert dispatcher.calls[0]["task_id"] == task_id
    assert dispatcher.calls[0]["trace_id"] == "trc_day4_task"
    assert dispatcher.calls[0]["payload"]["target"].endswith("portable-espresso-maker")


def test_create_task_applies_contract_defaults() -> None:
    client, store, _ = build_client()

    response = client.post(
        "/api/tasks",
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["data"]["status"] == "queued"
    assert body["trace_id"].startswith("trc_")
    stored_task = store.get(body["data"]["task_id"])
    assert stored_task is not None
    assert stored_task.mode == "competitive_research"
    assert stored_task.priority == "normal"
    assert stored_task.source_type == "demo_dataset"


def test_get_task_returns_status_from_status_store() -> None:
    client, _, _ = build_client()
    created_response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_lookup"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )
    task_id = created_response.json()["data"]["task_id"]

    response = client.get(f"/api/tasks/{task_id}", headers={"X-Trace-Id": "trc_lookup_get"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_lookup_get"
    assert body["data"]["task_id"] == task_id
    assert body["data"]["status"] == "queued"
    assert body["data"]["target"] == "demo://portable-espresso-maker-negative-reviews"


def test_get_task_returns_not_found_envelope() -> None:
    client, _, _ = build_client()

    response = client.get("/api/tasks/tsk_missing", headers={"X-Trace-Id": "trc_missing"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_missing"
    assert body["error"]["code"] == "TASK_NOT_FOUND"


def test_create_task_validation_error_uses_api_envelope() -> None:
    client, _, _ = build_client()

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_invalid_task"},
        json={
            "target": "   ",
            "mode": "unsupported_mode",
            "priority": "urgent",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"] == "request validation failed"
    assert body["trace_id"] == "trc_invalid_task"
    assert response.headers["X-Trace-Id"] == "trc_invalid_task"
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert body["error"]["details"]["errors"]


def test_create_task_queue_unavailable_returns_error_envelope() -> None:
    client, store, _ = build_client(dispatcher=FailingDispatcher())

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_queue_down"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_queue_down"
    assert body["error"]["code"] == "QUEUE_UNAVAILABLE"

    created_tasks = list(store.items())
    assert len(created_tasks) == 1
    assert created_tasks[0].status == TaskStatus.RECEIVED.value


def test_create_task_status_store_unavailable_returns_error_envelope() -> None:
    client, _, _ = build_client(store=FailingStatusStore())

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_store_down"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_store_down"
    assert body["error"]["code"] == "QUEUE_UNAVAILABLE"
