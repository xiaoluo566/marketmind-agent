from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.api.schemas.tasks import TaskStatusData
from app.reporting.generator import (
    EvidenceSnippet,
    ReportGenerationInput,
    StructuredReportGenerator,
)
from app.reporting.schemas import ReportFinding, StructuredReport
from app.reporting.stores import SQLAlchemyReportStore
from app.storage.base import Base
from app.storage.models import Project, Report, Task, User
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
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


def seed_task(session_factory, task_id: str = "tsk_report_001") -> None:
    now = datetime(2026, 5, 25, 14, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status="completed",
            trace_id="trc_report_001",
            target="demo://portable-espresso-maker",
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def test_structured_report_rejects_unknown_evidence_reference() -> None:
    with pytest.raises(ValidationError, match="unknown evidence refs"):
        StructuredReport(
            task_id="tsk_report_001",
            title="Portable Espresso Maker Evidence Report",
            summary="The main risk is product reliability.",
            evidence_refs=["chunk:known"],
            sections=[
                ReportFinding(
                    section_id="risk",
                    heading="Risk",
                    claim="Pump failure appears in negative reviews.",
                    evidence_refs=["chunk:missing"],
                    severity="high",
                )
            ],
        )


def test_generator_outputs_insufficient_evidence_without_fabricating_refs() -> None:
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_report_001",
            product_name="Portable Espresso Maker",
            observations=["Crawler returned product title but no review chunks matched."],
            evidence_snippets=[],
            requested_focus=["quality risk", "return support"],
        )
    )

    assert report.status == "insufficient_evidence"
    assert report.evidence_refs == []
    assert report.sections[0].evidence_refs == []
    assert "证据不足" in report.sections[0].claim
    assert "quality risk" in report.metadata["requested_focus"]


def test_generator_binds_findings_to_known_evidence_refs_and_renders_markdown() -> None:
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_report_001",
            product_name="Portable Espresso Maker",
            observations=["Crawler extracted 3 low-rating reviews."],
            evidence_snippets=[
                EvidenceSnippet(
                    evidence_ref="chunk:chk_return",
                    content=(
                        "The pump failed after three days and support ignored "
                        "the return request."
                    ),
                    similarity=0.86,
                    rating=1.0,
                    source_url="https://example.com/product/espresso#rev-return",
                    metadata={"query": "return support"},
                ),
                EvidenceSnippet(
                    evidence_ref="chunk:chk_shipping",
                    content="Shipping was slow and the box arrived cracked.",
                    similarity=0.74,
                    rating=2.0,
                    source_url="https://example.com/product/espresso#rev-shipping",
                ),
            ],
            requested_focus=["return support", "logistics"],
        )
    )

    markdown = report.to_markdown()

    assert report.status == "draft"
    assert report.evidence_refs == ["chunk:chk_return", "chunk:chk_shipping"]
    assert all(section.evidence_refs for section in report.sections)
    assert "chunk:chk_return" in markdown
    assert "Portable Espresso Maker" in markdown
    assert "证据引用" in markdown


def test_report_store_persists_validated_json_markdown_and_evidence_refs() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    store = SQLAlchemyReportStore(session_factory=session_factory)
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_report_001",
            product_name="Portable Espresso Maker",
            observations=[],
            evidence_snippets=[
                EvidenceSnippet(
                    evidence_ref="chunk:chk_return",
                    content="Return request and support were ignored.",
                    similarity=0.88,
                    rating=1.0,
                )
            ],
            requested_focus=["return support"],
        )
    )

    saved = store.save_report(report)

    with session_factory() as session:
        row = session.get(Report, saved.report_id)

    assert row is not None
    assert row.task_id == "tsk_report_001"
    assert row.status == "draft"
    assert row.schema_version == "report.v1"
    assert row.evidence_refs == ["chunk:chk_return"]
    assert row.content_json["sections"][0]["evidence_refs"] == ["chunk:chk_return"]
    assert "Return request" in row.content_markdown
