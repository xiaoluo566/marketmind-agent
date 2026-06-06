from fastapi import APIRouter

from app.api.routes import health, reports, tasks

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(reports.router, tags=["reports"])
