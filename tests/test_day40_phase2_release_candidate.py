from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_phase2_roadmap_contains_sdd_and_actual_gate_results() -> None:
    roadmap = read_project_file("doc/roadmap/day-40.md")

    assert "## SDD 规格" in roadmap
    assert "v0.2-phase2-rc1" in roadmap
    assert "Day31-Day39" in roadmap
    assert "不声明 v1.0" in roadmap
    assert "next/font/google" in roadmap
    assert "真实应用闭环" in roadmap
    assert "CSV/JSON 评论导入" in roadmap


def test_phase2_release_candidate_doc_records_scope_boundaries_and_merge_decision() -> None:
    release_candidate = read_project_file("doc/supporting/phase-2-release-candidate.md")

    assert "v0.2-phase2-rc1" in release_candidate
    assert "Phase 2 RC" in release_candidate
    assert "Day31-Day39" in release_candidate
    assert "main 合并判断" in release_candidate
    assert "不声明 v1.0" in release_candidate
    assert "不声明真实生产数据" in release_candidate
    assert "Docker Compose 真实 build/up" in release_candidate
    assert "真实 provider 成本" in release_candidate


def test_phase2_bug_summary_keeps_unfinished_items_honest() -> None:
    bug_summary = read_project_file("doc/supporting/phase-2-bug-summary.md")

    for expected_gap in [
        "Docker Compose 真实 build/up",
        "真实 provider 成本",
        "真实多容器 E2E",
        "branch protection",
        "CSV/JSON 评论导入",
        "低风险真实站点适配器",
    ]:
        assert expected_gap in bug_summary

    assert "next/font/google" in bug_summary
    assert "已修复" in bug_summary
    assert "不阻塞 Phase 2 RC" in bug_summary


def test_phase2_metrics_summary_uses_verified_commands_only() -> None:
    metrics = read_project_file("doc/supporting/phase-2-metrics-summary.md")

    for verified_command in [
        "uv run pytest",
        "uv run ruff check backend tests migrations",
        "npm run lint",
        "npm run build",
        "npm audit --audit-level=high",
    ]:
        assert verified_command in metrics

    assert "不写真实线上成本" in metrics
    assert "fixture" in metrics
    assert "mock" in metrics
    assert "database_snapshot" in metrics


def test_supporting_docs_and_readme_reference_current_project_entrypoint() -> None:
    readme = read_project_file("README.md")
    release_checklist = read_project_file("doc/supporting/release-checklist.md")
    future_iterations = read_project_file("doc/supporting/future-iterations.md")
    testing_strategy = read_project_file("doc/supporting/testing-strategy.md")
    interview = read_project_file("doc/supporting/interview-defense-dossier.md")
    development_log = read_project_file("doc/supporting/development-log.md")

    assert "doc/supporting/real-application-loop.md" in readme
    assert "phase-2-release-candidate.md" not in readme
    assert "Day 40 Phase 2 RC" in release_checklist
    assert "真实应用闭环优先级" in future_iterations
    assert "真实应用闭环" in future_iterations
    assert "Day 40 Phase 2 RC 测试边界" in testing_strategy
    assert "Day 40 第二阶段验收" in interview
    assert "Day 40 实际开发记录" in development_log
