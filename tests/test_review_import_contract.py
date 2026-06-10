from __future__ import annotations

import json
from pathlib import Path

from app.main import create_app
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.review_index import SQLAlchemyReviewChunkStore
from app.storage.base import Base
from app.storage.database import get_db_session
from app.storage.models import Product, Project, Review, ReviewChunk, Task, User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]


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
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_client(session_factory) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = build_session_override(session_factory)
    return TestClient(app)


def test_csv_review_import_persists_valid_rows_reports_errors_and_dedupes() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)
    csv_content = "\n".join(
        [
            "review_id,product_title,rating,content,author,published_at,source_url",
            "rev-001,Desk Lamp,1,The hinge broke after two days,Alice,2026-05-01,https://example.test/rev-001",
            "rev-002,Desk Lamp,2,Shipping was slow and support ignored me,Bob,2026-05-02,https://example.test/rev-002",
            "rev-bad,Desk Lamp,5,,Cara,2026-05-03,https://example.test/rev-bad",
            "rev-001,Desk Lamp,1,The hinge broke after two days,Alice,2026-05-01,https://example.test/rev-001",
        ]
    )

    response = client.post(
        "/api/imports/reviews",
        json={
            "format": "csv",
            "content": csv_content,
            "product_title": "Desk Lamp",
            "source_url": "demo://desk-lamp/reviews.csv",
        },
        headers={"X-Trace-Id": "trc_import_csv"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["trace_id"] == "trc_import_csv"
    data = body["data"]
    assert data["format"] == "csv"
    assert data["task_id"].startswith("tsk_")
    assert data["product_id"].startswith("prd_")
    assert data["imported_count"] == 2
    assert data["duplicate_count"] == 1
    assert data["error_count"] == 1
    assert data["errors"] == [
        {
            "row_number": 4,
            "field": "content",
            "message": "content is required",
        }
    ]
    assert data["review_external_ids"] == ["rev-001", "rev-002"]

    with session_factory() as session:
        reviews = session.scalars(select(Review).order_by(Review.external_id.asc())).all()
        task = session.get(Task, data["task_id"])

    assert task is not None
    assert task.source_type == "manual_upload"
    assert task.status == "completed"
    assert [review.external_id for review in reviews] == ["rev-001", "rev-002"]
    assert {review.source_type for review in reviews} == {"manual_upload"}


def test_json_review_import_accepts_reviews_array_and_can_be_indexed_for_rag() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)
    payload = {
        "product_title": "Pet Fountain",
        "source_url": "demo://pet-fountain/reviews.json",
        "reviews": [
            {
                "review_id": "rev-leak",
                "rating": 1,
                "content": "The pump leaks and the water smells bad.",
                "author": "buyer-a",
            },
            {
                "review_id": "rev-return",
                "rating": 2,
                "content": "Return process was slow and customer support never replied.",
                "author": "buyer-b",
            },
        ],
    }

    response = client.post(
        "/api/imports/reviews",
        json={
            "format": "json",
            "content": json.dumps(payload),
            "product_title": "Pet Fountain",
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["imported_count"] == 2
    assert data["error_count"] == 0

    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    provider = DeterministicEmbeddingProvider(dimensions=1536)
    index_result = store.index_task_reviews(task_id=data["task_id"], embedding_provider=provider)
    results = store.search_similar_reviews(
        task_id=data["task_id"],
        query="return customer support",
        embedding_provider=provider,
        top_k=1,
    )

    assert index_result.review_count == 2
    assert index_result.chunk_count == 2
    assert results[0].review_external_id == "rev-return"
    assert "support" in results[0].content


def test_review_import_rejects_invalid_json_without_writing_rows() -> None:
    session_factory = build_session_factory()
    client = build_client(session_factory)

    response = client.post(
        "/api/imports/reviews",
        json={
            "format": "json",
            "content": "{not-json",
            "product_title": "Broken Import",
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "REVIEW_IMPORT_INVALID_PAYLOAD"

    with session_factory() as session:
        assert session.scalars(select(Review)).all() == []


def build_session_override(session_factory):
    def override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return override
