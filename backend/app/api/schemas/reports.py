from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportSectionData(BaseModel):
    title: str
    body: str
    evidence_ids: list[str] = Field(default_factory=list)


class ReportSummaryData(BaseModel):
    report_id: str
    task_id: str
    task_status: str | None = None
    title: str
    summary: str
    status: str
    risk_level: str
    risk_score: int
    evidence_count: int
    created_at: datetime
    updated_at: datetime
    schema_version: str


class ReportDetailData(ReportSummaryData):
    sections: list[ReportSectionData] = Field(default_factory=list)
    content_markdown: str
    evidence_refs: list[str] = Field(default_factory=list)


class ReportListData(BaseModel):
    items: list[ReportSummaryData]
    limit: int
    offset: int
    total: int
