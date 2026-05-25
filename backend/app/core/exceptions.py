from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.responses import error_response


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
    return JSONResponse(
        status_code=422,
        content=error_response(
            code="VALIDATION_FAILED",
            message="request validation failed",
            trace_id=trace_id,
            details=_validation_details(exc.errors()),
        ),
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.code,
            message=exc.message,
            trace_id=trace_id,
            details=_sanitize(exc.details),
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
