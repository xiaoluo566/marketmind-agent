from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read_project_file(path: str) -> str:
    source_path = ROOT / path
    assert source_path.exists(), f"{path} should exist"
    return source_path.read_text(encoding="utf-8")


def read_frontend(path: str) -> str:
    source_path = FRONTEND / path
    assert source_path.exists(), f"{path} should exist"
    return source_path.read_text(encoding="utf-8")


def test_day33_roadmap_contains_embedded_sdd_without_external_specs() -> None:
    day33 = read_project_file("doc/roadmap/day-33.md")

    assert "## SDD 规格" in day33
    assert "不另开 `specs/` 文档" in day33
    assert "Spec Kit SDD -> tdd-workflow -> 代码实现 -> verification-loop" in read_project_file(
        "doc/supporting/dev-workflow.md"
    )
    for required_copy in [
        "用户故事 1：证明前端 retry 不是假按钮",
        "用户故事 2：证明后端 retry 链路和 Worker recovery payload 一致",
        "用户故事 3：真实后端事件进入中文控制台后可读",
        "FR-005",
        "接口契约",
        "成功标准",
    ]:
        assert required_copy in day33


def test_frontend_translates_real_backend_retry_and_recovery_events() -> None:
    api_source = read_frontend("lib/api.ts")

    assert "translateBackendTaskEventMessage" in api_source
    assert 'message: translateBackendTaskEventMessage(event)' in api_source
    for chinese_copy in [
        "任务正在等待重试。",
        "任务已重新进入队列。",
        "任务恢复执行已开始。",
        "重试队列不可用。",
    ]:
        assert chinese_copy in api_source

    for backend_message in [
        "task waiting retry",
        "task requeued",
        "task recovery resumed",
        "task retry queue unavailable",
    ]:
        assert backend_message in api_source


def test_frontend_classifies_retry_and_recovery_event_modules() -> None:
    api_source = read_frontend("lib/api.ts")

    assert 'eventType.includes("recovery")' in api_source
    assert 'eventType.includes("retry")' in api_source
    assert 'return "worker";' in api_source
    assert 'return "api";' in api_source


def test_backend_recovery_payload_and_events_remain_auditable() -> None:
    service_source = read_project_file("backend/app/tasks/service.py")
    worker_source = read_project_file("backend/app/worker/tasks.py")

    for backend_message in ["task waiting retry", "task requeued"]:
        assert backend_message in service_source

    assert "task recovery resumed" in worker_source
    for payload_key in [
        "retry_count",
        "resume_from_event_id",
        "resume_from_event_type",
        "last_error_code",
    ]:
        assert payload_key in worker_source
