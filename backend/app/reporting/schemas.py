from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ReportStatus = Literal["draft", "insufficient_evidence", "failed"]
FindingSeverity = Literal["low", "medium", "high"]


class ReportFinding(BaseModel):
    section_id: str = Field(min_length=1)
    heading: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    severity: FindingSeverity = "medium"
    recommendation: str | None = None
    metadata: dict = Field(default_factory=dict)


class StructuredReport(BaseModel):
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(min_length=1)
    sections: list[ReportFinding] = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    status: ReportStatus = "draft"
    schema_version: str = "report.v1"
    metadata: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_section_evidence_refs(self) -> StructuredReport:
        allowed_refs = set(self.evidence_refs)
        unknown_refs = sorted(
            {
                evidence_ref
                for section in self.sections
                for evidence_ref in section.evidence_refs
                if evidence_ref not in allowed_refs
            }
        )
        if unknown_refs:
            raise ValueError(f"unknown evidence refs: {unknown_refs}")
        return self

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            "",
            f"- 状态：`{self.status}`",
            f"- Schema：`{self.schema_version}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
        ]
        for section in self.sections:
            lines.extend(
                [
                    f"## {section.heading}",
                    "",
                    section.claim,
                    "",
                    f"- 风险等级：`{section.severity}`",
                    f"- 证据引用：{_format_evidence_refs(section.evidence_refs)}",
                ]
            )
            if section.recommendation:
                lines.append(f"- 建议动作：{section.recommendation}")
            lines.append("")

        evidence_snippets = self.metadata.get("evidence_snippets", [])
        if evidence_snippets:
            lines.extend(["## 证据摘录", ""])
            for snippet in evidence_snippets:
                lines.extend(
                    [
                        f"### {snippet.get('evidence_ref', 'unknown')}",
                        "",
                        str(snippet.get("content", "")),
                        "",
                        f"- 相似度：`{snippet.get('similarity', 'unknown')}`",
                        f"- 评分：`{snippet.get('rating', 'unknown')}`",
                        f"- 来源：{snippet.get('source_url') or 'unknown'}",
                        "",
                    ]
                )
        else:
            lines.extend(["## 证据摘录", "", "证据不足：当前没有可引用的评论证据。", ""])

        return "\n".join(lines).strip() + "\n"


def _format_evidence_refs(evidence_refs: list[str]) -> str:
    if not evidence_refs:
        return "证据不足"
    return ", ".join(f"`{evidence_ref}`" for evidence_ref in evidence_refs)
