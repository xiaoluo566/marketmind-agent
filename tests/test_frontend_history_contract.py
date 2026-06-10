from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "src"


def read_frontend(path: str) -> str:
    return (FRONTEND / path).read_text(encoding="utf-8")


def test_frontend_history_uses_real_task_list_endpoint_without_success_fallback() -> None:
    api_source = read_frontend("lib/api.ts")
    tasks_page_source = read_frontend("app/tasks/page.tsx")

    assert "type BackendTaskList" in api_source
    assert 'request<BackendTaskList>("/api/tasks")' in api_source
    assert "payload.items.map(mapBackendTask)" in api_source
    assert "return safeRequest<Task[]>(\"/api/tasks\", tasks)" not in api_source
    assert "listTasks()" in tasks_page_source


def test_frontend_reports_use_real_list_and_detail_contracts() -> None:
    api_source = read_frontend("lib/api.ts")
    reports_page_source = read_frontend("app/reports/page.tsx")
    report_detail_source = read_frontend("app/reports/[reportId]/page.tsx")

    assert "type BackendReportList" in api_source
    assert "type BackendReportDetail" in api_source
    assert 'request<BackendReportList>("/api/reports")' in api_source
    assert "payload.items.map(mapBackendReport)" in api_source
    assert "request<BackendReportDetail>(`/api/reports/${reportId}`)" in api_source
    assert "mapBackendReportDetail" in api_source
    assert "return safeRequest<typeof reports>(\"/api/reports\", reports)" not in api_source
    assert "listReports()" in reports_page_source
    assert "getReport(reportId)" in report_detail_source


def test_report_detail_uses_real_report_evidence_chain() -> None:
    api_source = read_frontend("lib/api.ts")
    report_detail_source = read_frontend("app/reports/[reportId]/page.tsx")

    assert "type BackendReportEvidence" in api_source
    assert "export async function getReportEvidence" in api_source
    assert "request<BackendReportEvidence>(`/api/reports/${reportId}/evidence`)" in api_source
    assert "mapBackendEvidenceSource" in api_source
    assert "getReportEvidence(reportId)" in report_detail_source
    assert "listEvidence()" not in report_detail_source


def test_report_detail_exposes_markdown_and_evidence_package_downloads() -> None:
    api_source = read_frontend("lib/api.ts")
    report_viewer_source = read_frontend("components/report-viewer.tsx")

    assert "export function getReportMarkdownExportUrl" in api_source
    assert "export function getReportEvidencePackageUrl" in api_source
    assert "/export/markdown" in api_source
    assert "/evidence-package" in api_source
    assert "buildDataUrl(" in api_source
    assert '"text/markdown"' in api_source
    assert '"application/json"' in api_source

    assert "导出 Markdown" in report_viewer_source
    assert "下载证据包" in report_viewer_source
    assert "marketmind-report-${report.report_id}.md" in report_viewer_source
    assert "marketmind-evidence-${report.report_id}.json" in report_viewer_source
