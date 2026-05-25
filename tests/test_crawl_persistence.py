from datetime import UTC, datetime

from app.api.schemas.tasks import TaskStatusData
from app.crawler.schemas import CrawlArtifact, CrawlResult, CrawlReview
from app.storage.base import Base
from app.storage.crawl_stores import SQLAlchemyCrawlResultStore
from app.storage.models import Artifact, CrawledPage, Product, Project, Review, Task, User
from app.storage.task_stores import SQLAlchemyTaskStatusStore
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
            Product.__table__,
            CrawledPage.__table__,
            Review.__table__,
            Artifact.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_task(session_factory, task_id: str = "tsk_crawl_db") -> None:
    now = datetime(2026, 5, 25, 11, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status="running",
            trace_id="trc_crawl_db",
            target="https://example.com/product/espresso",
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def build_crawl_result() -> CrawlResult:
    return CrawlResult(
        url="https://example.com/product/espresso",
        source_type="html_fixture",
        title="Portable Espresso Maker",
        price=39.99,
        rating=4.6,
        extracted_text="Portable Espresso Maker Travel ready. The pump stopped working.",
        html="<html><body><h1>Portable Espresso Maker</h1></body></html>",
        artifacts=[
            CrawlArtifact(
                artifact_type="crawler_html",
                path="data/artifacts/crawler/tsk_crawl_db/page.html",
                mime_type="text/html",
                checksum="checksum-001",
            )
        ],
        reviews=[
            CrawlReview(
                external_id="rev-001",
                content="The pump stopped working after three days.",
                rating=1.0,
                source_url="https://example.com/product/espresso#rev-001",
            )
        ],
    )


def test_crawl_result_store_persists_product_page_artifact_and_reviews() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    store = SQLAlchemyCrawlResultStore(session_factory=session_factory)

    persisted = store.persist_success(task_id="tsk_crawl_db", result=build_crawl_result())

    assert persisted.product_id is not None
    assert persisted.page_id is not None
    assert len(persisted.artifact_ids) == 1
    assert len(persisted.review_ids) == 1

    with session_factory() as session:
        product = session.get(Product, persisted.product_id)
        page = session.get(CrawledPage, persisted.page_id)
        artifact = session.get(Artifact, persisted.artifact_ids[0])
        review = session.get(Review, persisted.review_ids[0])

    assert product is not None
    assert product.task_id == "tsk_crawl_db"
    assert product.title == "Portable Espresso Maker"
    assert product.source_url == "https://example.com/product/espresso"
    assert product.price == 39.99
    assert page is not None
    assert page.task_id == "tsk_crawl_db"
    assert page.product_id == product.id
    assert page.html_artifact_id == artifact.id
    assert "Travel ready" in page.extracted_text
    assert artifact is not None
    assert artifact.artifact_type == "crawler_html"
    assert artifact.uri.endswith("page.html")
    assert review is not None
    assert review.product_id == product.id
    assert review.task_id == "tsk_crawl_db"
    assert review.external_id == "rev-001"


def test_crawl_result_store_is_idempotent_for_same_task_and_source() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    store = SQLAlchemyCrawlResultStore(session_factory=session_factory)

    first = store.persist_success(task_id="tsk_crawl_db", result=build_crawl_result())
    second = store.persist_success(task_id="tsk_crawl_db", result=build_crawl_result())

    assert second.product_id == first.product_id
    assert second.page_id == first.page_id
    assert second.artifact_ids == first.artifact_ids
    assert second.review_ids == first.review_ids
    with session_factory() as session:
        assert len(session.scalars(select(Product)).all()) == 1
        assert len(session.scalars(select(CrawledPage)).all()) == 1
        assert len(session.scalars(select(Artifact)).all()) == 1
        assert len(session.scalars(select(Review)).all()) == 1
