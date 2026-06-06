from datetime import UTC, datetime, timedelta

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.observability.error_store import (
    ErrorLayer,
    ErrorLogData,
    InMemoryErrorLogStore,
    SQLAlchemyErrorLogStore,
)
from app.storage.base import Base
from app.storage.models import ErrorLog, Project, Task, User
from app.storage.statuses import TaskStatus
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from app.tasks.dependencies import get_task_dispatcher, get_task_event_store, get_task_status_store
from app.tasks.dispatcher import QueueUnavailableError
from app.tasks.event_store import InMemoryTaskEventStore
from app.tasks.status_store import InMemoryTaskStatusStore, utc_now
from app.worker.tasks import run_research_task
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def build_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Project.__table__,
            Task.__table__,
            ErrorLog.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_task_status(task_id: str = "tsk_obs_001") -> TaskStatusData:
    now = datetime(2026, 5, 26, 10, 0, tzinfo=UTC)
    return TaskStatusData(
        task_id=task_id,
        status=TaskStatus.QUEUED.value,
        trace_id="trc_obs_001",
        target="https://example.com/product/blocked",
        mode="competitive_research",
        priority="normal",
        source_type="public_url",
        options={},
        created_at=now,
        updated_at=now,
    )


def test_sqlalchemy_error_log_store_persists_sanitized_error_details() -> None:
    session_factory = build_session_factory()
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(build_task_status())
    store = SQLAlchemyErrorLogStore(session_factory=session_factory)

    first = store.append(
        ErrorLogData(
            task_id="tsk_obs_001",
            trace_id="trc_obs_001",
            layer=ErrorLayer.CRAWLER,
            error_code="ACCESS_BLOCKED",
            message="crawler was blocked",
            details={
                "stage": "crawl",
                "duration_ms": 42,
                "api_key": "sk-secret",
                "nested": {"authorization": "Bearer token", "safe": "kept"},
            },
            created_at=datetime(2026, 5, 26, 10, 1, tzinfo=UTC),
        )
    )
    second = store.append(
        ErrorLogData(
            task_id="tsk_obs_001",
            trace_id="trc_obs_001",
            layer=ErrorLayer.WORKER,
            error_code="WORKER_FAILED",
            message="worker failed",
            details={"stage": "worker"},
            created_at=datetime(2026, 5, 26, 10, 2, tzinfo=UTC),
        )
    )

    logs = store.list_for_task("tsk_obs_001")

    assert [log.error_id for log in logs] == [first.error_id, second.error_id]
    assert logs[0].details["api_key"] == "[REDACTED]"
    assert logs[0].details["nested"]["authorization"] == "[REDACTED]"
    assert logs[0].details["nested"]["safe"] == "kept"
    with session_factory() as session:
        persisted = session.scalars(select(ErrorLog).order_by(ErrorLog.created_at.asc())).all()
    assert [row.error_code for row in persisted] == ["ACCESS_BLOCKED", "WORKER_FAILED"]


def test_worker_crawler_failure_records_classified_error_log(tmp_path) -> None:
    status_store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    error_store = InMemoryErrorLogStore()
    status_store.create(build_task_status(task_id="tsk_obs_worker"))

    result = run_research_task(
        task_id="tsk_obs_worker",
        payload={
            "target": "https://example.com/product/blocked",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "artifact_dir": str(tmp_path),
                "fixture_html": "<html><body><h1>Access Denied</h1><p>captcha</p></body></html>",
            },
        },
        trace_id="trc_obs_worker",
        status_store=status_store,
        event_store=event_store,
        error_log_store=error_store,
    )

    logs = error_store.list_for_task("tsk_obs_worker")

    assert result["error_code"] == "ACCESS_BLOCKED"
    assert len(logs) == 1
    assert logs[0].layer == ErrorLayer.CRAWLER
    assert logs[0].trace_id == "trc_obs_worker"
    assert logs[0].details["stage"] == "crawl"
    assert isinstance(logs[0].details["duration_ms"], int)
    assert logs[0].details["duration_ms"] >= 0


class FailingDispatcher:
    def enqueue(self, task_id: str, payload: dict, trace_id: str):
        raise QueueUnavailableError("redis broker is unavailable")


def test_api_app_error_records_error_log_and_request_duration_header() -> None:
    app = create_app()
    status_store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    error_store = InMemoryErrorLogStore()
    app.state.error_log_store = error_store
    app.dependency_overrides[get_task_status_store] = lambda: status_store
    app.dependency_overrides[get_task_event_store] = lambda: event_store
    app.dependency_overrides[get_task_dispatcher] = lambda: FailingDispatcher()
    client = TestClient(app)

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_obs_api"},
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    body = response.json()
    logs = error_store.list_for_trace("trc_obs_api")

    assert response.status_code == 503
    assert response.headers["X-Trace-Id"] == "trc_obs_api"
    assert int(response.headers["X-Request-Duration-Ms"]) >= 0
    assert body["error"]["code"] == "QUEUE_UNAVAILABLE"
    assert len(logs) == 1
    assert logs[0].layer == ErrorLayer.API
    assert logs[0].error_code == "QUEUE_UNAVAILABLE"
    assert logs[0].details["path"] == "/api/tasks"
    assert logs[0].details["method"] == "POST"
    assert isinstance(logs[0].details["duration_ms"], int)


def test_error_log_store_filters_by_trace_id() -> None:
    store = InMemoryErrorLogStore()
    now = utc_now()
    store.append(
        ErrorLogData(
            task_id="tsk_a",
            trace_id="trc_a",
            layer=ErrorLayer.API,
            error_code="VALIDATION_FAILED",
            message="validation failed",
            details={},
            created_at=now,
        )
    )
    store.append(
        ErrorLogData(
            task_id="tsk_b",
            trace_id="trc_b",
            layer=ErrorLayer.DATABASE,
            error_code="DATABASE_UNAVAILABLE",
            message="database unavailable",
            details={},
            created_at=now + timedelta(seconds=1),
        )
    )

    assert [log.trace_id for log in store.list_for_trace("trc_a")] == ["trc_a"]


def test_observability_errors_api_lists_logs_by_trace_id() -> None:
    app = create_app()
    error_store = InMemoryErrorLogStore()
    error_store.append(
        ErrorLogData(
            task_id="tsk_api_log",
            trace_id="trc_api_log",
            layer=ErrorLayer.WORKER,
            error_code="WORKER_FAILED",
            message="worker failed",
            details={"stage": "worker"},
        )
    )
    app.state.error_log_store = error_store
    client = TestClient(app)

    response = client.get(
        "/api/observability/errors",
        headers={"X-Trace-Id": "trc_query"},
        params={"trace_id": "trc_api_log"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["trace_id"] == "trc_query"
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["task_id"] == "tsk_api_log"
    assert body["data"]["items"][0]["layer"] == "worker"
    assert body["data"]["items"][0]["error_code"] == "WORKER_FAILED"


def test_observability_errors_api_requires_trace_or_task_filter() -> None:
    app = create_app()
    app.state.error_log_store = InMemoryErrorLogStore()
    client = TestClient(app)

    response = client.get("/api/observability/errors", headers={"X-Trace-Id": "trc_query"})

    body = response.json()

    assert response.status_code == 400
    assert body["success"] is False
    assert body["error"]["code"] == "OBSERVABILITY_FILTER_REQUIRED"
