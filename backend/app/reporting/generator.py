from __future__ import annotations

from pydantic import BaseModel, Field

from app.reporting.schemas import ReportFinding, StructuredReport


class EvidenceSnippet(BaseModel):
    evidence_ref: str = Field(min_length=1)
    content: str = Field(min_length=1)
    similarity: float = Field(default=0.0, ge=0, le=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    source_url: str | None = None
    metadata: dict = Field(default_factory=dict)


class ReportGenerationInput(BaseModel):
    task_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    observations: list[str] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    requested_focus: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class StructuredReportGenerator:
    def generate(self, payload: ReportGenerationInput) -> StructuredReport:
        evidence_snippets = _dedupe_snippets(payload.evidence_snippets)
        if not evidence_snippets:
            return self._build_insufficient_report(payload)

        evidence_refs = [snippet.evidence_ref for snippet in evidence_snippets]
        focus_text = _join_or_default(payload.requested_focus, "评论痛点、风险和机会")
        summary = (
            f"基于 {len(evidence_snippets)} 条可引用评论证据，"
            f"{payload.product_name} 当前需要重点关注：{focus_text}。"
        )
        return StructuredReport(
            task_id=payload.task_id,
            title=f"{payload.product_name} 证据链分析报告",
            status="draft",
            summary=summary,
            evidence_refs=evidence_refs,
            sections=[
                self._build_pain_point_section(evidence_snippets),
                self._build_risk_section(evidence_snippets),
                self._build_opportunity_section(evidence_snippets, payload.requested_focus),
            ],
            metadata={
                **payload.metadata,
                "observations": payload.observations,
                "requested_focus": payload.requested_focus,
                "evidence_snippets": [
                    snippet.model_dump(mode="json") for snippet in evidence_snippets
                ],
                "generator": "deterministic.report.v1",
            },
        )

    def _build_insufficient_report(self, payload: ReportGenerationInput) -> StructuredReport:
        focus_text = _join_or_default(payload.requested_focus, "目标问题")
        return StructuredReport(
            task_id=payload.task_id,
            title=f"{payload.product_name} 证据链分析报告",
            status="insufficient_evidence",
            summary=f"当前没有足够评论证据支撑对 {payload.product_name} 的结论。",
            evidence_refs=[],
            sections=[
                ReportFinding(
                    section_id="insufficient_evidence",
                    heading="证据状态",
                    claim=(
                        f"证据不足：当前没有召回可引用的评论片段，"
                        f"不能对 {focus_text} 下确定结论。"
                    ),
                    evidence_refs=[],
                    severity="medium",
                    recommendation="回到 RAG 检索或采集阶段补充评论证据后再生成报告。",
                )
            ],
            metadata={
                **payload.metadata,
                "observations": payload.observations,
                "requested_focus": payload.requested_focus,
                "generator": "deterministic.report.v1",
            },
        )

    def _build_pain_point_section(
        self,
        evidence_snippets: list[EvidenceSnippet],
    ) -> ReportFinding:
        strongest = evidence_snippets[0]
        return ReportFinding(
            section_id="customer_pain_points",
            heading="用户痛点",
            claim=(
                "最高相关证据显示用户痛点集中在："
                f"{_compact_text(strongest.content)}"
            ),
            evidence_refs=[strongest.evidence_ref],
            severity=_severity_from_rating(strongest.rating),
            recommendation="优先把该痛点拆成可验证的产品改进假设。",
        )

    def _build_risk_section(self, evidence_snippets: list[EvidenceSnippet]) -> ReportFinding:
        risky_refs = [
            snippet.evidence_ref
            for snippet in evidence_snippets
            if snippet.rating is not None and snippet.rating <= 2.0
        ] or [snippet.evidence_ref for snippet in evidence_snippets]
        worst = min(
            (snippet.rating for snippet in evidence_snippets if snippet.rating is not None),
            default=None,
        )
        risk_label = "低分评论" if worst is not None and worst <= 2.0 else "相关评论"
        return ReportFinding(
            section_id="risk_assessment",
            heading="风险判断",
            claim=(
                f"{risk_label} 已形成可追溯证据集合，"
                "报告结论必须围绕这些 evidence refs 展开。"
            ),
            evidence_refs=risky_refs,
            severity="high" if worst is not None and worst <= 2.0 else "medium",
            recommendation="进入后续机会评分前，先确认该风险是否属于可修复缺陷。",
        )

    def _build_opportunity_section(
        self,
        evidence_snippets: list[EvidenceSnippet],
        requested_focus: list[str],
    ) -> ReportFinding:
        evidence_refs = [snippet.evidence_ref for snippet in evidence_snippets[:2]]
        focus_text = _join_or_default(requested_focus, "已召回痛点")
        return ReportFinding(
            section_id="opportunity_notes",
            heading="机会判断",
            claim=(
                f"如果能够针对 {focus_text} 提供明确改进，"
                "这些差评可以转化为产品定位和卖点验证材料。"
            ),
            evidence_refs=evidence_refs,
            severity="medium",
            recommendation="后续 Day 18 再加入量化评分，不在 Day 16 直接给商业结论。",
        )


def _dedupe_snippets(snippets: list[EvidenceSnippet]) -> list[EvidenceSnippet]:
    seen: set[str] = set()
    deduped: list[EvidenceSnippet] = []
    for snippet in snippets:
        if snippet.evidence_ref in seen:
            continue
        seen.add(snippet.evidence_ref)
        deduped.append(snippet)
    return sorted(deduped, key=lambda snippet: snippet.similarity, reverse=True)


def _compact_text(value: str, max_length: int = 180) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."


def _join_or_default(values: list[str], default: str) -> str:
    normalized = [value.strip() for value in values if value.strip()]
    if not normalized:
        return default
    return "、".join(normalized)


def _severity_from_rating(rating: float | None) -> str:
    if rating is None:
        return "medium"
    if rating <= 2.0:
        return "high"
    if rating <= 3.0:
        return "medium"
    return "low"
