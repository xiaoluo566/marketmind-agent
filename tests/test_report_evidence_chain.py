from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.api.schemas.tasks import TaskStatusData
from app.main import create_app
from app.reporting.evidence import (
    SQLAlchemyEvidenceChainStore,
    attach_evidence_chain,
    parse_evidence_ref,
)
from app.reporting.generator import (
    EvidenceSnippet,
    ReportGenerationInput,
    StructuredReportGenerator,
)
from app.reporting.stores import SQLAlchemyReportStore
from app.storage.base import Base
from app.storage.database import get_db_session
from app.storage.models import (
    AgentRun,
    AgentStep,
    Artifact,
    Product,
    Project,
    Report,
    Review,
    ReviewChunk,
    Task,
    User,
)
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
            Artifact.__table__,
            AgentRun.__table__,
            AgentStep.__table__,
            Report.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_evidence_records(session_factory) -> None:
    now = datetime(2026, 5, 25, 15, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id="tsk_evidence_001",
            status="completed",
            trace_id="trc_evidence_001",
            target="demo://portable-espresso-maker",
            mode="competitive_research",
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
                id="prd_evidence_001",
                task_id="tsk_evidence_001",
                title="Portable Espresso Maker",
                source_url="https://example.com/product/espresso",
            )
            review = Review(
                id="rev_return",
                product_id="prd_evidence_001",
                task_id="tsk_evidence_001",
                external_id="return-001",
                source_url="https://example.com/product/espresso#return-001",
                source_type="crawler",
                rating=1.0,
                content="The pump failed after three days and support ignored the return request.",
            )
            chunk = ReviewChunk(
                id="chk_return",
                review_id="rev_return",
                task_id="tsk_evidence_001",
                chunk_index=0,
                content="The pump failed after three days and support ignored the return request.",
                embedding=[0.0] * 1536,
                embedding_model="fake-embedding-v1",
                embedding_dimensions=1536,
                metadata_={"source_type": "crawler"},
            )
            artifact = Artifact(
                id="art_html",
                task_id="tsk_evidence_001",
                artifact_type="crawler_html",
                uri="data/artifacts/crawler/tsk_evidence_001/page.html",
                mime_type="text/html",
                checksum="checksum-html",
                metadata_={"source_url": "https://example.com/product/espresso"},
            )
            run = AgentRun(
                id="run_evidence",
                task_id="tsk_evidence_001",
                status="completed",
            )
            step = AgentStep(
                id="stp_search",
                agent_run_id="run_evidence",
                task_id="tsk_evidence_001",
                step_index=1,
                step_type="action",
                tool_name="search_reviews_tool",
                tool_input={"query": "return support"},
                tool_output={"evidence_refs": ["chunk:chk_return"]},
                observation="Found return support evidence.",
                status="success",
            )
            session.add_all([product, review, chunk, artifact, run, step])


def build_report_with_chain(session_factory) -> str:
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_evidence_001",
            product_name="Portable Espresso Maker",
            observations=["search_reviews_tool returned one return-support evidence chunk."],
            evidence_snippets=[
                EvidenceSnippet(
                    evidence_ref="chunk:chk_return",
                    content=(
                        "The pump failed after three days and support ignored "
                        "the return request."
                    ),
                    similarity=0.9,
                    rating=1.0,
                    source_url="https://example.com/product/espresso#return-001",
                )
            ],
            requested_focus=["return support"],
        )
    )
    chain = SQLAlchemyEvidenceChainStore(session_factory).resolve(
        task_id="tsk_evidence_001",
        evidence_refs=["chunk:chk_return", "artifact:art_html", "step:stp_search"],
    )
    bound_report = attach_evidence_chain(report, chain)
    saved = SQLAlchemyReportStore(session_factory).save_report(bound_report)
    return saved.report_id


def test_parse_evidence_ref_supports_known_ref_types() -> None:
    parsed = parse_evidence_ref("chunk:chk_return")

    assert parsed.ref_type == "chunk"
    assert parsed.source_id == "chk_return"
    assert parsed.evidence_ref == "chunk:chk_return"


def test_parse_evidence_ref_rejects_malformed_refs() -> None:
    with pytest.raises(ValueError, match="invalid evidence ref"):
        parse_evidence_ref("chunk")

    with pytest.raises(ValueError, match="unsupported evidence ref type"):
        parse_evidence_ref("url:https://example.com")


def test_evidence_chain_resolves_review_chunk_artifact_and_agent_step() -> None:
    session_factory = build_session_factory()
    seed_evidence_records(session_factory)

    chain = SQLAlchemyEvidenceChainStore(session_factory).resolve(
        task_id="tsk_evidence_001",
        evidence_refs=["chunk:chk_return", "artifact:art_html", "step:stp_search"],
    )

    assert chain.task_id == "tsk_evidence_001"
    assert chain.missing_refs == []
    assert [source.evidence_ref for source in chain.sources] == [
        "chunk:chk_return",
        "artifact:art_html",
        "step:stp_search",
    ]
    chunk_source = chain.sources[0]
    assert chunk_source.source_type == "review_chunk"
    assert chunk_source.parent_refs == ["review:rev_return"]
    assert chunk_source.source_url == "https://example.com/product/espresso#return-001"
    assert "pump failed" in chunk_source.content_preview
    assert chain.sources[1].source_type == "artifact"
    assert chain.sources[2].source_type == "agent_step"


def test_evidence_chain_marks_missing_or_cross_task_refs_without_fabricating() -> None:
    session_factory = build_session_factory()
    seed_evidence_records(session_factory)

    chain = SQLAlchemyEvidenceChainStore(session_factory).resolve(
        task_id="tsk_evidence_001",
        evidence_refs=["chunk:missing", "review:rev_return"],
    )

    assert chain.missing_refs == ["chunk:missing"]
    assert chain.sources[0].available is False
    assert chain.sources[0].missing_reason == "EVIDENCE_NOT_FOUND"
    assert chain.sources[1].available is True


def test_attach_evidence_chain_returns_new_report_and_renders_citations() -> None:
    session_factory = build_session_factory()
    seed_evidence_records(session_factory)
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id="tsk_evidence_001",
            product_name="Portable Espresso Maker",
            evidence_snippets=[
                EvidenceSnippet(
                    evidence_ref="chunk:chk_return",
                    content=(
                        "The pump failed after three days and support ignored "
                        "the return request."
                    ),
                    similarity=0.9,
                    rating=1.0,
                )
            ],
        )
    )
    chain = SQLAlchemyEvidenceChainStore(session_factory).resolve(
        task_id="tsk_evidence_001",
        evidence_refs=["chunk:chk_return"],
    )

    bound_report = attach_evidence_chain(report, chain)
    markdown = bound_report.to_markdown()

    assert "evidence_chain" not in report.metadata
    assert bound_report.metadata["evidence_chain"]["sources"][0]["source_type"] == "review_chunk"
    assert "## 证据链回查" in markdown
    assert "review:rev_return" in markdown


def test_report_evidence_api_returns_structured_evidence_chain() -> None:
    session_factory = build_session_factory()
    seed_evidence_records(session_factory)
    report_id = build_report_with_chain(session_factory)
    app = create_app()
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    client = TestClient(app)

    response = client.get(
        f"/api/reports/{report_id}/evidence",
        headers={"X-Trace-Id": "trc_report_evidence"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_report_evidence"
    assert body["data"]["report_id"] == report_id
    assert body["data"]["task_id"] == "tsk_evidence_001"
    assert body["data"]["sources"][0]["evidence_ref"] == "chunk:chk_return"
    assert body["data"]["sources"][0]["parent_refs"] == ["review:rev_return"]


def test_report_evidence_api_returns_not_found_for_missing_report() -> None:
    session_factory = build_session_factory()
    seed_evidence_records(session_factory)
    app = create_app()
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    client = TestClient(app)

    response = client.get("/api/reports/rpt_missing/evidence")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REPORT_NOT_FOUND"


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
