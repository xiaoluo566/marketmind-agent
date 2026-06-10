from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


PHASE2_DOCS = {
    "doc/roadmap/day-32.md": ["retry", "POST /api/tasks/{task_id}/retry"],
    "doc/roadmap/day-33.md": ["waiting_retry", "task recovery resumed"],
    "doc/roadmap/day-34.md": ["EmbeddingProvider", "text-embedding-3-small"],
    "doc/roadmap/day-35.md": ["RAG", "provider metrics"],
    "doc/roadmap/day-36.md": ["StructuredReport", "evidence_refs"],
    "doc/roadmap/day-37.md": ["Playwright E2E", "证据链"],
    "doc/roadmap/day-38.md": ["Markdown", "证据包"],
    "doc/roadmap/day-39.md": ["LLMOps", "成本统计"],
    "doc/roadmap/day-40.md": ["Phase 2 RC", "release candidate"],
}


def test_phase2_docs_exist_and_keep_required_context() -> None:
    for relative_path, keywords in PHASE2_DOCS.items():
        doc = read_project_file(relative_path)
        for keyword in keywords:
            assert keyword in doc
        assert "development-log.md" in doc
        assert "interview-defense-dossier.md" in doc
        assert "testing-strategy.md" in doc


def test_phase2_master_plan_remains_available_as_history() -> None:
    master_plan = read_project_file("doc/roadmap/phase-2-master-plan.md")
    roadmap_index = read_project_file("doc/roadmap/README.md")
    doc_index = read_project_file("doc/README.md")

    for relative_path in PHASE2_DOCS:
        assert Path(relative_path).name in master_plan

    assert "Phase 2 RC" in master_plan
    assert "路线文档归档" in roadmap_index
    assert "不再作为项目当前主入口" in roadmap_index
    assert "真实应用闭环说明" in doc_index
    assert "supporting/real-application-loop.md" in doc_index


def test_development_and_interview_docs_still_record_phase2_history() -> None:
    development_log = read_project_file("doc/supporting/development-log.md")
    interview = read_project_file("doc/supporting/interview-defense-dossier.md")
    testing = read_project_file("doc/supporting/testing-strategy.md")

    assert "Day32-Day40" in development_log
    assert "Day32-Day40" in interview
    assert "Day32-Day40" in testing
    assert "真实应用闭环" in development_log

