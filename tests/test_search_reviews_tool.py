from datetime import UTC, datetime

from app.agent.tools.builtin import build_default_tool_registry
from app.agent.tools.executor import ToolExecutor
from app.agent.tools.schemas import ToolInvocationContext
from app.api.schemas.tasks import TaskStatusData
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.review_index import SQLAlchemyReviewChunkStore
from app.storage.base import Base
from app.storage.models import Product, Project, Review, ReviewChunk, Task, User
from app.storage.task_stores import SQLAlchemyTaskStatusStore
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
            Product.__table__,
            Review.__table__,
            ReviewChunk.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_indexed_reviews(session_factory) -> None:
    now = datetime(2026, 5, 25, 13, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id="tsk_search_001",
            status="completed",
            trace_id="trc_search_001",
            target="demo://portable-espresso-maker-negative-reviews",
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
                task_id="tsk_search_001",
                title="Portable Espresso Maker",
                source_url="https://example.com/product/espresso",
            )
            session.add(product)
            session.flush()
            session.add_all(
                [
                    Review(
                        product_id=product.id,
                        task_id="tsk_search_001",
                        external_id="rev-return",
                        source_url="https://example.com/product/espresso#rev-return",
                        source_type="crawler",
                        rating=1.0,
                        content=(
                            "The pump failed after three days. "
                            "Return request and support were ignored."
                        ),
                    ),
                    Review(
                        product_id=product.id,
                        task_id="tsk_search_001",
                        external_id="rev-shipping",
                        source_url="https://example.com/product/espresso#rev-shipping",
                        source_type="crawler",
                        rating=2.0,
                        content="Shipping was slow and the box arrived cracked.",
                    ),
                    Review(
                        product_id=product.id,
                        task_id="tsk_search_001",
                        external_id="rev-positive",
                        source_url="https://example.com/product/espresso#rev-positive",
                        source_type="crawler",
                        rating=5.0,
                        content="The machine was convenient for travel.",
                    ),
                ]
            )

    provider = DeterministicEmbeddingProvider(dimensions=1536)
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    store.index_task_reviews(task_id="tsk_search_001", embedding_provider=provider)


def build_executor(session_factory) -> ToolExecutor:
    provider = DeterministicEmbeddingProvider(
        dimensions=1536,
        model_name="fake-embedding-v1",
    )
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    registry = build_default_tool_registry(
        review_chunk_store=store,
        embedding_provider=provider,
    )
    return ToolExecutor(registry)


def test_default_registry_can_register_search_reviews_tool_with_dependencies() -> None:
    session_factory = build_session_factory()
    provider = DeterministicEmbeddingProvider(dimensions=1536, model_name="fake-embedding-v1")
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )

    registry = build_default_tool_registry(
        review_chunk_store=store,
        embedding_provider=provider,
    )

    manifest = registry.get_manifest("search_reviews_tool")
    assert manifest.name == "search_reviews_tool"
    assert manifest.input_schema == "SearchReviewsToolInput"
    assert manifest.output_schema == "SearchReviewsToolOutput"


def test_search_reviews_tool_returns_evidence_chunks_for_query() -> None:
    session_factory = build_session_factory()
    seed_indexed_reviews(session_factory)
    executor = build_executor(session_factory)

    result = executor.execute(
        "search_reviews_tool",
        {
            "task_id": "tsk_search_001",
            "query": "return support",
            "top_k": 2,
            "min_similarity": 0.0,
            "filters": {"rating_lte": 2.0},
        },
        context=ToolInvocationContext(task_id="tsk_search_001", trace_id="trc_search_001"),
    )

    assert result.success is True
    assert result.data is not None
    assert result.data["no_results_reason"] is None
    assert result.data["results"][0]["review_external_id"] == "rev-return"
    assert "Return" in result.data["results"][0]["content"]
    assert result.data["results"][0]["evidence_ref"].startswith("chunk:")
    assert "chunk:" in result.data["evidence_refs"][0]


def test_search_reviews_tool_returns_empty_result_without_fabricating_evidence() -> None:
    session_factory = build_session_factory()
    seed_indexed_reviews(session_factory)
    executor = build_executor(session_factory)

    result = executor.execute(
        "search_reviews_tool",
        {
            "task_id": "tsk_search_001",
            "query": "return support",
            "top_k": 3,
            "min_similarity": 1.0,
        },
        context=ToolInvocationContext(task_id="tsk_search_001", trace_id="trc_search_001"),
    )

    assert result.success is True
    assert result.data is not None
    assert result.data["results"] == []
    assert result.data["evidence_refs"] == []
    assert result.data["no_results_reason"] == "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD"
