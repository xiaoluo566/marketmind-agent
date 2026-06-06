from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.observability.sanitization import sanitize_details

LOGGER_NAME = "marketmind.observability"


def log_observability_event(
    *,
    level: str = "INFO",
    service: str = "marketmind-api",
    event: str,
    message: str,
    trace_id: str | None = None,
    task_id: str | None = None,
    agent_run_id: str | None = None,
    duration_ms: int | None = None,
    error_code: str | None = None,
    layer: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level.upper(),
        "service": service,
        "trace_id": trace_id,
        "task_id": task_id,
        "agent_run_id": agent_run_id,
        "event": event,
        "duration_ms": duration_ms,
        "error_code": error_code,
        "layer": layer,
        "message": message,
        "details": sanitize_details(details or {}),
    }
    logging.getLogger(LOGGER_NAME).log(
        _levelno(level),
        json.dumps(record, ensure_ascii=False, default=str),
    )


def _levelno(level: str) -> int:
    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(level.upper(), logging.INFO)
