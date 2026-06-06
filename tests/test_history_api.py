from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.base import Base
from app.storage.database import get_db_session
from app.storage.models import Project, Report, Task, User
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from app.tasks.dependencies import get_task_status_store
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


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
            Report.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client(session_factory) -> TestClient:
    app = create_app()
    task_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    app.dependency_overrides[get_task_status_store] = lambda: task_store
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    return TestClient(app)


def seed_task(
    session_factory,
    *,
    task_id: str,
    status: str,
    created_at: datetime,
    target: str = "demo://portable-espresso-maker",
) -> None:
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status=status,
            trace_id=f"trc_{task_id}",
            target=target,
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            error_code="PAGE_TIMEOUT" if status == "failed" else None,
            error_message="crawler timeout" if status == "failed" else None,
            created_at=created_at,
            updated_at=created_at,
        )
    )


def seed_report(session_factory, *, task_id: str, report_id: str = "rpt_history_001") -> str:
    with session_factory() as session:
        with session.begin():
            report = Report(
                id=report_id,
                task_id=task_id,
                title="Portable Espresso Maker Report",
                status="draft",
                summary="Quality and support issues dominate negative reviews.",
                content_markdown="# Portable Espresso Maker Report\n",
                content_json={
                    "sections": [
                        {
                            "heading": "Quality risk",
                            "claim": "Pump leakage appears in several reviews.",
                            "evidence_refs": ["chunk:chk_quality"],
                            "severity": "high",
                        }
                    ],
                    "metadata": {
                        "analysis_scorecard": {
                            "overall_risk_score": 76,
                        }
                    },
                },
                evidence_refs=["chunk:chk_quality", "step:stp_search"],
                schema_version="report.v1",
            )
            session.add(report)
    return report_id


def test_list_tasks_returns_history_sorted_and_keeps_failed_tasks() -> None:
    session_factory = build_session_factory()
    base_time = datetime(2026, 5, 26, 10, 0, tzinfo=UTC)
    seed_task(
        session_factory,
        task_id="tsk_old_failed",
        status="failed",
        created_at=base_time - timedelta(hours=2),
    )
    seed_task(
        session_factory,
        task_id="tsk_new_completed",
        status="completed",
        created_at=base_time,
    )
    client = build_client(session_factory)

    response = client.get("/api/tasks", headers={"X-Trace-Id": "trc_history"})

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_history"
    assert body["data"]["total"] == 2
    assert [item["task_id"] for item in body["data"]["items"]] == [
        "tsk_new_completed",
        "tsk_old_failed",
    ]
    assert body["data"]["items"][1]["status"] == "failed"
    assert body["data"]["items"][1]["error_code"] == "PAGE_TIMEOUT"


def test_list_tasks_supports_status_and_time_filters_with_pagination() -> None:
    session_factory = build_session_factory()
    base_time = datetime(2026, 5, 26, 10, 0, tzinfo=UTC)
    seed_task(session_factory, task_id="tsk_failed_a", status="failed", created_at=base_time)
    seed_task(
        session_factory,
        task_id="tsk_failed_b",
        status="failed",
        created_at=base_time + timedelta(minutes=5),
    )
    seed_task(
        session_factory,
        task_id="tsk_completed",
        status="completed",
        created_at=base_time + timedelta(minutes=10),
    )
    client = build_client(session_factory)

    response = client.get(
        "/api/tasks",
        params={
            "status": "failed",
            "created_after": (base_time - timedelta(minutes=1)).isoformat(),
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 2
    assert body["data"]["limit"] == 1
    assert body["data"]["offset"] == 1
    assert [item["task_id"] for item in body["data"]["items"]] == ["tsk_failed_a"]


def test_list_reports_and_report_detail_return_frontend_ready_payloads() -> None:
    session_factory = build_session_factory()
    created_at = datetime(2026, 5, 26, 10, 0, tzinfo=UTC)
    seed_task(
        session_factory,
        task_id="tsk_report_history",
        status="completed",
        created_at=created_at,
    )
    report_id = seed_report(session_factory, task_id="tsk_report_history")
    client = build_client(session_factory)

    list_response = client.get("/api/reports", headers={"X-Trace-Id": "trc_reports"})
    detail_response = client.get(f"/api/reports/{report_id}")

    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["trace_id"] == "trc_reports"
    assert list_body["data"]["total"] == 1
    assert list_body["data"]["items"][0]["report_id"] == report_id
    assert list_body["data"]["items"][0]["task_status"] == "completed"
    assert list_body["data"]["items"][0]["risk_score"] == 76
    assert list_body["data"]["items"][0]["evidence_count"] == 2

    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert detail["report_id"] == report_id
    assert detail["risk_level"] == "high"
    assert detail["sections"] == [
        {
            "title": "Quality risk",
            "body": "Pump leakage appears in several reviews.",
            "evidence_ids": ["chunk:chk_quality"],
        }
    ]


def test_report_detail_returns_not_found_envelope() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)

    response = client.get("/api/reports/rpt_missing", headers={"X-Trace-Id": "trc_missing_report"})

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_missing_report"
    assert body["error"]["code"] == "REPORT_NOT_FOUND"


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
