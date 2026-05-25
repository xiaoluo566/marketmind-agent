from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from app.agent.tools.registry import ToolRegistry
from app.agent.tools.schemas import (
    ToolArtifact,
    ToolErrorCode,
    ToolErrorData,
    ToolInvocationContext,
    ToolInvocationResult,
    ToolSpec,
)


class ToolExecutor:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        *,
        context: ToolInvocationContext,
    ) -> ToolInvocationResult:
        started_at = datetime.now(UTC)
        try:
            spec = self._registry.get(tool_name)
        except KeyError as exc:
            return self._build_failure(
                tool_name=tool_name,
                tool_version="unknown",
                context=context,
                started_at=started_at,
                code=ToolErrorCode.TOOL_NOT_FOUND,
                message=str(exc),
                retryable=False,
            )

        try:
            tool_input = spec.input_schema.model_validate(payload)
        except ValidationError as exc:
            return self._build_failure(
                tool_name=spec.name,
                tool_version=spec.version,
                context=context,
                started_at=started_at,
                code=ToolErrorCode.VALIDATION_FAILED,
                message="tool input validation failed",
                retryable=False,
                details={"errors": exc.errors()},
                spec=spec,
            )

        try:
            raw_output = spec.handler(tool_input, context)
        except Exception as exc:
            return self._build_failure(
                tool_name=spec.name,
                tool_version=spec.version,
                context=context,
                started_at=started_at,
                code=_error_code_from_exception(exc),
                message=str(exc),
                retryable=spec.retryable,
                details=_error_details_from_exception(exc),
                spec=spec,
            )

        try:
            output = spec.output_schema.model_validate(raw_output)
        except ValidationError as exc:
            return self._build_failure(
                tool_name=spec.name,
                tool_version=spec.version,
                context=context,
                started_at=started_at,
                code=ToolErrorCode.TOOL_OUTPUT_INVALID,
                message="tool output validation failed",
                retryable=spec.retryable,
                details={"errors": exc.errors()},
                spec=spec,
            )

        finished_at = datetime.now(UTC)
        return ToolInvocationResult(
            tool_name=spec.name,
            tool_version=spec.version,
            success=True,
            data=output.model_dump(mode="json"),
            artifacts=_extract_artifacts(output),
            task_id=context.task_id,
            trace_id=context.trace_id,
            idempotent=spec.idempotent,
            retryable=spec.retryable,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=_duration_ms(started_at, finished_at),
        )

    def _build_failure(
        self,
        *,
        tool_name: str,
        tool_version: str,
        context: ToolInvocationContext,
        started_at: datetime,
        code: ToolErrorCode | str,
        message: str,
        retryable: bool,
        details: dict[str, Any] | None = None,
        spec: ToolSpec | None = None,
    ) -> ToolInvocationResult:
        finished_at = datetime.now(UTC)
        return ToolInvocationResult(
            tool_name=tool_name,
            tool_version=tool_version,
            success=False,
            error=ToolErrorData(
                code=_error_code_value(code),
                message=message,
                retryable=retryable,
                details=details or {},
            ),
            task_id=context.task_id,
            trace_id=context.trace_id,
            idempotent=spec.idempotent if spec is not None else False,
            retryable=retryable,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=_duration_ms(started_at, finished_at),
        )


def _extract_artifacts(output: BaseModel) -> list[ToolArtifact]:
    artifacts = getattr(output, "artifacts", [])
    return [ToolArtifact.model_validate(artifact) for artifact in artifacts]


def _duration_ms(started_at: datetime, finished_at: datetime) -> int:
    return max(0, int((finished_at - started_at).total_seconds() * 1000))


def _error_code_from_exception(exc: Exception) -> str:
    code = getattr(exc, "code", None)
    if code is None:
        return ToolErrorCode.TOOL_RUNTIME_ERROR.value
    return _error_code_value(code)


def _error_details_from_exception(exc: Exception) -> dict[str, Any]:
    details = getattr(exc, "details", None)
    if isinstance(details, dict):
        return details
    return {}


def _error_code_value(code: ToolErrorCode | str | object) -> str:
    value = getattr(code, "value", code)
    return str(value)
