from __future__ import annotations

from datetime import UTC, datetime

from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.storage.base import Base
from app.storage.database import get_db_session
from app.storage.models import Product, Project, Report, Review, ReviewChunk, Task, User
from app.storage.task_stores import SQLAlchemyTaskStatusStore
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
            Product.__table__,
            Review.__table__,
            ReviewChunk.__table__,
            Report.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client(session_factory) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    return TestClient(app)


def seed_export_report(session_factory) -> str:
    now = datetime(2026, 5, 28, 10, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id="tsk_export_001",
            status="completed",
            trace_id="trc_export_001",
            target="demo://portable-espresso-maker",
            mode="complete_report",
            priority="normal",
            source_type="demo_dataset",
            options={},
            created_at=now,
            updated_at=now,
        )
    )
    with session_factory() as session:
        with session.begin():
            product = Product(
                id="prd_export_001",
                task_id="tsk_export_001",
                title="Portable Espresso Maker",
                source_url="https://example.com/products/espresso",
            )
            review = Review(
                id="rev_export_return",
                product_id="prd_export_001",
                task_id="tsk_export_001",
                external_id="return-001",
                source_url="https://example.com/products/espresso#return-001",
                source_type="crawler",
                rating=1.0,
                content="The pump failed after three days and support ignored the return request.",
                raw_payload={
                    "public_cluster": "return_support",
                    "api_key": "sk-should-not-export",
                    "authorization": "Bearer should-not-export",
                },
            )
            chunk = ReviewChunk(
                id="chk_export_return",
                review_id="rev_export_return",
                task_id="tsk_export_001",
                chunk_index=0,
                content="The pump failed after three days and support ignored the return request.",
                embedding=[0.0] * 1536,
                embedding_model="fake-embedding-v1",
                embedding_dimensions=1536,
                metadata_={
                    "cluster": "return_support",
                    "provider_token": "token-should-not-export",
                },
            )
            report = Report(
                id="rpt_export_001",
                task_id="tsk_export_001",
                title="Portable Espresso Maker Evidence Report",
                status="draft",
                summary="Return support and product reliability are the main risks.",
                content_markdown=(
                    "# Portable Espresso Maker Evidence Report\n\n"
                    "## Risk\n\n"
                    "Return support complaints cite `chunk:chk_export_return`.\n"
                ),
                content_json={
                    "sections": [
                        {
                            "heading": "Risk",
                            "claim": "Return support complaints are repeated.",
                            "evidence_refs": ["chunk:chk_export_return"],
                            "severity": "high",
                        }
                    ],
                    "metadata": {
                        "analysis_scorecard": {
                            "overall_risk_score": 72,
                        }
                    },
                },
                evidence_refs=["chunk:chk_export_return", "chunk:missing"],
                schema_version="report.v1",
            )
            session.add_all([product, review, chunk, report])
    return "rpt_export_001"


def test_report_markdown_export_returns_downloadable_markdown() -> None:
    session_factory = build_session_factory()
    report_id = seed_export_report(session_factory)
    client = build_client(session_factory)

    response = client.get(
        f"/api/reports/{report_id}/export/markdown",
        headers={"X-Trace-Id": "trc_export_markdown"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == (
        'attachment; filename="marketmind-report-rpt_export_001.md"'
    )
    assert "# Portable Espresso Maker Evidence Report" in response.text
    assert "chunk:chk_export_return" in response.text


def test_report_evidence_package_exports_sanitized_sources() -> None:
    session_factory = build_session_factory()
    report_id = seed_export_report(session_factory)
    client = build_client(session_factory)

    response = client.get(
        f"/api/reports/{report_id}/evidence-package",
        headers={"X-Trace-Id": "trc_export_evidence"},
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == (
        'attachment; filename="marketmind-evidence-rpt_export_001.json"'
    )
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_export_evidence"

    package = body["data"]
    assert package["package_version"] == "evidence_package.v1"
    assert package["report_id"] == report_id
    assert package["task_id"] == "tsk_export_001"
    assert package["evidence_refs"] == ["chunk:chk_export_return", "chunk:missing"]
    assert package["sources"][0]["evidence_ref"] == "chunk:chk_export_return"
    assert package["sources"][0]["source_url"] == (
        "https://example.com/products/espresso#return-001"
    )
    assert package["sources"][1]["available"] is False
    assert package["sources"][1]["missing_reason"] == "EVIDENCE_NOT_FOUND"

    serialized = response.text.lower()
    assert "sk-should-not-export" not in serialized
    assert "token-should-not-export" not in serialized
    assert "authorization" not in serialized
    assert "api_key" not in serialized


def test_report_export_missing_report_uses_error_envelope() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)

    response = client.get(
        "/api/reports/rpt_missing/export/markdown",
        headers={"X-Trace-Id": "trc_export_missing"},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["trace_id"] == "trc_export_missing"
    assert body["error"]["code"] == "REPORT_NOT_FOUND"


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
