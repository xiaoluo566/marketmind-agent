from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.storage.models import AgentRun, AgentStep, Task
from app.storage.statuses import AgentRunStatus, AgentStepStatus


@dataclass(frozen=True, slots=True)
class AgentRunData:
    run_id: str
    task_id: str
    status: str
    model_provider: str
    model_name: str
    report_model_name: str
    prompt_version: str
    started_at: datetime | None
    finished_at: datetime | None
    validation_error_count: int
    self_heal_count: int


@dataclass(frozen=True, slots=True)
class AgentStepData:
    step_id: str
    agent_run_id: str
    task_id: str
    step_index: int
    step_type: str
    status: str
    thought: str | None
    tool_name: str | None
    tool_input: dict[str, Any]
    tool_output: dict[str, Any]
    observation: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None


class SQLAlchemyAgentRunStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def create_run(
        self,
        *,
        task_id: str,
        model_provider: str = "openai-compatible",
        model_name: str = "gpt-5.4-mini",
        report_model_name: str = "gpt-5.5",
        prompt_version: str = "v1",
    ) -> AgentRunData:
        with self._session_scope() as session:
            with session.begin():
                self._ensure_task_exists(session, task_id)
                run = AgentRun(
                    task_id=task_id,
                    status=AgentRunStatus.PENDING.value,
                    model_provider=model_provider,
                    model_name=model_name,
                    report_model_name=report_model_name,
                    prompt_version=prompt_version,
                )
                session.add(run)
                session.flush()
                return self._to_run_data(run)

    def mark_run_running(self, run_id: str, *, started_at: datetime) -> AgentRunData:
        with self._session_scope() as session:
            with session.begin():
                run = self._get_run(session, run_id)
                run.status = AgentRunStatus.RUNNING.value
                run.started_at = run.started_at or started_at
                session.flush()
                return self._to_run_data(run)

    def complete_run(self, run_id: str, *, finished_at: datetime) -> AgentRunData:
        with self._session_scope() as session:
            with session.begin():
                run = self._get_run(session, run_id)
                run.status = AgentRunStatus.COMPLETED.value
                run.finished_at = finished_at
                session.flush()
                return self._to_run_data(run)

    def fail_run(self, run_id: str, *, finished_at: datetime) -> AgentRunData:
        with self._session_scope() as session:
            with session.begin():
                run = self._get_run(session, run_id)
                run.status = AgentRunStatus.FAILED.value
                run.finished_at = finished_at
                session.flush()
                return self._to_run_data(run)

    def record_guardrail_metrics(
        self,
        run_id: str,
        *,
        validation_error_count: int,
        self_heal_count: int,
    ) -> AgentRunData:
        with self._session_scope() as session:
            with session.begin():
                run = self._get_run(session, run_id)
                run.validation_error_count += max(0, validation_error_count)
                run.self_heal_count += max(0, self_heal_count)
                session.flush()
                return self._to_run_data(run)

    def append_step(
        self,
        *,
        agent_run_id: str,
        task_id: str,
        step_type: str,
        status: str = AgentStepStatus.PENDING.value,
        thought: str | None = None,
        tool_name: str | None = None,
        tool_input: dict[str, Any] | None = None,
        tool_output: dict[str, Any] | None = None,
        observation: str | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> AgentStepData:
        with self._session_scope() as session:
            with session.begin():
                self._ensure_run_matches_task(session, agent_run_id=agent_run_id, task_id=task_id)
                step = AgentStep(
                    agent_run_id=agent_run_id,
                    task_id=task_id,
                    step_index=self._next_step_index(session, agent_run_id),
                    step_type=step_type,
                    thought=thought,
                    tool_name=tool_name,
                    tool_input=tool_input or {},
                    tool_output=tool_output or {},
                    observation=observation,
                    status=status,
                    error_message=error_message,
                    started_at=started_at,
                    finished_at=finished_at,
                )
                session.add(step)
                session.flush()
                return self._to_step_data(step)

    def mark_step_running(self, step_id: str, *, started_at: datetime) -> AgentStepData:
        with self._session_scope() as session:
            with session.begin():
                step = self._get_step(session, step_id)
                step.status = AgentStepStatus.RUNNING.value
                step.started_at = step.started_at or started_at
                session.flush()
                return self._to_step_data(step)

    def complete_step(
        self,
        step_id: str,
        *,
        tool_output: dict[str, Any] | None = None,
        observation: str | None = None,
        finished_at: datetime,
    ) -> AgentStepData:
        with self._session_scope() as session:
            with session.begin():
                step = self._get_step(session, step_id)
                step.status = AgentStepStatus.SUCCESS.value
                step.tool_output = tool_output or {}
                step.observation = observation
                step.finished_at = finished_at
                session.flush()
                return self._to_step_data(step)

    def fail_step(
        self,
        step_id: str,
        *,
        tool_output: dict[str, Any] | None = None,
        observation: str | None = None,
        error_message: str,
        finished_at: datetime,
    ) -> AgentStepData:
        with self._session_scope() as session:
            with session.begin():
                step = self._get_step(session, step_id)
                step.status = AgentStepStatus.FAILED.value
                step.tool_output = tool_output or {}
                step.observation = observation
                step.error_message = error_message
                step.finished_at = finished_at
                session.flush()
                return self._to_step_data(step)

    def list_steps(self, agent_run_id: str) -> list[AgentStepData]:
        with self._session_scope() as session:
            stmt = (
                select(AgentStep)
                .where(AgentStep.agent_run_id == agent_run_id)
                .order_by(AgentStep.step_index.asc())
            )
            return [self._to_step_data(row) for row in session.scalars(stmt).all()]

    def get_latest_step(self, agent_run_id: str) -> AgentStepData | None:
        with self._session_scope() as session:
            stmt = (
                select(AgentStep)
                .where(AgentStep.agent_run_id == agent_run_id)
                .order_by(AgentStep.step_index.desc())
                .limit(1)
            )
            row = session.scalars(stmt).first()
            if row is None:
                return None
            return self._to_step_data(row)

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _ensure_task_exists(self, session: Session, task_id: str) -> None:
        if session.get(Task, task_id) is None:
            raise ValueError(f"task {task_id} does not exist")

    def _ensure_run_matches_task(
        self,
        session: Session,
        *,
        agent_run_id: str,
        task_id: str,
    ) -> None:
        run = self._get_run(session, agent_run_id)
        if run.task_id != task_id:
            raise ValueError(f"agent run {agent_run_id} does not belong to task {task_id}")

    def _get_run(self, session: Session, run_id: str) -> AgentRun:
        run = session.get(AgentRun, run_id)
        if run is None:
            raise ValueError(f"agent run {run_id} does not exist")
        return run

    def _get_step(self, session: Session, step_id: str) -> AgentStep:
        step = session.get(AgentStep, step_id)
        if step is None:
            raise ValueError(f"agent step {step_id} does not exist")
        return step

    def _next_step_index(self, session: Session, agent_run_id: str) -> int:
        stmt = select(func.max(AgentStep.step_index)).where(AgentStep.agent_run_id == agent_run_id)
        current_max = session.scalar(stmt)
        return int(current_max or 0) + 1

    def _to_run_data(self, run: AgentRun) -> AgentRunData:
        return AgentRunData(
            run_id=run.id,
            task_id=run.task_id,
            status=run.status,
            model_provider=run.model_provider,
            model_name=run.model_name,
            report_model_name=run.report_model_name,
            prompt_version=run.prompt_version,
            started_at=run.started_at,
            finished_at=run.finished_at,
            validation_error_count=run.validation_error_count,
            self_heal_count=run.self_heal_count,
        )

    def _to_step_data(self, step: AgentStep) -> AgentStepData:
        return AgentStepData(
            step_id=step.id,
            agent_run_id=step.agent_run_id,
            task_id=step.task_id,
            step_index=step.step_index,
            step_type=step.step_type,
            status=step.status,
            thought=step.thought,
            tool_name=step.tool_name,
            tool_input=dict(step.tool_input or {}),
            tool_output=dict(step.tool_output or {}),
            observation=step.observation,
            error_message=step.error_message,
            started_at=step.started_at,
            finished_at=step.finished_at,
        )


__all__ = [
    "AgentRunData",
    "AgentStepData",
    "SQLAlchemyAgentRunStore",
]
