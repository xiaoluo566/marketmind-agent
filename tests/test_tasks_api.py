from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.statuses import TaskStatus
from app.tasks.dependencies import get_task_dispatcher, get_task_event_store, get_task_status_store
from app.tasks.dispatcher import QueueDispatchResult, QueueUnavailableError
from app.tasks.event_store import InMemoryTaskEventStore, TaskEventStoreUnavailableError
from app.tasks.status_store import InMemoryTaskStatusStore, TaskStatusStoreUnavailableError, utc_now
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


class FailingEventStore(InMemoryTaskEventStore):
    def append(self, event):
        raise TaskEventStoreUnavailableError("redis event store is unavailable")


class FailingEventReadStore(InMemoryTaskEventStore):
    def list_for_task(self, task_id: str):
        raise TaskEventStoreUnavailableError("redis event store is unavailable")


def build_client(
    store: InMemoryTaskStatusStore | None = None,
    event_store: InMemoryTaskEventStore | None = None,
    dispatcher: FakeDispatcher | FailingDispatcher | None = None,
) -> tuple[
    TestClient,
    InMemoryTaskStatusStore,
    InMemoryTaskEventStore,
    FakeDispatcher | FailingDispatcher,
]:
    app = create_app()
    task_store = store or InMemoryTaskStatusStore()
    task_event_store = event_store or InMemoryTaskEventStore()
    task_dispatcher = dispatcher or FakeDispatcher()
    app.dependency_overrides[get_task_status_store] = lambda: task_store
    app.dependency_overrides[get_task_event_store] = lambda: task_event_store
    app.dependency_overrides[get_task_dispatcher] = lambda: task_dispatcher
    return TestClient(app), task_store, task_event_store, task_dispatcher


def test_create_task_returns_accepted_envelope() -> None:
    client, store, event_store, dispatcher = build_client()

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

    events = event_store.list_for_task(task_id)
    assert [event.status for event in events] == [
        TaskStatus.RECEIVED.value,
        TaskStatus.QUEUED.value,
    ]
    assert [event.message for event in events] == ["task received", "task queued"]


def test_create_task_applies_contract_defaults() -> None:
    client, store, event_store, _ = build_client()

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
    assert len(event_store.list_for_task(body["data"]["task_id"])) == 2


def test_get_task_returns_status_from_status_store() -> None:
    client, _, _, _ = build_client()
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


def test_get_task_events_returns_task_timeline() -> None:
    client, _, _, _ = build_client()
    created_response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_events"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )
    task_id = created_response.json()["data"]["task_id"]

    response = client.get(f"/api/tasks/{task_id}/events", headers={"X-Trace-Id": "trc_events_2"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["task_id"] == task_id
    assert len(body["data"]["events"]) == 2
    assert body["data"]["events"][0]["status"] == TaskStatus.RECEIVED.value
    assert body["data"]["events"][1]["status"] == TaskStatus.QUEUED.value


def test_get_task_events_returns_not_found_envelope() -> None:
    client, _, _, _ = build_client()

    response = client.get("/api/tasks/tsk_missing/events", headers={"X-Trace-Id": "trc_missing"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_missing"
    assert body["error"]["code"] == "TASK_NOT_FOUND"


def test_get_task_events_event_store_unavailable_returns_error_envelope() -> None:
    store = InMemoryTaskStatusStore()
    created_at = utc_now()
    store.create(
        TaskStatusData(
            task_id="tsk_event_store_down",
            status=TaskStatus.QUEUED.value,
            trace_id="trc_event_store_down",
            target="demo://portable-espresso-maker-negative-reviews",
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            created_at=created_at,
            updated_at=created_at,
        )
    )
    client, _, _, _ = build_client(store=store, event_store=FailingEventReadStore())

    response = client.get(
        "/api/tasks/tsk_event_store_down/events",
        headers={"X-Trace-Id": "trc_event_store_down"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_event_store_down"
    assert body["error"]["code"] == "EVENT_STORE_UNAVAILABLE"


def test_get_task_returns_not_found_envelope() -> None:
    client, _, _, _ = build_client()

    response = client.get("/api/tasks/tsk_missing", headers={"X-Trace-Id": "trc_missing"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_missing"
    assert body["error"]["code"] == "TASK_NOT_FOUND"


def test_create_task_validation_error_uses_api_envelope() -> None:
    client, _, _, _ = build_client()

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
    client, store, event_store, _ = build_client(dispatcher=FailingDispatcher())

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
    assert created_tasks[0].status == TaskStatus.FAILED.value

    events = event_store.list_for_task(created_tasks[0].task_id)
    assert [event.status for event in events] == [
        TaskStatus.RECEIVED.value,
        TaskStatus.FAILED.value,
    ]
    assert events[-1].event_type == "error"


def test_create_task_status_store_unavailable_returns_error_envelope() -> None:
    client, _, _, _ = build_client(store=FailingStatusStore())

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


def test_create_task_event_store_unavailable_returns_error_envelope() -> None:
    client, _, _, _ = build_client(event_store=FailingEventStore())

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_event_down"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_event_down"
    assert body["error"]["code"] == "EVENT_STORE_UNAVAILABLE"
