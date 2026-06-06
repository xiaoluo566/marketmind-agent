from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read_frontend(path: str) -> str:
    return (FRONTEND / path).read_text(encoding="utf-8")


def test_api_client_exposes_real_task_creation_and_envelope_errors() -> None:
    api_source = read_frontend("lib/api.ts")

    assert "export async function createTask" in api_source
    assert "TaskCreateInput" in api_source
    assert "ApiEnvelope" in api_source
    assert "ApiClientError" in api_source
    assert 'request<TaskAccepted>("/api/tasks"' in api_source
    assert "envelope.error" in api_source


def test_research_form_submits_to_real_task_api_and_links_task_detail() -> None:
    form_source = read_frontend("components/new-research-form.tsx")
    page_source = read_frontend("app/research/new/page.tsx")

    assert '"use client"' in form_source
    assert "createTask" in form_source
    assert "router.push(`/tasks/${accepted.task_id}`)" in form_source
    assert "ApiClientError" in form_source
    assert "useState" in form_source
    assert "<NewResearchForm />" in page_source


def test_task_detail_uses_real_status_and_events_with_safe_step_fallback() -> None:
    api_source = read_frontend("lib/api.ts")
    task_detail_source = read_frontend("app/tasks/[taskId]/page.tsx")

    assert "getTask(taskId)" in task_detail_source
    assert "getTaskEvents(taskId)" in task_detail_source
    assert "getTaskSteps(taskId)" in task_detail_source
    assert "safeRequest" in api_source
    assert "`/api/tasks/${taskId}/steps`" in api_source
    assert "return []" in api_source


def test_app_shell_and_env_example_expose_api_mode() -> None:
    shell_source = read_frontend("components/app-shell.tsx")
    env_example = (ROOT / "frontend" / ".env.example").read_text(encoding="utf-8")

    assert "getApiModeLabel" in shell_source
    assert "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" in env_example
    assert "NEXT_PUBLIC_USE_MOCKS=false" in env_example
