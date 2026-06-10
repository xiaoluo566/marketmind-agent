from datetime import UTC, datetime

import pytest
from app.api.schemas.tasks import TaskStatusData
from app.rag.embeddings import (
    EMBEDDING_PROVIDER_TIMEOUT,
    DeterministicEmbeddingProvider,
    EmbeddingProviderError,
)
from app.rag.quality import (
    InstrumentedEmbeddingProvider,
    RAGEvaluationCase,
    evaluate_rag_quality,
    summarize_provider_metrics,
)
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


def seed_rag_eval_reviews(session_factory, *, task_id: str = "tsk_rag_eval_001") -> None:
    now = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status="completed",
            trace_id="trc_rag_eval_001",
            target="demo://rag-quality-eval",
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
                task_id=task_id,
                title="Outdoor Power Bank",
                source_url="https://example.com/products/power-bank",
            )
            session.add(product)
            session.flush()
            session.add_all(
                [
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev_quality",
                        source_type="crawler",
                        rating=1.0,
                        content="质量差，外壳松动，充电口用了三天就坏了。",
                    ),
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev_return",
                        source_type="crawler",
                        rating=1.0,
                        content="申请退货一直没人处理，售后流程很慢。",
                    ),
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev_logistics",
                        source_type="crawler",
                        rating=2.0,
                        content="物流慢，包装盒压坏，到货时配件散落。",
                    ),
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev_support",
                        source_type="crawler",
                        rating=2.0,
                        content="客服差，问了三次都没有解决问题。",
                    ),
                    Review(
                        product_id=product.id,
                        task_id=task_id,
                        external_id="rev_battery",
                        source_type="crawler",
                        rating=2.0,
                        content="续航短，满电只能用两个小时。",
                    ),
                ]
            )


def build_eval_cases() -> list[RAGEvaluationCase]:
    return [
        RAGEvaluationCase(
            query="质量差",
            expected_review_external_ids=["rev_quality"],
            reason="质量问题应召回外壳和充电口故障差评。",
        ),
        RAGEvaluationCase(
            query="退货",
            expected_review_external_ids=["rev_return"],
            reason="退货问题应召回售后流程差评。",
        ),
        RAGEvaluationCase(
            query="物流慢",
            expected_review_external_ids=["rev_logistics"],
            reason="物流慢应召回到货和包装损坏差评。",
        ),
        RAGEvaluationCase(
            query="客服差",
            expected_review_external_ids=["rev_support"],
            reason="客服差应召回客服未解决问题的差评。",
        ),
        RAGEvaluationCase(
            query="续航短",
            expected_review_external_ids=["rev_battery"],
            reason="续航短应召回电量使用时间差评。",
        ),
    ]


def test_rag_quality_evaluation_reports_expected_evidence_hits() -> None:
    session_factory = build_session_factory()
    seed_rag_eval_reviews(session_factory)
    provider = InstrumentedEmbeddingProvider(
        DeterministicEmbeddingProvider(dimensions=1536, model_name="fake-embedding-v1"),
        provider_name="fake",
    )
    store = SQLAlchemyReviewChunkStore(
        session_factory=session_factory,
        embedding_model="fake-embedding-v1",
        embedding_dimensions=1536,
    )
    store.index_task_reviews(task_id="tsk_rag_eval_001", embedding_provider=provider)

    summary = evaluate_rag_quality(
        store=store,
        embedding_provider=provider,
        task_id="tsk_rag_eval_001",
        cases=build_eval_cases(),
    )

    assert summary.total_cases == 5
    assert summary.passed_cases == 5
    assert summary.empty_recall_count == 0
    assert summary.micro_hit_rate == 1.0
    assert all(result.matched for result in summary.results)
    assert all(result.expected_review_external_ids for result in summary.results)
    assert provider.metrics
    assert all(metric.success for metric in provider.metrics)


def test_provider_metrics_summary_counts_success_failure_and_fallback() -> None:
    successful_provider = InstrumentedEmbeddingProvider(
        DeterministicEmbeddingProvider(dimensions=8, model_name="fake-embedding-v1"),
        provider_name="fake",
        fallback_used=True,
    )
    successful_provider.embed_texts(["质量差", "物流慢"])

    failing_provider = InstrumentedEmbeddingProvider(
        TimeoutEmbeddingProvider(),
        provider_name="openai-compatible",
    )
    with pytest.raises(EmbeddingProviderError):
        failing_provider.embed_texts(["退货"])

    summary = summarize_provider_metrics(
        [*successful_provider.metrics, *failing_provider.metrics]
    )

    assert summary.total_calls == 2
    assert summary.success_count == 1
    assert summary.failure_count == 1
    assert summary.fallback_count == 1
    assert summary.error_counts == {EMBEDDING_PROVIDER_TIMEOUT: 1}
    assert summary.total_input_characters == len("质量差物流慢退货")


class TimeoutEmbeddingProvider:
    dimensions = 8
    model_name = "timeout-embedding"

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingProviderError(
            code=EMBEDDING_PROVIDER_TIMEOUT,
            message="embedding provider timeout",
        )
