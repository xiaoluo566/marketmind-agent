from datetime import datetime
from enum import StrEnum
from ipaddress import ip_address
from typing import Any, Self
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskMode(StrEnum):
    COMPETITIVE_RESEARCH = "competitive_research"
    COMPLETE_REPORT = "complete_report"
    REVIEW_RISK_SCAN = "review_risk_scan"
    OPPORTUNITY_ANALYSIS = "opportunity_analysis"
    COMPETITOR_REVIEW = "competitor_review"
    RISK_SCAN = "risk_scan"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TaskSourceType(StrEnum):
    DEMO_DATASET = "demo_dataset"
    MANUAL_UPLOAD = "manual_upload"
    PUBLIC_URL = "public_url"


class TaskCreateRequest(BaseModel):
    target: str = Field(min_length=1, max_length=2048)
    mode: TaskMode = TaskMode.COMPETITIVE_RESEARCH
    priority: TaskPriority = TaskPriority.NORMAL
    source_type: TaskSourceType = TaskSourceType.DEMO_DATASET
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("target")
    @classmethod
    def normalize_target(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("target cannot be blank")
        return normalized

    @model_validator(mode="after")
    def validate_public_url_target(self) -> Self:
        if self.source_type != TaskSourceType.PUBLIC_URL:
            return self

        parsed = urlparse(self.target)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("public_url target must use http or https")
        if not parsed.hostname:
            raise ValueError("public_url target must include a hostname")
        if _is_blocked_public_url_host(parsed.hostname):
            raise ValueError("public_url target host is not allowed")
        return self


class TaskAcceptedData(BaseModel):
    task_id: str
    status: str
    trace_id: str
    queue_task_id: str | None = None


class TaskStatusData(BaseModel):
    task_id: str
    status: str
    trace_id: str
    target: str
    mode: str
    priority: str
    source_type: str
    options: dict[str, Any] = Field(default_factory=dict)
    queue_task_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TaskEventData(BaseModel):
    event_id: str
    task_id: str
    status: str
    event_type: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None
    created_at: datetime


class TaskEventsData(BaseModel):
    task_id: str
    events: list[TaskEventData]


class TaskListData(BaseModel):
    items: list[TaskStatusData]
    limit: int
    offset: int
    total: int


class AgentStepSummaryData(BaseModel):
    step_id: str
    agent_run_id: str
    task_id: str
    step_index: int
    step_type: str
    tool_name: str | None = None
    status: str
    duration_ms: int | None = None
    input_summary: str | None = None
    observation_summary: str | None = None
    error_code: str | None = None


class TaskAgentStepsData(BaseModel):
    task_id: str
    steps: list[AgentStepSummaryData]


def _is_blocked_public_url_host(hostname: str) -> bool:
    normalized = hostname.strip().lower().rstrip(".")
    if normalized in {"localhost", "0", "0.0.0.0"}:
        return True
    if normalized.endswith(".localhost") or normalized.endswith(".local"):
        return True
    try:
        address = ip_address(normalized)
    except ValueError:
        return False
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )
