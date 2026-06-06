from __future__ import annotations

from pydantic import BaseModel, Field

from app.reporting.generator import EvidenceSnippet
from app.reporting.schemas import StructuredReport

DIMENSION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "quality": (
        "quality",
        "failed",
        "failure",
        "broke",
        "broken",
        "leak",
        "leaking",
        "defect",
        "poor quality",
        "pressure",
        "pump",
    ),
    "logistics": (
        "shipping",
        "delivery",
        "late",
        "slow",
        "arrived late",
        "logistics",
    ),
    "support": (
        "support",
        "return",
        "refund",
        "service",
        "warranty",
        "ignored",
        "email",
    ),
    "price": (
        "price",
        "expensive",
        "overpriced",
        "cost",
        "cheap",
        "value",
    ),
    "packaging": (
        "box",
        "packaging",
        "package",
        "crushed",
        "wet",
        "damaged box",
    ),
    "functional_defect": (
        "button",
        "feature",
        "function",
        "useless",
        "cannot",
        "does not work",
        "not working",
    ),
}

DIMENSION_LABELS: dict[str, str] = {
    "quality": "质量风险",
    "logistics": "物流风险",
    "support": "售后风险",
    "price": "价格风险",
    "packaging": "包装风险",
    "functional_defect": "功能缺陷风险",
}


class ScorecardInput(BaseModel):
    task_id: str = Field(min_length=1)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    minimum_samples: int = Field(default=2, ge=1, le=20)
    metadata: dict = Field(default_factory=dict)


class DimensionScore(BaseModel):
    dimension: str
    label: str
    risk_score: int = Field(ge=0, le=100)
    opportunity_score: int = Field(ge=0, le=100)
    evidence_refs: list[str] = Field(default_factory=list)
    sample_size: int = Field(ge=0)
    average_rating: float | None = None
    max_similarity: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    sample_warning: str | None = None
    explanation: str
    metadata: dict = Field(default_factory=dict)


class AnalysisScorecard(BaseModel):
    task_id: str
    status: str
    overall_risk_score: int = Field(ge=0, le=100)
    overall_opportunity_score: int = Field(ge=0, le=100)
    evidence_refs: list[str] = Field(default_factory=list)
    dimensions: list[DimensionScore] = Field(default_factory=list)
    summary: str
    schema_version: str = "scorecard.v1"
    metadata: dict = Field(default_factory=dict)

    def get_dimension(self, dimension: str) -> DimensionScore | None:
        for item in self.dimensions:
            if item.dimension == dimension:
                return item
        return None


class CompetitiveRiskScorer:
    def score(self, payload: ScorecardInput) -> AnalysisScorecard:
        snippets = _dedupe_snippets(payload.evidence_snippets)
        if not snippets:
            return AnalysisScorecard(
                task_id=payload.task_id,
                status="insufficient_evidence",
                overall_risk_score=0,
                overall_opportunity_score=0,
                evidence_refs=[],
                dimensions=[],
                summary="证据不足：当前没有可用于风险和机会评分的评论证据。",
                metadata={**payload.metadata, "minimum_samples": payload.minimum_samples},
            )

        grouped = _group_by_dimension(snippets)
        dimensions = [
            _score_dimension(
                dimension=dimension,
                snippets=dimension_snippets,
                minimum_samples=payload.minimum_samples,
            )
            for dimension, dimension_snippets in grouped.items()
        ]
        dimensions.sort(key=lambda item: item.risk_score, reverse=True)
        evidence_refs = [snippet.evidence_ref for snippet in snippets]

        return AnalysisScorecard(
            task_id=payload.task_id,
            status="scored",
            overall_risk_score=_weighted_average(
                [(item.risk_score, item.sample_size) for item in dimensions]
            ),
            overall_opportunity_score=_weighted_average(
                [(item.opportunity_score, item.sample_size) for item in dimensions]
            ),
            evidence_refs=evidence_refs,
            dimensions=dimensions,
            summary=_build_scorecard_summary(dimensions),
            metadata={
                **payload.metadata,
                "minimum_samples": payload.minimum_samples,
                "scorer": "deterministic.scorecard.v1",
            },
        )


def attach_scorecard_to_report(
    report: StructuredReport,
    scorecard: AnalysisScorecard,
) -> StructuredReport:
    return report.model_copy(
        deep=True,
        update={
            "metadata": {
                **report.metadata,
                "analysis_scorecard": scorecard.model_dump(mode="json"),
            }
        },
    )


def _group_by_dimension(snippets: list[EvidenceSnippet]) -> dict[str, list[EvidenceSnippet]]:
    grouped: dict[str, list[EvidenceSnippet]] = {}
    for snippet in snippets:
        dimensions = _classify_dimensions(snippet.content)
        for dimension in dimensions:
            grouped.setdefault(dimension, []).append(snippet)
    return grouped


def _classify_dimensions(content: str) -> list[str]:
    text = content.lower()
    matched = [
        dimension
        for dimension, keywords in DIMENSION_KEYWORDS.items()
        if any(keyword in text for keyword in keywords)
    ]
    if not matched:
        return ["quality"]
    return matched


def _score_dimension(
    *,
    dimension: str,
    snippets: list[EvidenceSnippet],
    minimum_samples: int,
) -> DimensionScore:
    sample_size = len(snippets)
    ratings = [snippet.rating for snippet in snippets if snippet.rating is not None]
    average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
    max_similarity = max((snippet.similarity for snippet in snippets), default=0.0)
    base_risk = _base_risk_score(
        average_rating=average_rating,
        max_similarity=max_similarity,
        sample_size=sample_size,
    )
    confidence = min(1.0, sample_size / minimum_samples)
    adjusted_risk = round(base_risk * confidence)
    opportunity_score = _opportunity_score(adjusted_risk, confidence)
    sample_warning = "LOW_SAMPLE_SIZE" if sample_size < minimum_samples else None
    explanation = _build_dimension_explanation(
        dimension=dimension,
        sample_size=sample_size,
        minimum_samples=minimum_samples,
        average_rating=average_rating,
        risk_score=adjusted_risk,
        sample_warning=sample_warning,
    )

    return DimensionScore(
        dimension=dimension,
        label=DIMENSION_LABELS.get(dimension, dimension),
        risk_score=adjusted_risk,
        opportunity_score=opportunity_score,
        evidence_refs=[snippet.evidence_ref for snippet in snippets],
        sample_size=sample_size,
        average_rating=average_rating,
        max_similarity=round(max_similarity, 4),
        confidence=round(confidence, 4),
        sample_warning=sample_warning,
        explanation=explanation,
        metadata={
            "keywords": DIMENSION_KEYWORDS.get(dimension, ()),
            "minimum_samples": minimum_samples,
        },
    )


def _base_risk_score(
    *,
    average_rating: float | None,
    max_similarity: float,
    sample_size: int,
) -> int:
    if average_rating is None:
        rating_risk = 45
    else:
        rating_risk = round((5 - average_rating) / 4 * 100)
    similarity_boost = round(max_similarity * 15)
    sample_boost = min(15, sample_size * 5)
    return _clamp(rating_risk + similarity_boost + sample_boost)


def _opportunity_score(risk_score: int, confidence: float) -> int:
    if risk_score == 0:
        return 0
    return _clamp(round((risk_score * 0.75) + (confidence * 20)))


def _build_dimension_explanation(
    *,
    dimension: str,
    sample_size: int,
    minimum_samples: int,
    average_rating: float | None,
    risk_score: int,
    sample_warning: str | None,
) -> str:
    rating_text = "缺少评分" if average_rating is None else f"平均评分 {average_rating}"
    warning_text = ""
    if sample_warning:
        warning_text = f" 样本不足：当前 {sample_size} 条，低于阈值 {minimum_samples} 条，已降权。"
    return (
        f"{DIMENSION_LABELS.get(dimension, dimension)}({dimension}) 基于 {sample_size} 条证据，"
        f"{rating_text}，风险分 {risk_score}。{warning_text}"
    ).strip()


def _build_scorecard_summary(dimensions: list[DimensionScore]) -> str:
    if not dimensions:
        return "证据不足：没有形成可评分维度。"
    top = dimensions[0]
    return (
        f"最高风险维度是 {top.label}，风险分 {top.risk_score}，"
        f"基于 {top.sample_size} 条证据。评分用于排序和解释，不代表严格商业预测。"
    )


def _weighted_average(scores: list[tuple[int, int]]) -> int:
    weighted_sum = sum(score * max(1, weight) for score, weight in scores)
    total_weight = sum(max(1, weight) for _, weight in scores)
    if total_weight == 0:
        return 0
    return _clamp(round(weighted_sum / total_weight))


def _dedupe_snippets(snippets: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
    seen: set[str] = set()
    deduped: list[EvidenceSnippet] = []
    for snippet in snippets:
        if snippet.evidence_ref in seen:
            continue
        seen.add(snippet.evidence_ref)
        deduped.append(snippet)
    return deduped


def _clamp(value: int) -> int:
    return max(0, min(100, value))
