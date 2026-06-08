from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_compose_declares_runtime_services_and_ordering() -> None:
    compose = read_project_file("docker-compose.yml")

    for service in ("postgres", "redis", "migrate", "api", "worker", "frontend"):
        assert re.search(rf"(?m)^  {service}:\s*$", compose), f"missing {service} service"

    assert "pgvector/pgvector" in compose
    assert "redis:7" in compose
    assert "condition: service_healthy" in compose
    assert "condition: service_completed_successfully" in compose
    assert "uv run alembic upgrade head" in compose
    assert "uv run celery -A app.worker.celery_app.celery_app worker" in compose
    assert "http://localhost:8000/api/health" in compose
    assert "NEXT_PUBLIC_API_BASE_URL: http://localhost:8000" in compose


def test_compose_uses_container_internal_database_and_redis_urls() -> None:
    compose = read_project_file("docker-compose.yml")

    assert (
        "postgresql+psycopg://${POSTGRES_USER:-marketmind}:${POSTGRES_PASSWORD:-marketmind}"
        "@postgres:5432/${POSTGRES_DB:-marketmind}" in compose
    )
    assert "redis://redis:6379/1" in compose
    assert "redis://redis:6379/2" in compose
    assert "redis://redis:6379/3" in compose
    assert "CRAWLER_ARTIFACT_DIR: /app/data/artifacts/crawler" in compose


def test_backend_and_frontend_dockerfiles_define_reproducible_builds() -> None:
    backend_dockerfile = read_project_file("Dockerfile.backend")
    frontend_dockerfile = read_project_file("frontend/Dockerfile")

    assert "python:3.12" in backend_dockerfile
    assert "uv sync --frozen --no-dev" in backend_dockerfile
    assert "uv run playwright install --with-deps chromium" in backend_dockerfile
    assert "uv run uvicorn app.main:create_app --factory" in backend_dockerfile

    assert "node:22" in frontend_dockerfile
    assert "npm ci" in frontend_dockerfile
    assert "npm run build" in frontend_dockerfile
    assert "npm run start" in frontend_dockerfile


def test_env_examples_and_dockerignore_protect_local_runtime_state() -> None:
    root_env = read_project_file(".env.example")
    frontend_env = read_project_file("frontend/.env.example")
    dockerignore = read_project_file(".dockerignore")

    for key in (
        "POSTGRES_USER=marketmind",
        "POSTGRES_PASSWORD=marketmind",
        "POSTGRES_DB=marketmind",
        "API_PORT=8000",
        "FRONTEND_PORT=3000",
    ):
        assert key in root_env

    assert "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" in frontend_env
    assert "NEXT_PUBLIC_USE_MOCKS=false" in frontend_env

    for ignored in (".env", ".venv", "node_modules", ".next", "data", "__pycache__"):
        assert ignored in dockerignore
