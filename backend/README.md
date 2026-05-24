# Backend

FastAPI backend for MarketMind Agent.

## Responsibilities

- Accept task requests from the frontend
- Return stable API envelopes
- Own request validation and trace IDs
- Dispatch long-running work to background workers in later milestones
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
