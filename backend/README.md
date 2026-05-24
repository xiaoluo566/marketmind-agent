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

