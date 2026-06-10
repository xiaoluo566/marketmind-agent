from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.agent.guardrails import StructuredOutputGuardrail, StructuredOutputGuardrailError
from app.reporting.generator import ReportGenerationInput, StructuredReportGenerator
from app.reporting.schemas import StructuredReport

REPORT_PROMPT_VERSION = "report.evidence_chain.v1"


class LLMReportClient(Protocol):
    def complete(self, prompt: str) -> str: ...

    def repair(self, prompt: str) -> str: ...


@dataclass(frozen=True, slots=True)
class ReportPromptBundle:
    prompt_version: str
    system_prompt: str
    developer_prompt: str
    evidence_context: str
    output_contract: str

    def to_prompt(self) -> str:
        return "\n\n".join(
            [
                f"[system]\n{self.system_prompt}",
                f"[developer]\n{self.developer_prompt}",
                f"[evidence]\n{self.evidence_context}",
                f"[output]\n{self.output_contract}",
            ]
        )


@dataclass(frozen=True, slots=True)
class LLMReportGenerationResult:
    report: StructuredReport
    prompt_version: str
    model_provider: str
    model_name: str
    fallback_used: bool
    validation_error_count: int
    self_heal_count: int
    raw_output: str | None = None
    repaired_output: str | None = None


class LLMStructuredReportGenerator:
    def __init__(
        self,
        *,
        client: LLMReportClient,
        provider_name: str,
        model_name: str,
        prompt_version: str = REPORT_PROMPT_VERSION,
        fallback_generator: StructuredReportGenerator | None = None,
        guardrail: StructuredOutputGuardrail | None = None,
    ) -> None:
        self._client = client
        self._provider_name = provider_name
        self._model_name = model_name
        self._prompt_version = prompt_version
        self._fallback_generator = fallback_generator or StructuredReportGenerator()
        self._guardrail = guardrail or StructuredOutputGuardrail(max_self_heal_attempts=1)

    def generate(self, payload: ReportGenerationInput) -> LLMReportGenerationResult:
        if not payload.evidence_snippets:
            report = self._fallback_generator.generate(payload)
            return self._fallback_result(
                report=report,
                fallback_reason="no_evidence_snippets",
                extra_metadata={"llm_skipped_reason": "NO_EVIDENCE_SNIPPETS"},
            )

        bundle = build_report_prompt_bundle(payload, prompt_version=self._prompt_version)
        raw_output = self._client.complete(bundle.to_prompt())
        try:
            parsed = self._guardrail.parse(
                raw_output,
                schema=StructuredReport,
                prompt_name=self._prompt_version,
                repair=self._client.repair,
            )
        except StructuredOutputGuardrailError:
            report = self._fallback_generator.generate(payload)
            return self._fallback_result(
                report=report,
                fallback_reason="structured_output_guardrail_failed",
                raw_output=raw_output,
            )

        report = _attach_llm_metadata(
            parsed.output,
            prompt_version=self._prompt_version,
            model_provider=self._provider_name,
            model_name=self._model_name,
            fallback_used=False,
        )
        return LLMReportGenerationResult(
            report=report,
            prompt_version=self._prompt_version,
            model_provider=self._provider_name,
            model_name=self._model_name,
            fallback_used=False,
            validation_error_count=parsed.validation_error_count,
            self_heal_count=parsed.self_heal_count,
            raw_output=raw_output,
            repaired_output=parsed.repaired_output,
        )

    def _fallback_result(
        self,
        *,
        report: StructuredReport,
        fallback_reason: str,
        raw_output: str | None = None,
        extra_metadata: dict | None = None,
    ) -> LLMReportGenerationResult:
        fallback_report = _attach_llm_metadata(
            report,
            prompt_version=self._prompt_version,
            model_provider=self._provider_name,
            model_name=self._model_name,
            fallback_used=True,
            extra_metadata={
                "fallback_reason": fallback_reason,
                **(extra_metadata or {}),
            },
        )
        return LLMReportGenerationResult(
            report=fallback_report,
            prompt_version=self._prompt_version,
            model_provider=self._provider_name,
            model_name=self._model_name,
            fallback_used=True,
            validation_error_count=1 if raw_output is not None else 0,
            self_heal_count=0,
            raw_output=raw_output,
            repaired_output=None,
        )


def build_report_prompt_bundle(
    payload: ReportGenerationInput,
    *,
    prompt_version: str = REPORT_PROMPT_VERSION,
) -> ReportPromptBundle:
    allowed_refs = [snippet.evidence_ref for snippet in payload.evidence_snippets]
    system_prompt = (
        "你是 MarketMind 的电商评论证据链报告生成器。"
        "你只能根据输入的评论证据组织报告，不要编造证据 ID，不要输出没有证据支撑的结论。"
    )
    developer_prompt = (
        f"Prompt version: {prompt_version}\n"
        f"Task ID: {payload.task_id}\n"
        f"Product: {payload.product_name}\n"
        f"Requested focus: {_format_list(payload.requested_focus)}\n"
        f"Allowed evidence_refs: {_format_list(allowed_refs)}\n"
        "每个 section.evidence_refs 必须来自 Allowed evidence_refs。"
    )
    evidence_context = "\n".join(
        [
            (
                f"- evidence_ref={snippet.evidence_ref}; rating={snippet.rating}; "
                f"similarity={snippet.similarity}; source={snippet.source_url or 'unknown'}; "
                f"content={snippet.content}"
            )
            for snippet in payload.evidence_snippets
        ]
    )
    output_contract = (
        "只返回 JSON，不要 Markdown。\n"
        "JSON 必须匹配 StructuredReport(report.v1)：task_id, title, summary, status, "
        "schema_version, evidence_refs, sections, metadata。\n"
        "status 只能是 draft / insufficient_evidence / failed。\n"
        "sections[*].evidence_refs 不允许出现 Allowed evidence_refs 之外的值。"
    )
    return ReportPromptBundle(
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        developer_prompt=developer_prompt,
        evidence_context=evidence_context,
        output_contract=output_contract,
    )


def _attach_llm_metadata(
    report: StructuredReport,
    *,
    prompt_version: str,
    model_provider: str,
    model_name: str,
    fallback_used: bool,
    extra_metadata: dict | None = None,
) -> StructuredReport:
    return report.model_copy(
        deep=True,
        update={
            "metadata": {
                **report.metadata,
                "prompt_version": prompt_version,
                "model_provider": model_provider,
                "model_name": model_name,
                "fallback_used": fallback_used,
                **(extra_metadata or {}),
            }
        },
    )


def _format_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)
