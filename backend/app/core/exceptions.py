from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response


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
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_FAILED",
            message="request validation failed",
            trace_id=trace_id,
            details=_validation_details(exc.errors()),
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    detail = exc.detail
    message = detail if isinstance(detail, str) else "http request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code="HTTP_ERROR",
            message=message,
            trace_id=trace_id,
            details={"detail": _sanitize(detail)},
        ),
    )
