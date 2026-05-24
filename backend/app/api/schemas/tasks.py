from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


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
    created_at: datetime
    updated_at: datetime
