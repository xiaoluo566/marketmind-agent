# Alembic Migrations

Day 3 creates the migration scaffold and initial schema migration.

Common commands:

```bash
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "describe change"
```

The first migration enables the PostgreSQL `vector` extension and creates the core tables used by tasks, Agent state, crawler evidence, review chunks, reports, artifacts, and structured errors.
