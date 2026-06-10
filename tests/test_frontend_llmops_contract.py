from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"


def read_frontend(relative_path: str) -> str:
    path = FRONTEND_SRC / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_frontend_exposes_llmops_summary_api_and_types() -> None:
    api_source = read_frontend("lib/api.ts")
    types_source = read_frontend("lib/types.ts")
    mock_data = read_frontend("lib/mock-data.ts")

    assert "export async function getLLMOpsSummary" in api_source
    assert "/api/observability/llmops-summary" in api_source
    assert "llmopsSummary" in api_source
    assert "export const llmopsSummary" in mock_data

    for expected_type in [
        "export type LLMOpsSummary",
        "summary_version",
        "task_metrics",
        "model_usage",
        "guardrail_metrics",
        "recovery_metrics",
        "provider_metrics",
    ]:
        assert expected_type in types_source


def test_dashboard_renders_chinese_llmops_metrics_without_hiding_data_source() -> None:
    dashboard = read_frontend("app/page.tsx")

    assert "getLLMOpsSummary" in dashboard
    assert "LLMOps 指标" in dashboard
    assert "模型调用" in dashboard
    assert "Token 总量" in dashboard
    assert "结构化解析失败" in dashboard
    assert "自愈成功率" in dashboard
    assert "恢复成功率" in dashboard
    assert "数据来源" in dashboard
    assert "llmopsSummary.warnings" in dashboard
