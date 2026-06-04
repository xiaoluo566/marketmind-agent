from datetime import UTC, datetime

from app.api.schemas.tasks import TaskStatusData
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.review_index import SQLAlchemyReviewChunkStore
from app.rag.text import clean_review_text, split_review_text
from app.storage.base import Base
from app.storage.models import Product, Project, Review, ReviewChunk, Task, User
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
            Review.__table__,
            ReviewChunk.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_task(session_factory, *, task_id: str = "tsk_rag_001") -> None:
    now = datetime(2026, 5, 25, 12, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status="completed",
            trace_id="trc_rag_001",
            target="demo://portable-espresso-maker-negative-reviews",
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def seed_reviews(session_factory, *, task_id: str = "tsk_rag_001") -> None:
    with session_factory() as session:
        with session.begin():
            product = Product(
                task_id=task_id,
                title="Portable Espresso Maker",
                source_url="https://example.com/product/espresso",
            )
            session.add(product)
            session.flush()
            session.add_all(
                [
                    Review(
                        product_id=product.id,
                        task_id=task_id,
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
                        task_id=task_id,
                        external_id="rev-shipping",
                        source_url="https://example.com/product/espresso#rev-shipping",
                        source_type="crawler",
                        rating=2.0,
                        content=(
                            "The package was thin, shipping was slow, "
                            "and the shell arrived cracked."
                        ),
                    ),
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev-positive",
                        source_url="https://example.com/product/espresso#rev-positive",
                        source_type="crawler",
                        rating=5.0,
                        content="The coffee tasted good and the machine was convenient for travel.",
                    ),
                ]
            )


def test_clean_review_text_removes_markup_scripts_and_redundant_space() -> None:
    raw = "  <div>物流&nbsp;很慢</div><script>alert(1)</script>\n\n售后   拖延  "

    assert clean_review_text(raw) == "物流 很慢 售后 拖延"


def test_split_review_text_keeps_sentence_boundaries_and_metadata() -> None:
    text = "Pump failed. Return denied. Box cracked."

    chunks = split_review_text(text, max_chars=14)

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.content for chunk in chunks] == [
        "Pump failed.",
        "Return denied.",
        "Box cracked.",
    ]


def test_deterministic_embedding_provider_is_stable_and_dimensioned() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=16)

    first = provider.embed_texts(["退货 售后"])[0]
    second = provider.embed_texts(["退货 售后"])[0]

    assert first == second
    assert len(first) == 16
    assert sum(abs(value) for value in first) > 0


def test_review_chunk_store_indexes_reviews_idempotently() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    seed_reviews(session_factory)
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    provider = DeterministicEmbeddingProvider(dimensions=1536)

    first = store.index_task_reviews(task_id="tsk_rag_001", embedding_provider=provider)
    second = store.index_task_reviews(task_id="tsk_rag_001", embedding_provider=provider)

    assert first.review_count == 3
    assert first.chunk_count == 3
    assert second.review_count == 3
    assert second.chunk_count == 3
    with session_factory() as session:
        chunks = session.scalars(select(ReviewChunk)).all()

    assert len(chunks) == 3
    assert {chunk.embedding_model for chunk in chunks} == {"fake-embedding-v1"}
    assert {chunk.embedding_dimensions for chunk in chunks} == {1536}
    assert all(chunk.embedding is not None for chunk in chunks)


def test_review_chunk_store_returns_top_k_with_review_source_and_similarity() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    seed_reviews(session_factory)
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    provider = DeterministicEmbeddingProvider(dimensions=1536)
    store.index_task_reviews(task_id="tsk_rag_001", embedding_provider=provider)

    results = store.search_similar_reviews(
        task_id="tsk_rag_001",
        query="return support",
        embedding_provider=provider,
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].review_external_id == "rev-return"
    assert "Return" in results[0].content
    assert results[0].source_url == "https://example.com/product/espresso#rev-return"
    assert results[0].rating == 1.0
    assert 0 <= results[0].similarity <= 1
