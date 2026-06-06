from datetime import UTC, datetime

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.agent_stores import SQLAlchemyAgentRunStore
from app.storage.base import Base
from app.storage.models import AgentRun, AgentStep, Project, Task, User
from app.storage.statuses import AgentStepStatus, TaskStatus
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from app.tasks.dependencies import (
    get_agent_run_store,
    get_task_dispatcher,
    get_task_event_store,
    get_task_status_store,
)
from app.tasks.dispatcher import QueueDispatchResult
from app.tasks.event_store import InMemoryTaskEventStore
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class FakeDispatcher:
    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        return QueueDispatchResult(queue_task_id=f"celery_{task_id}")


def build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Project.__table__,
            Task.__table__,
            AgentRun.__table__,
            AgentStep.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client():
    app = create_app()
    session_factory = build_session_factory()
    status_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    event_store = InMemoryTaskEventStore()
    agent_store = SQLAlchemyAgentRunStore(session_factory=session_factory)
    app.dependency_overrides[get_task_status_store] = lambda: status_store
    app.dependency_overrides[get_task_event_store] = lambda: event_store
    app.dependency_overrides[get_task_dispatcher] = lambda: FakeDispatcher()
    app.dependency_overrides[get_agent_run_store] = lambda: agent_store
    return TestClient(app), status_store, agent_store


def seed_task(status_store: SQLAlchemyTaskStatusStore, task_id: str = "tsk_steps_001") -> None:
    now = datetime(2026, 6, 7, 9, 0, tzinfo=UTC)
    status_store.create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            trace_id="trc_steps_001",
            target="demo://portable-espresso-maker-negative-reviews",
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def test_get_task_steps_returns_sanitized_agent_steps() -> None:
    client, status_store, agent_store = build_client()
    seed_task(status_store)
    run = agent_store.create_run(task_id="tsk_steps_001")
    agent_store.append_step(
        agent_run_id=run.run_id,
        task_id="tsk_steps_001",
        step_type="thought",
        thought="内部推理不应该暴露给前端。",
        status=AgentStepStatus.SUCCESS.value,
        started_at=datetime(2026, 6, 7, 9, 1, tzinfo=UTC),
        finished_at=datetime(2026, 6, 7, 9, 1, 1, tzinfo=UTC),
    )
    agent_store.append_step(
        agent_run_id=run.run_id,
        task_id="tsk_steps_001",
        step_type="action",
        tool_name="search_reviews_tool",
        tool_input={"query": "quality issue", "top_k": 3},
        tool_output={"evidence_refs": ["chunk:chk_001"]},
        observation="Found 1 review chunk for quality issue.",
        status=AgentStepStatus.SUCCESS.value,
        started_at=datetime(2026, 6, 7, 9, 2, tzinfo=UTC),
        finished_at=datetime(2026, 6, 7, 9, 2, 2, tzinfo=UTC),
    )

    response = client.get(
        "/api/tasks/tsk_steps_001/steps",
        headers={"X-Trace-Id": "trc_steps_get"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_steps_get"
    assert body["data"]["task_id"] == "tsk_steps_001"
    assert body["data"]["steps"][0]["step_type"] == "thought"
    assert body["data"]["steps"][0]["input_summary"] == "Thought recorded"
    assert "thought" not in body["data"]["steps"][0]
    assert body["data"]["steps"][1]["tool_name"] == "search_reviews_tool"
    assert body["data"]["steps"][1]["duration_ms"] == 2000
    assert body["data"]["steps"][1]["observation_summary"] == (
        "Found 1 review chunk for quality issue."
    )


def test_get_task_steps_returns_empty_list_when_task_has_no_agent_run() -> None:
    client, status_store, _ = build_client()
    seed_task(status_store, task_id="tsk_no_steps")

    response = client.get("/api/tasks/tsk_no_steps/steps")

    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"task_id": "tsk_no_steps", "steps": []}


def test_get_task_steps_returns_not_found_for_missing_task() -> None:
    client, _, _ = build_client()

    response = client.get("/api/tasks/tsk_missing/steps", headers={"X-Trace-Id": "trc_missing"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_missing"
    assert body["error"]["code"] == "TASK_NOT_FOUND"
