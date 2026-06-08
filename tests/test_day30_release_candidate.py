from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_day30_release_candidate_doc_records_tag_scope_and_boundaries() -> None:
    release_candidate = read_project_file("doc/supporting/day30-release-candidate.md")

    assert "v0.1-day30-rc1" in release_candidate
    assert "release candidate" in release_candidate
    assert "Docker Desktop daemon" in release_candidate
    assert "不声明 v1.0" in release_candidate
    assert "GitHub Actions" in release_candidate


def test_day30_metrics_summary_uses_verified_numbers_only() -> None:
    metrics = read_project_file("doc/supporting/day30-metrics-summary.md")

    assert "168 passed" in metrics
    assert "90.77%" in metrics
    assert "20" in metrics
    assert "95.00%" in metrics
    assert "338 ms" in metrics
    assert "391 ms" in metrics
    assert "模型调用次数：0" in metrics
    assert "fixture benchmark" in metrics


def test_day30_bug_summary_and_next_iterations_are_explicit() -> None:
    bug_summary = read_project_file("doc/supporting/day30-bug-summary.md")
    future_iterations = read_project_file("doc/supporting/future-iterations.md")

    assert "未解决缺口" in bug_summary
    assert "前端 retry 按钮" in bug_summary
    assert "真实 compose build/up" in bug_summary
    assert "真实 embedding provider" in bug_summary
    assert "第二阶段优先级" in future_iterations
    assert "前端 retry 按钮" in future_iterations
    assert "真实 compose build/up 验证" in future_iterations


def test_day30_roadmap_log_testing_and_interview_docs_are_synced() -> None:
    roadmap = read_project_file("doc/roadmap/day-30.md")
    development_log = read_project_file("doc/supporting/development-log.md")
    testing_strategy = read_project_file("doc/supporting/testing-strategy.md")
    interview_dossier = read_project_file("doc/supporting/interview-defense-dossier.md")

    assert "Day 30 实际完成内容" in roadmap
    assert "Day 30 开发记录" in development_log
    assert "Day30 release candidate tests" in development_log
    assert "Day 30 Release Candidate 测试边界" in testing_strategy
    assert "Day 30 里程碑验收" in interview_dossier


def test_release_checklist_and_readme_reflect_day30_candidate() -> None:
    release_checklist = read_project_file("doc/supporting/release-checklist.md")
    readme = read_project_file("README.md")

    assert "Day 30 release candidate" in release_checklist
    assert "v0.1-day30-rc1" in release_checklist
    assert "Day 30" in readme
    assert "day30-release-candidate.md" in readme


def test_day30_audit_removes_stale_day29_release_status() -> None:
    readme = read_project_file("README.md")
    release_candidate = read_project_file("doc/supporting/day30-release-candidate.md")
    development_log = read_project_file("doc/supporting/development-log.md")
    resume_story = read_project_file("doc/supporting/resume-story.md")

    assert "截至 Day 30" in readme
    assert "Day 1-30 的第一阶段 release candidate" in readme
    assert "run id: 27138404103" in release_candidate
    assert "Day 30 最新远程 GitHub Actions 已通过" in release_candidate
    assert "| Day 30 | 里程碑发布、tag、指标和复盘 | 待记录" not in development_log
    assert "Day30 release candidate tests 6 passed" in development_log
    assert "Day30 `uv run pytest`：168 passed" in resume_story
