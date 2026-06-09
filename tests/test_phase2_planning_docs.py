from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_phase2_master_plan_links_practicality_localization_and_risk_docs() -> None:
    master_plan = read_project_file("doc/roadmap/phase-2-master-plan.md")

    assert "第二阶段" in master_plan
    assert "中文界面" in master_plan
    assert "前端 retry 按钮" in master_plan
    assert "真实 compose build/up" in master_plan
    assert "真实 embedding provider" in master_plan
    assert "真实 LLM report prompt" in master_plan
    assert "Playwright E2E" in master_plan
    assert "frontend-localization-contract.md" in master_plan
    assert "phase-2-practicality-plan.md" in master_plan
    assert "phase-2-acceptance-and-risk.md" in master_plan


def test_day31_doc_is_a_localization_first_execution_manual() -> None:
    day31 = read_project_file("doc/roadmap/day-31.md")

    assert "Day 31" in day31
    assert "先文档后开发" in day31
    assert "中文界面" in day31
    assert "AppShell" in day31
    assert "Dashboard" in day31
    assert "NewResearchForm" in day31
    assert "tests/test_frontend_localization_contract.py" in day31


def test_localization_contract_defines_terms_scope_and_non_goals() -> None:
    localization = read_project_file("doc/supporting/frontend-localization-contract.md")

    assert "中文术语表" in localization
    assert "任务" in localization
    assert "报告" in localization
    assert "证据链" in localization
    assert "重试" in localization
    assert "暂不引入复杂 i18n 框架" in localization
    assert "不要翻译 API 字段名" in localization


def test_phase2_practicality_and_acceptance_docs_are_actionable() -> None:
    practicality = read_project_file("doc/supporting/phase-2-practicality-plan.md")
    acceptance = read_project_file("doc/supporting/phase-2-acceptance-and-risk.md")

    assert "用户可用性" in practicality
    assert "工程深度" in practicality
    assert "数据可信度" in practicality
    assert "前端 retry 按钮" in practicality
    assert "真实 provider" in practicality
    assert "验收门槛" in acceptance
    assert "回退策略" in acceptance
    assert "Docker daemon 不可用" in acceptance
    assert "main 只保留稳定版本" in acceptance
