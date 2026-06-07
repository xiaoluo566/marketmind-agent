from __future__ import annotations

from dataclasses import dataclass, field

from app.main import create_app
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.review_index import SQLAlchemyReviewChunkStore
from app.reporting.generator import (
    EvidenceSnippet,
    ReportGenerationInput,
    StructuredReportGenerator,
)
from app.reporting.stores import SQLAlchemyReportStore
from app.storage.base import Base
from app.storage.crawl_stores import SQLAlchemyCrawlResultStore
from app.storage.database import get_db_session
from app.storage.models import (
    Artifact,
    CrawledPage,
    Product,
    Project,
    Report,
    Review,
    ReviewChunk,
    Task,
    TaskEvent,
    User,
)
from app.storage.statuses import TaskStatus
from app.storage.task_stores import SQLAlchemyTaskEventStore, SQLAlchemyTaskStatusStore
from app.tasks.dependencies import (
    get_task_dispatcher,
    get_task_event_store,
    get_task_status_store,
)
from app.tasks.dispatcher import QueueDispatchResult
from app.worker.tasks import run_research_task
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@dataclass
class CapturingDispatcher:
    queue_task_id: str = "celery_day24_flow"
    calls: list[dict] = field(default_factory=list)

    def enqueue(self, task_id: str, payload: dict, trace_id: str) -> QueueDispatchResult:
        self.calls.append({"task_id": task_id, "payload": payload, "trace_id": trace_id})
        return QueueDispatchResult(queue_task_id=self.queue_task_id)


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
            Product.__table__,
            CrawledPage.__table__,
            Review.__table__,
            ReviewChunk.__table__,
            Artifact.__table__,
            Report.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client(
    *,
    session_factory,
    status_store: SQLAlchemyTaskStatusStore,
    event_store: SQLAlchemyTaskEventStore,
    dispatcher: CapturingDispatcher,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_task_status_store] = lambda: status_store
    app.dependency_overrides[get_task_event_store] = lambda: event_store
    app.dependency_overrides[get_task_dispatcher] = lambda: dispatcher
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    return TestClient(app)


def test_day24_main_flow_submits_crawls_indexes_reports_and_resolves_evidence(tmp_path) -> None:
    session_factory = build_session_factory()
    status_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    event_store = SQLAlchemyTaskEventStore(session_factory=session_factory)
    dispatcher = CapturingDispatcher()
    client = build_client(
        session_factory=session_factory,
        status_store=status_store,
        event_store=event_store,
        dispatcher=dispatcher,
    )

    accepted_response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_day24_flow"},
        json={
            "target": "https://example.com/products/portable-espresso-maker",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "artifact_dir": str(tmp_path),
                "fixture_html": """
                    <html>
                      <body>
                        <h1>Portable Espresso Maker</h1>
                        <p>$39.99</p>
                        <p>4.2 out of 5</p>
                        <article class="review" data-review-id="rev-return">
                          <p>The pump failed after three days.</p>
                          <p>Support ignored my return request. 1 out of 5</p>
                        </article>
                        <article class="review" data-review-id="rev-shipping">
                          <p>Shipping was slow and the shell arrived cracked. 2 out of 5</p>
                        </article>
                      </body>
                    </html>
                """,
            },
        },
    )

    assert accepted_response.status_code == 202
    accepted = accepted_response.json()["data"]
    task_id = accepted["task_id"]
    assert accepted["status"] == TaskStatus.QUEUED.value
    assert accepted["queue_task_id"] == "celery_day24_flow"
    assert dispatcher.calls[0]["task_id"] == task_id

    worker_result = run_research_task(
        task_id=task_id,
        payload=dispatcher.calls[0]["payload"],
        trace_id=dispatcher.calls[0]["trace_id"],
        status_store=status_store,
        event_store=event_store,
        crawl_result_store=SQLAlchemyCrawlResultStore(session_factory=session_factory),
    )

    assert worker_result["status"] == TaskStatus.COMPLETED.value
    task_response = client.get(f"/api/tasks/{task_id}")
    events_response = client.get(f"/api/tasks/{task_id}/events")
    assert task_response.json()["data"]["status"] == TaskStatus.COMPLETED.value
    assert [event["message"] for event in events_response.json()["data"]["events"]] == [
        "task received",
        "task queued",
        "task running",
        "crawl started",
        "crawl completed",
        "task completed",
    ]

    chunk_store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    embedding_provider = DeterministicEmbeddingProvider(dimensions=1536)
    index_result = chunk_store.index_task_reviews(
        task_id=task_id,
        embedding_provider=embedding_provider,
    )
    search_results = chunk_store.search_similar_reviews(
        task_id=task_id,
        query="return support pump failed",
        embedding_provider=embedding_provider,
        top_k=2,
    )

    assert index_result.review_count == 2
    assert index_result.chunk_count == 2
    assert {result.review_external_id for result in search_results} == {
        "rev-return",
        "rev-shipping",
    }

    snippets = [
        EvidenceSnippet(
            evidence_ref=f"chunk:{result.chunk_id}",
            content=result.content,
            similarity=result.similarity,
            rating=result.rating,
            source_url=result.source_url,
            metadata={"review_external_id": result.review_external_id},
        )
        for result in search_results
    ]
    report = StructuredReportGenerator().generate(
        ReportGenerationInput(
            task_id=task_id,
            product_name=_product_title(session_factory, task_id),
            observations=["Worker persisted crawler reviews and RAG indexed them."],
            evidence_snippets=snippets,
            requested_focus=["return support", "shipping risk"],
            metadata={"analysis_scorecard": {"overall_risk_score": 72}},
        )
    )
    saved_report = SQLAlchemyReportStore(session_factory=session_factory).save_report(report)

    list_response = client.get("/api/reports", params={"task_status": "completed"})
    detail_response = client.get(f"/api/reports/{saved_report.report_id}")
    evidence_response = client.get(f"/api/reports/{saved_report.report_id}/evidence")

    assert list_response.status_code == 200
    assert list_response.json()["data"]["items"][0]["report_id"] == saved_report.report_id
    assert list_response.json()["data"]["items"][0]["risk_score"] == 72
    assert detail_response.json()["data"]["task_id"] == task_id
    assert detail_response.json()["data"]["evidence_refs"] == saved_report.evidence_refs

    evidence = evidence_response.json()["data"]
    assert evidence["missing_refs"] == []
    assert evidence["evidence_refs"] == saved_report.evidence_refs
    assert {source["source_type"] for source in evidence["sources"]} == {"review_chunk"}
    assert all(source["available"] for source in evidence["sources"])
    assert all(source["parent_refs"][0].startswith("review:") for source in evidence["sources"])


def _product_title(session_factory, task_id: str) -> str:
    with session_factory() as session:
        product = session.scalars(select(Product).where(Product.task_id == task_id)).one()
        return product.title


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
