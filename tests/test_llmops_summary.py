from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.base import Base
from app.storage.database import get_db_session
from app.storage.models import AgentRun, Project, Task, TaskEvent, User
from app.storage.statuses import AgentRunStatus, TaskStatus
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"


def read_frontend(relative_path: str) -> str:
    path = FRONTEND_SRC / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


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
            TaskEvent.__table__,
            AgentRun.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client(session_factory) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    return TestClient(app)


def test_llmops_summary_api_aggregates_database_metrics_with_source_labels() -> None:
    session_factory = build_session_factory()
    seed_llmops_metrics(session_factory)
    client = build_client(session_factory)

    response = client.get(
        "/api/observability/llmops-summary",
        headers={"X-Trace-Id": "trc_llmops_summary"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["trace_id"] == "trc_llmops_summary"

    data = body["data"]
    assert data["summary_version"] == "llmops.summary.v1"
    assert data["data_freshness"] == "database_snapshot"
    assert "database:tasks" in data["data_sources"]
    assert "database:agent_runs" in data["data_sources"]
    assert "database:task_events" in data["data_sources"]

    task_metrics = data["task_metrics"]
    assert task_metrics["total_tasks"] == 3
    assert task_metrics["completed_tasks"] == 2
    assert task_metrics["failed_tasks"] == 1
    assert task_metrics["success_rate"] == 0.6667
    assert task_metrics["failure_rate"] == 0.3333
    assert task_metrics["average_duration_ms"] == 90000
    assert task_metrics["data_source"] == "database:tasks"

    model_usage = data["model_usage"]
    assert model_usage["agent_run_count"] == 2
    assert model_usage["model_call_count"] == 2
    assert model_usage["input_tokens"] == 140
    assert model_usage["output_tokens"] == 80
    assert model_usage["total_tokens"] == 220
    assert model_usage["reported_cost"] == 0.07
    assert model_usage["cost_source"] == "agent_runs.total_cost"
    assert model_usage["cost_confidence"] == "provider_reported_or_manual_recorded"

    guardrails = data["guardrail_metrics"]
    assert guardrails["validation_error_count"] == 3
    assert guardrails["self_heal_count"] == 1
    assert guardrails["self_heal_success_rate"] == 0.3333
    assert guardrails["data_source"] == "database:agent_runs"

    recovery = data["recovery_metrics"]
    assert recovery["retry_requested_count"] == 1
    assert recovery["retry_requeued_count"] == 1
    assert recovery["recovery_resumed_count"] == 1
    assert recovery["retry_queue_unavailable_count"] == 0
    assert recovery["recovery_success_count"] == 1
    assert recovery["recovery_success_rate"] == 1.0
    assert recovery["data_source"] == "database:task_events+tasks"

    provider = data["provider_metrics"]
    assert provider["embedding_provider_calls"] == 0
    assert provider["average_latency_ms"] == 0
    assert provider["data_source"] == "not_persisted"
    assert "Day35" in provider["note"]
    assert "暂无真实 provider 成本数据" in data["warnings"]


def test_llmops_summary_api_returns_zero_baseline_for_empty_database() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)

    response = client.get("/api/observability/llmops-summary")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["task_metrics"]["total_tasks"] == 0
    assert data["task_metrics"]["success_rate"] == 0.0
    assert data["model_usage"]["total_tokens"] == 0
    assert data["model_usage"]["cost_confidence"] == "not_available"
    assert data["guardrail_metrics"]["self_heal_success_rate"] == 0.0
    assert data["recovery_metrics"]["recovery_success_rate"] == 0.0
    assert "暂无真实 provider 成本数据" in data["warnings"]


def test_frontend_dashboard_consumes_llmops_summary_with_chinese_copy() -> None:
    api_source = read_frontend("lib/api.ts")
    types_source = read_frontend("lib/types.ts")
    mock_data = read_frontend("lib/mock-data.ts")
    dashboard = read_frontend("app/page.tsx")

    assert "export type LLMOpsSummary" in types_source
    assert "export async function getLLMOpsSummary" in api_source
    assert "/api/observability/llmops-summary" in api_source
    assert "llmopsSummary" in mock_data

    for chinese_copy in [
        "LLMOps 指标",
        "数据来源",
        "模型调用",
        "Token 总量",
        "自愈成功率",
        "恢复成功率",
        "llmopsSummary.warnings",
    ]:
        assert chinese_copy in dashboard


def seed_llmops_metrics(session_factory) -> None:
    now = datetime(2026, 5, 29, 10, 0, tzinfo=UTC)
    store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    store.create(
        build_task_status(
            task_id="tsk_completed_plain",
            status=TaskStatus.COMPLETED.value,
            started_at=now,
            finished_at=now + timedelta(seconds=60),
        )
    )
    store.create(
        build_task_status(
            task_id="tsk_completed_recovery",
            status=TaskStatus.COMPLETED.value,
            started_at=now,
            finished_at=now + timedelta(seconds=180),
            options={"recovery": {"retry_count": 1}},
        )
    )
    store.create(
        build_task_status(
            task_id="tsk_failed",
            status=TaskStatus.FAILED.value,
            started_at=now,
            finished_at=now + timedelta(seconds=30),
            error_code="ACCESS_BLOCKED",
        )
    )

    with session_factory() as session:
        with session.begin():
            session.add_all(
                [
                    AgentRun(
                        id="run_completed",
                        task_id="tsk_completed_plain",
                        status=AgentRunStatus.COMPLETED.value,
                        model_provider="openai-compatible",
                        model_name="gpt-5.4-mini",
                        report_model_name="gpt-5.5",
                        prompt_version="report.evidence_chain.v1",
                        input_tokens=100,
                        output_tokens=40,
                        total_tokens=140,
                        total_cost=0.03,
                        validation_error_count=2,
                        self_heal_count=1,
                    ),
                    AgentRun(
                        id="run_failed",
                        task_id="tsk_failed",
                        status=AgentRunStatus.FAILED.value,
                        model_provider="openai-compatible",
                        model_name="gpt-5.4-mini",
                        report_model_name="gpt-5.5",
                        prompt_version="report.evidence_chain.v1",
                        input_tokens=40,
                        output_tokens=40,
                        total_tokens=80,
                        total_cost=0.04,
                        validation_error_count=1,
                        self_heal_count=0,
                    ),
                    TaskEvent(
                        id="evt_waiting_retry",
                        task_id="tsk_completed_recovery",
                        status=TaskStatus.WAITING_RETRY.value,
                        event_type="status",
                        message="task waiting retry",
                        payload={"retry_count": 1},
                        trace_id="trc_recovery",
                    ),
                    TaskEvent(
                        id="evt_requeued",
                        task_id="tsk_completed_recovery",
                        status=TaskStatus.QUEUED.value,
                        event_type="status",
                        message="task requeued",
                        payload={"retry_count": 1},
                        trace_id="trc_recovery",
                    ),
                    TaskEvent(
                        id="evt_recovery_resumed",
                        task_id="tsk_completed_recovery",
                        status=TaskStatus.RUNNING.value,
                        event_type="recovery",
                        message="task recovery resumed",
                        payload={"retry_count": 1},
                        trace_id="trc_recovery",
                    ),
                ]
            )


def build_task_status(
    *,
    task_id: str,
    status: str,
    started_at: datetime,
    finished_at: datetime,
    options: dict | None = None,
    error_code: str | None = None,
) -> TaskStatusData:
    return TaskStatusData(
        task_id=task_id,
        status=status,
        trace_id=f"trc_{task_id}",
        target=f"demo://{task_id}",
        mode="complete_report",
        priority="normal",
        source_type="demo_dataset",
        options=options or {},
        error_code=error_code,
        error_message=None if error_code is None else "task failed",
        started_at=started_at,
        finished_at=finished_at,
        created_at=started_at,
        updated_at=finished_at,
    )


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
