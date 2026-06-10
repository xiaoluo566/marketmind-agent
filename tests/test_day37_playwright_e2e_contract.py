from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def read_frontend_file(relative_path: str) -> str:
    path = FRONTEND_ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_frontend_exposes_playwright_e2e_script_and_dependency() -> None:
    package_json = json.loads((FRONTEND_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["scripts"]["test:e2e"] == "playwright test"
    assert "@playwright/test" in package_json["devDependencies"]


def test_playwright_config_uses_mock_dev_server_and_failure_artifacts() -> None:
    config = read_frontend_file("playwright.config.ts")

    assert 'testDir: "./e2e"' in config
    assert 'baseURL: "http://127.0.0.1:3100"' in config
    assert "npm run dev -- --hostname 127.0.0.1 --port 3100" in config
    assert 'NEXT_PUBLIC_USE_MOCKS: "true"' in config
    assert 'NEXT_PUBLIC_API_BASE_URL: "http://127.0.0.1:8000"' in config
    assert 'trace: "retain-on-failure"' in config
    assert 'screenshot: "only-on-failure"' in config
    assert 'video: "retain-on-failure"' in config
    assert '"html"' in config


def test_e2e_main_flow_uses_chinese_user_visible_contract() -> None:
    spec = read_frontend_file("e2e/marketmind-main-flow.spec.ts")

    for chinese_locator in [
        "Agent 调研工作台",
        "新建调研",
        "最近任务",
        "创建竞品调研任务",
        "商品 URL 或数据集",
        "创建任务",
        "任务详情",
        "便携咖啡机竞品扫描",
        "Agent 步骤",
        "调研任务历史",
        "USB-C 拓展坞采集任务",
        "重试任务",
        "重试任务已提交",
        "报告",
        "已生成调研报告",
        "报告详情",
        "证据引用",
        "证据链",
        "评论语义检索",
        "搜索质量差",
    ]:
        assert chinese_locator in spec

    assert "task.retry_submitted" in spec
    assert "demo://e2e-negative-reviews" in spec
    assert "tsk_9A21" in spec


def test_mock_task_creation_keeps_e2e_independent_from_backend() -> None:
    api_client = read_frontend_file("src/lib/api.ts")

    assert "export async function createTask" in api_client
    assert "if (USE_MOCKS)" in api_client
    assert 'task_id: tasks[0]?.task_id ?? "tsk_mock_created"' in api_client
    assert 'queue_task_id: "queue_mock_created"' in api_client
