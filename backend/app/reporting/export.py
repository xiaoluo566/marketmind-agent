from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.reporting.evidence import EvidenceChain
from app.storage.models import Report

SENSITIVE_KEY_PARTS = ("api_key", "apikey", "token", "secret", "password", "authorization")
SENSITIVE_VALUE_MARKERS = ("sk-", "bearer ")


def build_report_markdown_export(report: Report) -> str:
    markdown = (report.content_markdown or "").strip()
    if markdown:
        return markdown + "\n"

    return "\n".join(
        [
            f"# {report.title}",
            "",
            report.summary or "当前报告没有可导出的摘要。",
            "",
            "## 证据引用",
            "",
            ", ".join(str(evidence_ref) for evidence_ref in report.evidence_refs or [])
            or "证据不足",
            "",
        ]
    )


def build_evidence_package(report: Report, chain: EvidenceChain) -> dict[str, Any]:
    return {
        "package_version": "evidence_package.v1",
        "report_id": report.id,
        "task_id": report.task_id,
        "schema_version": report.schema_version,
        "title": report.title,
        "summary": report.summary or "",
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_refs": list(report.evidence_refs or []),
        "missing_refs": list(chain.missing_refs),
        "sources": [
            {
                "evidence_ref": source.evidence_ref,
                "source_type": source.source_type,
                "source_id": source.source_id,
                "task_id": source.task_id,
                "available": source.available,
                "title": source.title,
                "content_preview": source.content_preview,
                "source_url": source.source_url,
                "parent_refs": list(source.parent_refs),
                "missing_reason": source.missing_reason,
                "metadata": sanitize_export_metadata(source.metadata),
            }
            for source in chain.sources
        ],
    }


def export_filename(prefix: str, report_id: str, extension: str) -> str:
    safe_report_id = "".join(
        char if char.isalnum() or char in {"_", "-"} else "_" for char in report_id
    )
    return f"{prefix}-{safe_report_id}.{extension}"


def sanitize_export_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                continue
            sanitized[key_text] = sanitize_export_metadata(item)
        return sanitized

    if isinstance(value, list):
        return [sanitize_export_metadata(item) for item in value]

    if isinstance(value, tuple):
        return [sanitize_export_metadata(item) for item in value]

    if isinstance(value, str) and _is_sensitive_value(value):
        return "[REDACTED]"

    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _is_sensitive_value(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in SENSITIVE_VALUE_MARKERS)
