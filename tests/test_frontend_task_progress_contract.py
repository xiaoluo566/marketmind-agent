from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read_frontend(path: str) -> str:
    return (FRONTEND / path).read_text(encoding="utf-8")


def test_task_detail_uses_client_progress_panel_for_polling() -> None:
    page_source = read_frontend("app/tasks/[taskId]/page.tsx")
    panel_source = read_frontend("components/task-progress-panel.tsx")

    assert "<TaskProgressPanel" in page_source
    assert '"use client"' in panel_source
    assert "setInterval" in panel_source
    assert "refreshTaskProgress" in panel_source
    assert "getTask(taskId)" in panel_source
    assert "getTaskEvents(taskId)" in panel_source
    assert "getTaskSteps(taskId)" in panel_source


def test_frontend_maps_real_agent_steps_without_mock_fallback_for_successful_api() -> None:
    api_source = read_frontend("lib/api.ts")
    types_source = read_frontend("lib/types.ts")

    assert "BackendTaskSteps" in api_source
    assert "mapBackendAgentStep" in api_source
    assert 'request<BackendTaskSteps>(`/api/tasks/${taskId}/steps`)' in api_source
    assert "step_id: string" in types_source
    assert "task_id: string" in types_source
