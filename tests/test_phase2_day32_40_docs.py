from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


DAY_TOPICS = {
    32: {
        "title": "前端失败任务重试闭环",
        "keywords": ["retry", "重试任务", "TaskProgressPanel", "POST /api/tasks/{task_id}/retry"],
    },
    33: {
        "title": "重试链路联调与恢复事件验收",
        "keywords": ["恢复事件", "waiting_retry", "task recovery resumed", "agent-browser-cli"],
    },
    34: {
        "title": "真实 embedding provider 接入设计",
        "keywords": [
            "EmbeddingProvider",
            "text-embedding-3-small",
            "fake provider",
            "provider fallback",
        ],
    },
    35: {
        "title": "RAG 检索质量与 provider 指标",
        "keywords": ["RAG 评估集", "召回质量", "provider_metrics", "LLMOps"],
    },
    36: {
        "title": "真实 LLM 报告生成 Prompt",
        "keywords": ["StructuredReport", "evidence_refs", "prompt version", "Pydantic"],
    },
    37: {
        "title": "Playwright E2E 主链路",
        "keywords": ["Playwright E2E", "新建调研", "报告详情", "证据链"],
    },
    38: {
        "title": "报告导出与证据包",
        "keywords": ["Markdown 导出", "证据包", "报告交付物", "artifact"],
    },
    39: {
        "title": "LLMOps 运营指标面板",
        "keywords": ["成本统计", "失败率", "自愈成功率", "恢复成功率"],
    },
    40: {
        "title": "第二阶段阶段验收与发布候选",
        "keywords": ["Phase 2 RC", "阶段验收", "release candidate", "回归门禁"],
    },
}


def test_day32_to_day40_docs_exist_and_are_actionable() -> None:
    required_sections = [
        "当天目标",
        "前置依赖",
        "当天交付物",
        "实施步骤",
        "测试计划",
        "验收标准",
        "风险与回退",
        "文档同步清单",
        "面试讲法",
        "建议提交",
    ]

    for day, expected in DAY_TOPICS.items():
        doc = read_project_file(f"doc/roadmap/day-{day:02d}.md")
        assert f"Day {day}" in doc
        assert expected["title"] in doc
        for section in required_sections:
            assert f"## {section}" in doc
        for keyword in expected["keywords"]:
            assert keyword in doc
        assert "development-log.md" in doc
        assert "interview-defense-dossier.md" in doc
        assert "testing-strategy.md" in doc


def test_phase2_master_plan_indexes_day32_to_day40() -> None:
    master_plan = read_project_file("doc/roadmap/phase-2-master-plan.md")
    roadmap_index = read_project_file("doc/roadmap/README.md")
    doc_index = read_project_file("doc/README.md")

    for day, expected in DAY_TOPICS.items():
        for source in [master_plan, roadmap_index, doc_index]:
            assert f"day-{day:02d}.md" in source
            assert expected["title"] in source

    assert "Day32-Day40" in master_plan
    assert "前端 retry" in master_plan
    assert "真实 embedding provider" in master_plan
    assert "真实 LLM 报告生成" in master_plan
    assert "报告导出" in master_plan
    assert "Phase 2 RC" in master_plan


def test_development_and_interview_docs_prepare_day32_to_day40_updates() -> None:
    development_log = read_project_file("doc/supporting/development-log.md")
    interview = read_project_file("doc/supporting/interview-defense-dossier.md")
    testing = read_project_file("doc/supporting/testing-strategy.md")

    for day, expected in DAY_TOPICS.items():
        for source in [development_log, interview, testing]:
            assert f"Day {day}" in source
            assert expected["title"] in source

    assert "Day32-Day40 开发前置记录" in development_log
    assert "Day32-Day40 面试讲述准备" in interview
    assert "Day32-Day40 文档契约测试边界" in testing
