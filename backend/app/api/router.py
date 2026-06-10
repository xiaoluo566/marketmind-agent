from fastapi import APIRouter

from app.api.routes import health, imports, observability, reports, tasks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(imports.router, tags=["imports"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(observability.router, tags=["observability"])
