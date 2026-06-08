from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_ci_workflow_runs_backend_frontend_compose_and_security_gates() -> None:
    workflow = read_project_file(".github/workflows/ci.yml")

    for expected in (
        "pull_request:",
        "push:",
        "branches: [main, dev]",
        "astral-sh/setup-uv",
        "python-version: '3.12'",
        "node-version: 22",
        "uv run ruff check backend tests migrations",
        "uv run pytest --cov=backend --cov-report=term-missing",
        "uv run alembic heads",
        "docker compose config",
        "npm ci",
        "npm run lint",
        "npm run build",
        "npm audit --audit-level=high",
        "uvx pip-audit",
    ):
        assert expected in workflow

    assert "docker compose up" not in workflow
    assert "docker compose build" not in workflow


def test_pull_request_template_requires_quality_and_rollback_evidence() -> None:
    template = read_project_file(".github/pull_request_template.md")

    for expected in (
        "## 变更摘要",
        "## 验证记录",
        "uv run pytest",
        "uv run pytest --cov=backend --cov-report=term-missing",
        "uv run ruff check backend tests migrations",
        "npm run lint",
        "npm run build",
        "docker compose config",
        "## 回退方案",
        "是否涉及数据库迁移",
    ):
        assert expected in template


def test_release_and_rollback_docs_define_tags_backup_and_revert_flow() -> None:
    release_checklist = read_project_file("doc/supporting/release-checklist.md")
    rollback_runbook = read_project_file("doc/supporting/rollback-runbook.md")

    for expected in (
        "v0.1-dayXX",
        "backup/",
        "git tag",
        "git revert",
        "docker compose config",
        "uv run pytest --cov=backend --cov-report=term-missing",
    ):
        assert expected in release_checklist

    for expected in (
        "优先使用 `git revert`",
        "不要默认使用 `git reset --hard`",
        "数据库迁移回退",
        "docker compose down",
        "docker compose up --build -d",
        "回退记录模板",
    ):
        assert expected in rollback_runbook


def test_day26_docs_are_linked_from_testing_and_development_logs() -> None:
    testing_strategy = read_project_file("doc/supporting/testing-strategy.md")
    development_log = read_project_file("doc/supporting/development-log.md")

    assert "Day 26 CI 契约测试边界" in testing_strategy
    assert "tests/test_day26_ci_contract.py" in testing_strategy
    assert "Day 26 开发记录" in development_log
    assert ".github/workflows/ci.yml" in development_log
