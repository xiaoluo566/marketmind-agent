from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from app.rag.embeddings import EmbeddingProvider, EmbeddingProviderError
from app.rag.review_index import SQLAlchemyReviewChunkStore


@dataclass(frozen=True, slots=True)
class ProviderMetric:
    provider_name: str
    model_name: str
    operation: str
    input_count: int
    input_characters: int
    latency_ms: int
    success: bool
    error_code: str | None = None
    fallback_used: bool = False


@dataclass(frozen=True, slots=True)
class ProviderMetricsSummary:
    total_calls: int
    success_count: int
    failure_count: int
    fallback_count: int
    total_input_characters: int
    average_latency_ms: int
    error_counts: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RAGEvaluationCase:
    query: str
    expected_review_external_ids: list[str]
    top_k: int = 5
    min_similarity: float = 0.0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RAGEvaluationResult:
    query: str
    expected_review_external_ids: list[str]
    returned_review_external_ids: list[str]
    hit_count: int
    expected_count: int
    hit_rate: float
    top_similarity: float
    latency_ms: int
    empty_recall: bool
    matched: bool
    reason: str


@dataclass(frozen=True, slots=True)
class RAGEvaluationSummary:
    total_cases: int
    passed_cases: int
    empty_recall_count: int
    micro_hit_rate: float
    average_case_hit_rate: float
    average_latency_ms: int
    results: list[RAGEvaluationResult]
    provider_metrics: list[ProviderMetric]
    provider_metrics_summary: ProviderMetricsSummary


class InstrumentedEmbeddingProvider:
    def __init__(
        self,
        provider: EmbeddingProvider,
        *,
        provider_name: str,
        operation: str = "embedding",
        fallback_used: bool = False,
    ) -> None:
        self._provider = provider
        self.provider_name = provider_name
        self.operation = operation
        self.fallback_used = fallback_used
        self.dimensions = provider.dimensions
        self.model_name = provider.model_name
        self.metrics: list[ProviderMetric] = []

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        started_at = perf_counter()
        try:
            vectors = self._provider.embed_texts(texts)
        except EmbeddingProviderError as exc:
            self.metrics.append(
                self._build_metric(
                    texts=texts,
                    started_at=started_at,
                    success=False,
                    error_code=exc.code,
                )
            )
            raise
        except Exception:
            self.metrics.append(
                self._build_metric(
                    texts=texts,
                    started_at=started_at,
                    success=False,
                    error_code="EMBEDDING_PROVIDER_UNKNOWN_ERROR",
                )
            )
            raise

        self.metrics.append(
            self._build_metric(
                texts=texts,
                started_at=started_at,
                success=True,
                error_code=None,
            )
        )
        return vectors

    def _build_metric(
        self,
        *,
        texts: list[str],
        started_at: float,
        success: bool,
        error_code: str | None,
    ) -> ProviderMetric:
        return ProviderMetric(
            provider_name=self.provider_name,
            model_name=self.model_name,
            operation=self.operation,
            input_count=len(texts),
            input_characters=sum(len(text) for text in texts),
            latency_ms=_duration_ms(started_at),
            success=success,
            error_code=error_code,
            fallback_used=self.fallback_used,
        )


def evaluate_rag_quality(
    *,
    store: SQLAlchemyReviewChunkStore,
    embedding_provider: EmbeddingProvider,
    task_id: str,
    cases: list[RAGEvaluationCase],
) -> RAGEvaluationSummary:
    results: list[RAGEvaluationResult] = []
    provider_metric_start = len(getattr(embedding_provider, "metrics", []))
    for case in cases:
        started_at = perf_counter()
        raw_results = store.search_similar_reviews(
            task_id=task_id,
            query=case.query,
            embedding_provider=embedding_provider,
            top_k=case.top_k,
        )
        filtered_results = [
            result for result in raw_results if result.similarity >= case.min_similarity
        ]
        returned_ids = [
            result.review_external_id
            for result in filtered_results
            if result.review_external_id is not None
        ]
        expected_ids = set(case.expected_review_external_ids)
        hit_count = len(expected_ids.intersection(returned_ids))
        expected_count = len(expected_ids)
        hit_rate = hit_count / expected_count if expected_count else 0.0
        results.append(
            RAGEvaluationResult(
                query=case.query,
                expected_review_external_ids=case.expected_review_external_ids,
                returned_review_external_ids=returned_ids,
                hit_count=hit_count,
                expected_count=expected_count,
                hit_rate=hit_rate,
                top_similarity=filtered_results[0].similarity if filtered_results else 0.0,
                latency_ms=_duration_ms(started_at),
                empty_recall=len(filtered_results) == 0,
                matched=hit_count == expected_count and expected_count > 0,
                reason=case.reason,
            )
        )

    provider_metrics = list(getattr(embedding_provider, "metrics", [])[provider_metric_start:])
    return RAGEvaluationSummary(
        total_cases=len(cases),
        passed_cases=sum(1 for result in results if result.matched),
        empty_recall_count=sum(1 for result in results if result.empty_recall),
        micro_hit_rate=_micro_hit_rate(results),
        average_case_hit_rate=_average_case_hit_rate(results),
        average_latency_ms=_average_latency_ms([result.latency_ms for result in results]),
        results=results,
        provider_metrics=provider_metrics,
        provider_metrics_summary=summarize_provider_metrics(provider_metrics),
    )


def summarize_provider_metrics(metrics: list[ProviderMetric]) -> ProviderMetricsSummary:
    error_counts: dict[str, int] = {}
    for metric in metrics:
        if metric.error_code is None:
            continue
        error_counts[metric.error_code] = error_counts.get(metric.error_code, 0) + 1
    return ProviderMetricsSummary(
        total_calls=len(metrics),
        success_count=sum(1 for metric in metrics if metric.success),
        failure_count=sum(1 for metric in metrics if not metric.success),
        fallback_count=sum(1 for metric in metrics if metric.fallback_used),
        total_input_characters=sum(metric.input_characters for metric in metrics),
        average_latency_ms=_average_latency_ms([metric.latency_ms for metric in metrics]),
        error_counts=error_counts,
    )


def _micro_hit_rate(results: list[RAGEvaluationResult]) -> float:
    expected_total = sum(result.expected_count for result in results)
    if expected_total == 0:
        return 0.0
    return round(sum(result.hit_count for result in results) / expected_total, 4)


def _average_case_hit_rate(results: list[RAGEvaluationResult]) -> float:
    if not results:
        return 0.0
    return round(sum(result.hit_rate for result in results) / len(results), 4)


def _average_latency_ms(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _duration_ms(started_at: float) -> int:
    return max(0, int((perf_counter() - started_at) * 1000))
