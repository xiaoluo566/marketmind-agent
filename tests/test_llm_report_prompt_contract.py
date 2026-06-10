import json

from app.reporting.generator import EvidenceSnippet, ReportGenerationInput
from app.reporting.llm_prompt import (
    LLMReportClient,
    LLMStructuredReportGenerator,
    build_report_prompt_bundle,
)


def build_report_input() -> ReportGenerationInput:
    return ReportGenerationInput(
        task_id="tsk_llm_report_001",
        product_name="Portable Espresso Maker",
        observations=["Crawler extracted low-rating reviews and RAG returned evidence chunks."],
        evidence_snippets=[
            EvidenceSnippet(
                evidence_ref="chunk:chk_return",
                content="The pump failed after three days and support ignored the return request.",
                similarity=0.88,
                rating=1.0,
                source_url="https://example.com/product#return",
            ),
            EvidenceSnippet(
                evidence_ref="chunk:chk_shipping",
                content="Shipping was slow and the box arrived cracked.",
                similarity=0.72,
                rating=2.0,
                source_url="https://example.com/product#shipping",
            ),
        ],
        requested_focus=["return support", "logistics"],
    )


def test_report_prompt_bundle_contains_evidence_refs_and_schema_constraints() -> None:
    bundle = build_report_prompt_bundle(build_report_input())

    prompt_text = "\n".join(
        [
            bundle.system_prompt,
            bundle.developer_prompt,
            bundle.evidence_context,
            bundle.output_contract,
        ]
    )

    assert bundle.prompt_version == "report.evidence_chain.v1"
    assert "StructuredReport" in prompt_text
    assert "chunk:chk_return" in prompt_text
    assert "chunk:chk_shipping" in prompt_text
    assert "不要编造证据 ID" in prompt_text
    assert "evidence_refs" in prompt_text


def test_llm_report_generator_self_heals_bad_json_and_records_prompt_metadata() -> None:
    client = FakeLLMReportClient(
        raw_outputs=["not-json"],
        repairs=[build_valid_report_json(summary="修复后的报告摘要。")],
    )
    generator = LLMStructuredReportGenerator(
        client=client,
        provider_name="openai-compatible",
        model_name="gpt-5.5",
    )

    result = generator.generate(build_report_input())

    assert result.report.summary == "修复后的报告摘要。"
    assert result.report.metadata["prompt_version"] == "report.evidence_chain.v1"
    assert result.report.metadata["model_name"] == "gpt-5.5"
    assert result.report.metadata["model_provider"] == "openai-compatible"
    assert result.report.metadata["fallback_used"] is False
    assert result.validation_error_count == 1
    assert result.self_heal_count == 1
    assert client.repair_prompts
    assert "StructuredReport" in client.repair_prompts[0]


def test_llm_report_generator_falls_back_when_repair_cannot_produce_valid_report() -> None:
    client = FakeLLMReportClient(
        raw_outputs=[
            json.dumps(
                {
                    "task_id": "tsk_llm_report_001",
                    "title": "Bad evidence report",
                    "summary": "This report invents evidence.",
                    "evidence_refs": ["chunk:chk_return"],
                    "sections": [
                        {
                            "section_id": "risk",
                            "heading": "Risk",
                            "claim": "Invented claim.",
                            "evidence_refs": ["chunk:not_allowed"],
                            "severity": "high",
                        }
                    ],
                }
            )
        ],
        repairs=["{\"still\":\"invalid\"}"],
    )
    generator = LLMStructuredReportGenerator(
        client=client,
        provider_name="openai-compatible",
        model_name="gpt-5.5",
    )

    result = generator.generate(build_report_input())

    assert result.fallback_used is True
    assert result.report.metadata["fallback_used"] is True
    assert result.report.metadata["fallback_reason"] == "structured_output_guardrail_failed"
    assert result.report.metadata["prompt_version"] == "report.evidence_chain.v1"
    assert set(result.report.evidence_refs) == {"chunk:chk_return", "chunk:chk_shipping"}
    assert all(
        set(section.evidence_refs).issubset(set(result.report.evidence_refs))
        for section in result.report.sections
    )


def test_llm_report_generator_skips_llm_without_evidence() -> None:
    client = FakeLLMReportClient(raw_outputs=[build_valid_report_json()])
    generator = LLMStructuredReportGenerator(
        client=client,
        provider_name="openai-compatible",
        model_name="gpt-5.5",
    )
    payload = ReportGenerationInput(
        task_id="tsk_empty_evidence",
        product_name="Portable Espresso Maker",
        evidence_snippets=[],
        requested_focus=["quality risk"],
    )

    result = generator.generate(payload)

    assert result.report.status == "insufficient_evidence"
    assert result.report.evidence_refs == []
    assert result.fallback_used is True
    assert result.report.metadata["llm_skipped_reason"] == "NO_EVIDENCE_SNIPPETS"
    assert client.raw_prompt_calls == []


def build_valid_report_json(*, summary: str = "LLM report summary.") -> str:
    return json.dumps(
        {
            "task_id": "tsk_llm_report_001",
            "title": "Portable Espresso Maker 证据链报告",
            "summary": summary,
            "evidence_refs": ["chunk:chk_return", "chunk:chk_shipping"],
            "status": "draft",
            "schema_version": "report.v1",
            "sections": [
                {
                    "section_id": "customer_pain_points",
                    "heading": "用户痛点",
                    "claim": "退货售后和物流破损是主要风险。",
                    "evidence_refs": ["chunk:chk_return", "chunk:chk_shipping"],
                    "severity": "high",
                    "recommendation": "优先验证售后和物流体验改进。",
                }
            ],
            "metadata": {},
        }
    )


class FakeLLMReportClient(LLMReportClient):
    def __init__(self, *, raw_outputs: list[str], repairs: list[str] | None = None) -> None:
        self._raw_outputs = list(raw_outputs)
        self._repairs = list(repairs or [])
        self.raw_prompt_calls: list[str] = []
        self.repair_prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.raw_prompt_calls.append(prompt)
        return self._raw_outputs.pop(0)

    def repair(self, prompt: str) -> str:
        self.repair_prompts.append(prompt)
        return self._repairs.pop(0)
