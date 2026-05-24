from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.responses import success_response

router = APIRouter()


@router.get("/health")
def health_check(request: Request) -> dict:
    settings = get_settings()
    return success_response(
        data={
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.app_env,
        },
        message="ok",
        trace_id=request.state.trace_id,
    )

