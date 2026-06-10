from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.models import AgentRun, Task, TaskEvent
from app.storage.statuses import TaskStatus


def summarize_llmops(session: Session) -> dict[str, Any]:
    tasks = list(session.scalars(select(Task)).all())
    agent_runs = list(session.scalars(select(AgentRun)).all())
    events = list(session.scalars(select(TaskEvent)).all())

    model_usage = _model_usage(agent_runs)
    warnings = _warnings(model_usage=model_usage)
    return {
        "summary_version": "llmops.summary.v1",
        "generated_at": datetime.now().astimezone().isoformat(),
        "data_freshness": "database_snapshot",
        "data_sources": [
            "database:tasks",
            "database:agent_runs",
            "database:task_events",
            "not_persisted:provider_metrics",
        ],
        "task_metrics": _task_metrics(tasks),
        "model_usage": model_usage,
        "guardrail_metrics": _guardrail_metrics(agent_runs),
        "recovery_metrics": _recovery_metrics(tasks=tasks, events=events),
        "provider_metrics": {
            "embedding_provider_calls": 0,
            "average_latency_ms": 0,
            "data_source": "not_persisted",
            "note": (
                "Day35 provider metrics are fixture/in-memory baselines; "
                "they are not persisted as production provider metrics yet."
            ),
        },
        "warnings": warnings,
    }


def _task_metrics(tasks: list[Task]) -> dict[str, Any]:
    total = len(tasks)
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED.value)
    failed = sum(1 for task in tasks if task.status == TaskStatus.FAILED.value)
    return {
        "total_tasks": total,
        "completed_tasks": completed,
        "failed_tasks": failed,
        "success_rate": _ratio(completed, total),
        "failure_rate": _ratio(failed, total),
        "average_duration_ms": _average_duration_ms(
            [_duration_ms(task.started_at, task.finished_at) for task in tasks]
        ),
        "data_source": "database:tasks",
    }


def _model_usage(agent_runs: list[AgentRun]) -> dict[str, Any]:
    total_cost = round(sum(float(run.total_cost or 0.0) for run in agent_runs), 4)
    return {
        "agent_run_count": len(agent_runs),
        "model_call_count": len(agent_runs),
        "input_tokens": sum(int(run.input_tokens or 0) for run in agent_runs),
        "output_tokens": sum(int(run.output_tokens or 0) for run in agent_runs),
        "total_tokens": sum(int(run.total_tokens or 0) for run in agent_runs),
        "reported_cost": total_cost,
        "cost_source": "agent_runs.total_cost" if total_cost > 0 else "not_available",
        "cost_confidence": (
            "provider_reported_or_manual_recorded" if total_cost > 0 else "not_available"
        ),
        "data_source": "database:agent_runs",
    }


def _guardrail_metrics(agent_runs: list[AgentRun]) -> dict[str, Any]:
    validation_errors = sum(int(run.validation_error_count or 0) for run in agent_runs)
    self_heals = sum(int(run.self_heal_count or 0) for run in agent_runs)
    return {
        "validation_error_count": validation_errors,
        "self_heal_count": self_heals,
        "self_heal_success_rate": _ratio(self_heals, validation_errors),
        "data_source": "database:agent_runs",
    }


def _recovery_metrics(*, tasks: list[Task], events: list[TaskEvent]) -> dict[str, Any]:
    retry_requested = _count_events(events, "task waiting retry")
    retry_requeued = _count_events(events, "task requeued")
    recovery_resumed = _count_events(events, "task recovery resumed")
    queue_unavailable = _count_events(events, "task retry queue unavailable")
    recovered_task_ids = {
        task.id
        for task in tasks
        if isinstance(task.options, dict)
        and isinstance(task.options.get("recovery"), dict)
        and task.status == TaskStatus.COMPLETED.value
    }
    return {
        "retry_requested_count": retry_requested,
        "retry_requeued_count": retry_requeued,
        "recovery_resumed_count": recovery_resumed,
        "retry_queue_unavailable_count": queue_unavailable,
        "recovery_success_count": len(recovered_task_ids),
        "recovery_success_rate": _ratio(len(recovered_task_ids), retry_requested),
        "data_source": "database:task_events+tasks",
    }


def _count_events(events: list[TaskEvent], message: str) -> int:
    return sum(1 for event in events if event.message == message)


def _duration_ms(started_at: datetime | None, finished_at: datetime | None) -> int | None:
    if started_at is None or finished_at is None:
        return None
    return max(0, round((finished_at - started_at).total_seconds() * 1000))


def _average_duration_ms(values: list[int | None]) -> int:
    durations = [value for value in values if value is not None]
    if not durations:
        return 0
    return round(sum(durations) / len(durations))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _warnings(*, model_usage: dict[str, Any]) -> list[str]:
    warnings: list[str] = ["暂无真实 provider 成本数据"]
    if model_usage["cost_confidence"] == "not_available":
        warnings.append("agent_runs.total_cost 当前没有可用记录")
    warnings.append("provider metrics 尚未持久化，Day35 指标仅代表 fixture/in-memory baseline")
    return warnings
