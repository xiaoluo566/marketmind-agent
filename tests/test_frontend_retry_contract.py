from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read_frontend(path: str) -> str:
    source_path = FRONTEND / path
    assert source_path.exists(), f"{path} should exist"
    return source_path.read_text(encoding="utf-8")


def test_api_client_exposes_retry_task_with_real_backend_route() -> None:
    api_source = read_frontend("lib/api.ts")

    assert "export async function retryTask" in api_source
    assert "request<TaskAccepted>" in api_source
    assert "`/api/tasks/${taskId}/retry`" in api_source
    assert 'method: "POST"' in api_source
    assert "ApiClientError" in api_source


def test_task_progress_panel_shows_retry_only_for_failed_tasks() -> None:
    panel_source = read_frontend("components/task-progress-panel.tsx")

    assert "retryTask" in panel_source
    assert "canRetryTask" in panel_source
    assert 'task.status === "failed"' in panel_source
    assert "canRetryTask ?" in panel_source
    assert "disabled={retrying || refreshing}" in panel_source


def test_task_progress_panel_uses_chinese_retry_copy_and_errors() -> None:
    panel_source = read_frontend("components/task-progress-panel.tsx")

    for chinese_copy in [
        "重试任务",
        "正在重新投递",
        "重试任务已提交",
        "重试失败",
        "重试投递失败，请稍后再试。",
    ]:
        assert chinese_copy in panel_source

    assert "trace id" in panel_source
    assert "setRetryError" in panel_source
    assert "setRetryMessage" in panel_source


def test_retry_success_refreshes_task_events_and_steps() -> None:
    panel_source = read_frontend("components/task-progress-panel.tsx")

    assert "handleRetryTask" in panel_source
    assert "await retryTask(taskId)" in panel_source
    assert "await refreshTaskProgress()" in panel_source
    assert "setRetrying(true)" in panel_source
    assert "setRetrying(false)" in panel_source


def test_mock_retry_flow_updates_task_snapshot_and_timeline() -> None:
    api_source = read_frontend("lib/api.ts")

    assert "mockRetriedTaskIds" in api_source
    assert "buildMockRetriedTask" in api_source
    assert "task.retry_submitted" in api_source
    assert "重试任务已提交，任务已重新进入队列。" in api_source
    assert 'status: "queued"' in api_source
