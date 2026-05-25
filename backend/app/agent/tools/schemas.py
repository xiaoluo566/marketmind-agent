from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ToolErrorCode(StrEnum):
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    TOOL_RUNTIME_ERROR = "TOOL_RUNTIME_ERROR"
    TOOL_OUTPUT_INVALID = "TOOL_OUTPUT_INVALID"


class ToolInvocationContext(BaseModel):
    task_id: str
    trace_id: str
    agent_run_id: str | None = None
    step_id: str | None = None
    attempt: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolArtifact(BaseModel):
    artifact_type: str
    path: str
    mime_type: str | None = None
    checksum: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolErrorData(BaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ToolInvocationResult(BaseModel):
    tool_name: str
    tool_version: str
    success: bool
    data: dict[str, Any] | None = None
    error: ToolErrorData | None = None
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    task_id: str
    trace_id: str
    idempotent: bool
    retryable: bool
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int = 0


class ToolManifest(BaseModel):
    name: str
    version: str
    description: str
    input_schema: str
    output_schema: str
    idempotent: bool
    retryable: bool
    timeout_ms: int
    error_codes: list[str]


ToolHandler = Callable[[BaseModel, ToolInvocationContext], BaseModel | dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: ToolHandler
    version: str = "v1"
    idempotent: bool = True
    retryable: bool = True
    timeout_ms: int = 30_000
    error_codes: tuple[str, ...] = ()

    def manifest(self) -> ToolManifest:
        return ToolManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            input_schema=self.input_schema.__name__,
            output_schema=self.output_schema.__name__,
            idempotent=self.idempotent,
            retryable=self.retryable,
            timeout_ms=self.timeout_ms,
            error_codes=list(self.error_codes),
        )
