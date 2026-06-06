from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.logging import log_observability_event


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or f"trc_{uuid4().hex}"
        started_at = perf_counter()
        request.state.trace_id = trace_id
        request.state.request_started_at = started_at
        response = await call_next(request)
        duration_ms = max(0, int((perf_counter() - started_at) * 1000))
        request.state.duration_ms = duration_ms
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Request-Duration-Ms"] = str(duration_ms)
        log_observability_event(
            service="marketmind-api",
            event="api.request.completed",
            message="request completed",
            trace_id=trace_id,
            duration_ms=duration_ms,
            layer="api",
            details={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )
        return response
