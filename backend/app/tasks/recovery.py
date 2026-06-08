from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.api.schemas.tasks import TaskEventData, TaskStatusData
from app.storage.statuses import TaskStatus


class RetryErrorClassification(StrEnum):
    RETRYABLE = "retryable"
    NOT_RETRYABLE = "not_retryable"
    UNKNOWN = "unknown"


class RecoveryDecision(StrEnum):
    RETRY = "retry"
    NOT_RETRYABLE = "not_retryable"
    LIMIT_REACHED = "limit_reached"
    INVALID_STATE = "invalid_state"


@dataclass(frozen=True)
class RetryPlan:
    decision: RecoveryDecision
    classification: RetryErrorClassification
    retry_count: int
    next_retry_count: int
    max_attempts: int
    backoff_seconds: int
    reason: str


@dataclass(frozen=True)
class ResumeCheckpoint:
    event_id: str | None
    event_type: str | None
    message: str | None


RETRYABLE_ERROR_CODES = {
    "PAGE_TIMEOUT",
    "NETWORK_ERROR",
    "ACCESS_BLOCKED",
    "CRAWL_PERSISTENCE_FAILED",
    "QUEUE_UNAVAILABLE",
}

NOT_RETRYABLE_ERROR_CODES = {
    "DOM_NOT_FOUND",
    "PARSER_ERROR",
    "VALIDATION_FAILED",
    "TASK_NOT_FOUND",
    "UNKNOWN_SITE",
}


def classify_retry_error(error_code: str | None) -> RetryErrorClassification:
    if error_code is None:
        return RetryErrorClassification.UNKNOWN
    normalized = error_code.strip().upper()
    if normalized in RETRYABLE_ERROR_CODES:
        return RetryErrorClassification.RETRYABLE
    if normalized in NOT_RETRYABLE_ERROR_CODES:
        return RetryErrorClassification.NOT_RETRYABLE
    return RetryErrorClassification.UNKNOWN


def plan_retry(
    *,
    error_code: str | None,
    retry_count: int,
    max_attempts: int = 3,
) -> RetryPlan:
    classification = classify_retry_error(error_code)
    if classification != RetryErrorClassification.RETRYABLE:
        return RetryPlan(
            decision=RecoveryDecision.NOT_RETRYABLE,
            classification=classification,
            retry_count=retry_count,
            next_retry_count=retry_count,
            max_attempts=max_attempts,
            backoff_seconds=0,
            reason=f"error code {error_code or 'UNKNOWN'} is not retryable",
        )
    if retry_count >= max_attempts:
        return RetryPlan(
            decision=RecoveryDecision.LIMIT_REACHED,
            classification=classification,
            retry_count=retry_count,
            next_retry_count=retry_count,
            max_attempts=max_attempts,
            backoff_seconds=0,
            reason="retry attempt limit reached",
        )
    next_retry_count = retry_count + 1
    return RetryPlan(
        decision=RecoveryDecision.RETRY,
        classification=classification,
        retry_count=retry_count,
        next_retry_count=next_retry_count,
        max_attempts=max_attempts,
        backoff_seconds=30 * (2 ** retry_count),
        reason="retry is allowed",
    )


def retry_count_from_options(options: dict[str, Any]) -> int:
    recovery = options.get("recovery")
    if not isinstance(recovery, dict):
        return 0
    raw_count = recovery.get("retry_count", 0)
    if isinstance(raw_count, bool):
        return int(raw_count)
    if isinstance(raw_count, int):
        return max(0, raw_count)
    if isinstance(raw_count, str) and raw_count.isdigit():
        return int(raw_count)
    return 0


def build_retry_options(
    *,
    task: TaskStatusData,
    plan: RetryPlan,
    checkpoint: ResumeCheckpoint,
) -> dict[str, Any]:
    next_options = dict(task.options)
    previous_recovery = next_options.get("recovery")
    if not isinstance(previous_recovery, dict):
        previous_recovery = {}
    next_options["recovery"] = {
        **previous_recovery,
        "retry_count": plan.next_retry_count,
        "max_attempts": plan.max_attempts,
        "backoff_seconds": plan.backoff_seconds,
        "last_error_code": task.error_code,
        "last_error_message": task.error_message,
        "resume_from_event_id": checkpoint.event_id,
        "resume_from_event_type": checkpoint.event_type,
        "resume_from_message": checkpoint.message,
    }
    return next_options


def build_retry_payload(task: TaskStatusData) -> dict[str, Any]:
    return {
        "target": task.target,
        "mode": task.mode,
        "priority": task.priority,
        "source_type": task.source_type,
        "options": task.options,
    }


def find_resume_checkpoint(events: list[TaskEventData]) -> ResumeCheckpoint:
    for event in reversed(events):
        if event.status == TaskStatus.FAILED.value:
            continue
        if event.event_type.endswith("error"):
            continue
        return ResumeCheckpoint(
            event_id=event.event_id,
            event_type=event.event_type,
            message=event.message,
        )
    return ResumeCheckpoint(event_id=None, event_type=None, message=None)
