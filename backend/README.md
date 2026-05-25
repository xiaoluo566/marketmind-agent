# Backend

FastAPI backend for MarketMind Agent.

## Responsibilities

- Accept task requests from the frontend
- Return stable API envelopes
- Own request validation and trace IDs
- Dispatch long-running work to background workers
- Expose task, event, Agent step, report, and evidence APIs

## Current status

Day 1 backend baseline:

- FastAPI application factory
- `/health` endpoint
- trace ID middleware
- typed settings
- response envelope helpers
- pytest coverage for health response and trace behavior

Day 3 storage baseline:

- SQLAlchemy 2.0 declarative base
- Core task, Agent, crawler, review, report, artifact, and error models
- Status enums for tasks, Agent runs, and Agent steps
- pgvector review chunk field fixed at 1536 dimensions
- Alembic scaffold and initial schema migration

Day 5 async task baseline:

- `POST /api/tasks` creates a task status snapshot and dispatches Celery work
- `GET /api/tasks/{task_id}` reads the current task status snapshot
- Redis-backed task status store
- Celery app configured with Redis broker and result backend
- Minimal worker task that advances queued tasks to running and completed

Day 6 task progress baseline:

- `GET /api/tasks/{task_id}/events` reads the structured task timeline
- Redis-backed task event store
- API writes received, queued, and failed events
- Worker writes running and completed events

## Local worker

Redis must be running before using the real queue path.

```powershell
uv run uvicorn app.main:app --app-dir backend --reload
uv run celery -A app.worker.celery_app.celery_app worker -Q marketmind --loglevel=INFO --pool=solo
```

Use `--pool=solo` on Windows.
