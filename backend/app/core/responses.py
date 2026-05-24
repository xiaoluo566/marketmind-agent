from typing import Any


def success_response(data: Any, message: str = "ok", trace_id: str | None = None) -> dict:
    return {
        "success": True,
        "data": data,
        "error": None,
        "message": message,
        "trace_id": trace_id,
    }


def error_response(
    code: str,
    message: str,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "message": message,
        "trace_id": trace_id,
    }

