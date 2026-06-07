import pytest
from app.api.schemas.tasks import TaskCreateRequest, TaskPriority, TaskSourceType
from app.reporting.schemas import ReportFinding, StructuredReport
from app.storage.statuses import AgentStepStatus, TaskStatus
from pydantic import ValidationError


def test_task_create_request_trims_target_and_applies_defaults() -> None:
    request = TaskCreateRequest(target="  demo://portable-espresso-maker-negative-reviews  ")

    assert request.target == "demo://portable-espresso-maker-negative-reviews"
    assert request.priority == TaskPriority.NORMAL
    assert request.source_type == TaskSourceType.DEMO_DATASET
    assert request.options == {}


@pytest.mark.parametrize(
    "target",
    [
        "file:///etc/passwd",
        "http://localhost:8000/admin",
        "http://127.0.0.1:8000/admin",
        "http://10.0.0.5/internal",
        "http://example.local/product",
    ],
)
def test_task_create_request_rejects_unsafe_public_url_targets(target: str) -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(target=target, source_type=TaskSourceType.PUBLIC_URL)


def test_task_create_request_accepts_public_https_target() -> None:
    request = TaskCreateRequest(
        target="https://example.com/products/portable-espresso",
        source_type=TaskSourceType.PUBLIC_URL,
    )

    assert request.target == "https://example.com/products/portable-espresso"


def test_structured_report_rejects_section_refs_outside_report_refs() -> None:
    with pytest.raises(ValidationError, match="unknown evidence refs"):
        StructuredReport(
            task_id="tsk_schema_001",
            title="Portable espresso review risk",
            summary="Evidence-backed summary.",
            evidence_refs=["chunk:known"],
            sections=[
                ReportFinding(
                    section_id="quality",
                    heading="Quality risk",
                    claim="Some reviews mention pump failure.",
                    evidence_refs=["chunk:missing"],
                )
            ],
        )


def test_structured_report_accepts_evidence_backed_sections() -> None:
    report = StructuredReport(
        task_id="tsk_schema_001",
        title="Portable espresso review risk",
        summary="Evidence-backed summary.",
        evidence_refs=["chunk:known"],
        sections=[
            ReportFinding(
                section_id="quality",
                heading="Quality risk",
                claim="Some reviews mention pump failure.",
                evidence_refs=["chunk:known"],
            )
        ],
    )

    assert report.evidence_refs == ["chunk:known"]
    assert report.sections[0].evidence_refs == ["chunk:known"]


def test_status_enums_keep_documented_task_and_step_values() -> None:
    assert {status.value for status in TaskStatus} == {
        "received",
        "queued",
        "running",
        "waiting_retry",
        "completed",
        "failed",
        "cancelled",
    }
    assert {status.value for status in AgentStepStatus} == {
        "pending",
        "running",
        "success",
        "failed",
        "skipped",
    }
