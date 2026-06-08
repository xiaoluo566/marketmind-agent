from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_readme_is_demo_ready_and_links_core_materials() -> None:
    readme = read_project_file("README.md")

    assert "Day 30" in readme
    assert "## 快速启动" in readme
    assert "## 架构图" in readme
    assert "## 演示路径" in readme
    assert "## 已知边界" in readme
    assert "doc/supporting/demo-script.md" in readme
    assert "doc/supporting/resume-story.md" in readme
    assert "doc/supporting/interview-story.md" in readme
    assert "doc/supporting/day30-release-candidate.md" in readme


def test_demo_script_covers_main_flow_retry_and_fallbacks() -> None:
    demo_script = read_project_file("doc/supporting/demo-script.md")

    assert "5-8 分钟" in demo_script
    assert "演示前检查" in demo_script
    assert "主线演示流程" in demo_script
    assert "失败重试" in demo_script
    assert "备用路线" in demo_script
    assert "不要现场声称" in demo_script


def test_resume_story_uses_verified_metrics_and_limits_claims() -> None:
    resume_story = read_project_file("doc/supporting/resume-story.md")

    assert "Day27 fixture benchmark" in resume_story
    assert "Day28 失败任务 retry" in resume_story
    assert "90.79%" in resume_story
    assert "157 passed" in resume_story
    assert "不建议写" in resume_story


def test_interview_story_has_short_pitch_and_day29_boundaries() -> None:
    interview_story = read_project_file("doc/supporting/interview-story.md")

    assert "2 分钟版本" in interview_story
    assert "不是套壳" in interview_story
    assert "Day 28" in interview_story
    assert "Day 29" in interview_story
    assert "如果被追问" in interview_story


def test_day29_docs_are_linked_from_development_log_and_testing_strategy() -> None:
    development_log = read_project_file("doc/supporting/development-log.md")
    testing_strategy = read_project_file("doc/supporting/testing-strategy.md")

    assert "Day 29 开发记录" in development_log
    assert "Day29 demo docs tests" in development_log
    assert "Day 29 Demo 文档测试边界" in testing_strategy
    assert "tests/test_day29_demo_docs.py" in testing_strategy
