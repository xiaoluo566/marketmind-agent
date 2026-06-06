from collections.abc import Iterable
from time import perf_counter
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response
from app.observability.error_store import ErrorLayer, ErrorLogData, ErrorLogStore
from app.observability.logging import log_observability_event


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def app_error(
    code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
) -> AppError:
    return AppError(code=code, message=message, status_code=status_code, details=details)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(item) for item in value]
    if isinstance(value, set):
        return [_sanitize(item) for item in value]
    if isinstance(value, Exception):
        return str(value)
    return value


def _validation_details(errors: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {"errors": [_sanitize(error) for error in errors]}


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    details = _validation_details(exc.errors())
    _record_api_error(
        request=request,
        code="VALIDATION_FAILED",
        message="request validation failed",
        status_code=422,
        details=details,
    )
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_FAILED",
            message="request validation failed",
            trace_id=trace_id,
            details=details,
        ),
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    details = _sanitize(exc.details)
    _record_api_error(
        request=request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            trace_id=trace_id,
            details=details,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    detail = exc.detail
    message = detail if isinstance(detail, str) else "http request failed"
    details = {"detail": _sanitize(detail)}
    _record_api_error(
        request=request,
        code="HTTP_ERROR",
        message=message,
        status_code=exc.status_code,
        details=details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code="HTTP_ERROR",
            message=message,
            trace_id=trace_id,
            details=details,
        ),
    )


def _record_api_error(
    *,
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any],
) -> None:
    trace_id = getattr(request.state, "trace_id", None)
    duration_ms = _request_duration_ms(request)
    task_id = _task_id_from_details(details)
    log_details = {
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **details,
    }
    log_observability_event(
        level="WARNING" if status_code < 500 else "ERROR",
        service="marketmind-api",
        event="api.error",
        message=message,
        trace_id=trace_id,
        task_id=task_id,
        duration_ms=duration_ms,
        error_code=code,
        layer=ErrorLayer.API.value,
        details=log_details,
    )
    error_store = _error_store_from_request(request)
    if error_store is None:
        return
    try:
        error_store.append(
            ErrorLogData(
                task_id=task_id,
                trace_id=trace_id,
                layer=ErrorLayer.API,
                error_code=code,
                message=message,
                details=log_details,
            )
        )
    except Exception as exc:
        log_observability_event(
            level="ERROR",
            service="marketmind-api",
            event="api.error_log_write_failed",
            message="failed to persist api error log",
            trace_id=trace_id,
            error_code="ERROR_LOG_WRITE_FAILED",
            layer=ErrorLayer.API.value,
            details={"reason": str(exc)},
        )


def _request_duration_ms(request: Request) -> int:
    started_at = getattr(request.state, "request_started_at", None)
    if isinstance(started_at, int | float):
        return max(0, int((perf_counter() - started_at) * 1000))
    duration_ms = getattr(request.state, "duration_ms", None)
    if isinstance(duration_ms, int):
        return max(0, duration_ms)
    return 0


def _task_id_from_details(details: dict[str, Any]) -> str | None:
    task_id = details.get("task_id")
    return task_id if isinstance(task_id, str) else None


def _error_store_from_request(request: Request) -> ErrorLogStore | None:
    store = getattr(request.app.state, "error_log_store", None)
    if store is not None:
        return store
    store_factory = getattr(request.app.state, "error_log_store_factory", None)
    if store_factory is None:
        return None
    return store_factory()
