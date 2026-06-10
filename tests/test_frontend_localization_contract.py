from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = PROJECT_ROOT / "frontend" / "src"


def read_frontend(relative_path: str) -> str:
    path = FRONTEND_SRC / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_app_shell_navigation_uses_chinese_labels() -> None:
    app_shell = read_frontend("components/app-shell.tsx")

    for english_label in ["Dashboard", "New Research", "Tasks", "Reports", "Evidence", "Settings"]:
        assert f'label: "{english_label}"' not in app_shell

    for chinese_label in ["工作台", "新建调研", "任务", "报告", "证据链", "设置"]:
        assert chinese_label in app_shell

    assert "证据链控制台" in app_shell
    assert "本地开发环境" in app_shell
    assert "刷新" in app_shell


def test_dashboard_uses_chinese_operational_copy() -> None:
    dashboard = read_frontend("app/page.tsx")

    for english_copy in [
        "Agent research operations",
        "Tasks today",
        "Success rate",
        "Recent tasks",
        "System chain",
        "Recent reports",
        "View all",
    ]:
        assert english_copy not in dashboard

    for chinese_copy in [
        "Agent 调研工作台",
        "今日任务",
        "成功率",
        "最近任务",
        "系统链路",
        "最近报告",
        "查看全部",
    ]:
        assert chinese_copy in dashboard


def test_new_research_form_uses_chinese_labels_without_translating_api_fields() -> None:
    form = read_frontend("components/new-research-form.tsx")

    for english_copy in [
        "Demo Dataset",
        "URL Crawl",
        "Product URL or dataset",
        "Data source",
        "Analysis mode",
        "Create task",
        "Request payload",
    ]:
        assert english_copy not in form

    for chinese_copy in [
        "演示数据集",
        "公开 URL 采集",
        "商品 URL 或数据集",
        "数据来源",
        "分析模式",
        "创建任务",
        "请求载荷",
    ]:
        assert chinese_copy in form

    for api_field in ["source_type", "use_rag", "priority", "options"]:
        assert api_field in form


def test_status_badge_and_mock_services_use_chinese_user_visible_text() -> None:
    status_badge = read_frontend("components/status-badge.tsx")
    mock_data = read_frontend("lib/mock-data.ts")

    assert "status.replace" not in status_badge
    for chinese_status in ["已接收", "排队中", "运行中", "等待重试", "已完成", "失败"]:
        assert chinese_status in status_badge

    assert "Next.js mock client" not in mock_data
    assert "Stitch reference available" not in mock_data
    assert "state machine planned" not in mock_data
    for chinese_copy in ["Next.js 模拟客户端", "Stitch 参考稿可用", "状态机已接入"]:
        assert chinese_copy in mock_data


def test_task_report_evidence_and_settings_pages_use_chinese_copy() -> None:
    tasks_page = read_frontend("app/tasks/page.tsx")
    reports_page = read_frontend("app/reports/page.tsx")
    report_detail_page = read_frontend("app/reports/[reportId]/page.tsx")
    evidence_page = read_frontend("app/evidence/page.tsx")
    settings_page = read_frontend("app/settings/page.tsx")

    for english_copy in [
        "Task history",
        "Generated reports",
        "Structured report output",
        "Evidence search",
        "Local settings",
    ]:
        for source in [tasks_page, reports_page, report_detail_page, evidence_page, settings_page]:
            assert english_copy not in source

    for chinese_copy in ["调研任务历史", "任务", "状态", "模式", "耗时", "创建时间"]:
        assert chinese_copy in tasks_page

    for chinese_copy in ["已生成调研报告", "条证据", "评分", "风险评分", "证据引用"]:
        report_viewer = read_frontend("components/report-viewer.tsx")
        assert chinese_copy in reports_page + report_detail_page + report_viewer

    for chinese_copy in ["评论语义检索", "搜索质量差", "全部评分", "已选证据", "评分"]:
        assert chinese_copy in evidence_page + read_frontend("components/evidence-list.tsx")

    for chinese_copy in [
        "本地联调设置",
        "API 基础地址",
        "轮询间隔",
        "启用 RAG 检索",
        "采集截图留存",
        "Agent 步骤调试",
        "失败任务重试",
    ]:
        assert chinese_copy in settings_page

    for api_flag in [
        "enable_rag",
        "enable_crawler_screenshot",
        "enable_agent_step_debug",
        "enable_retry",
    ]:
        assert api_flag in settings_page


def test_task_progress_components_use_chinese_operational_copy() -> None:
    progress_panel = read_frontend("components/task-progress-panel.tsx")
    timeline = read_frontend("components/task-timeline.tsx")
    steps_table = read_frontend("components/agent-steps-table.tsx")

    for english_copy in ["Event timeline", "No task events recorded.", "Open report"]:
        assert english_copy not in progress_panel + timeline + steps_table

    for chinese_copy in [
        "刷新中",
        "轮询中",
        "已结束",
        "打开报告",
        "重试任务",
        "正在重新投递",
        "重试失败",
    ]:
        assert chinese_copy in progress_panel

    for chinese_copy in ["事件时间线", "暂无任务事件记录"]:
        assert chinese_copy in timeline

    for chinese_copy in ["Agent 步骤", "步骤", "类型", "工具", "观察结果", "暂无 Agent 步骤记录"]:
        assert chinese_copy in steps_table


def test_frontend_date_formatter_uses_chinese_locale() -> None:
    utils = read_frontend("lib/utils.ts")

    assert 'Intl.DateTimeFormat("en"' not in utils
    assert 'Intl.DateTimeFormat("zh-CN"' in utils
    assert 'month: "2-digit"' in utils


def test_root_layout_uses_chinese_document_metadata() -> None:
    layout = read_frontend("app/layout.tsx")

    assert '<html lang="en"' not in layout
    assert '<html lang="zh-CN"' in layout
    assert "E-commerce review intelligence" not in layout
    assert "电商评论洞察" in layout
