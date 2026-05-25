from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.agent.tools.builtin import build_default_tool_registry
from app.agent.tools.executor import ToolExecutor
from app.agent.tools.schemas import ToolInvocationContext, ToolInvocationResult
from app.storage.agent_stores import SQLAlchemyAgentRunStore
from app.storage.statuses import AgentStepStatus


@dataclass(frozen=True, slots=True)
class AgentTaskInput:
    task_id: str
    trace_id: str
    target: str
    source_type: str
    options: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    run_id: str
    task_id: str
    status: str
    completed_steps: int
    last_tool_name: str | None = None
    last_error_code: str | None = None


class AgentStateMachine:
    def __init__(
        self,
        *,
        run_store: SQLAlchemyAgentRunStore,
        tool_executor: ToolExecutor | None = None,
        max_tool_calls: int = 1,
    ) -> None:
        self._run_store = run_store
        self._tool_executor = tool_executor or ToolExecutor(build_default_tool_registry())
        self._max_tool_calls = max_tool_calls

    def run(self, task: AgentTaskInput) -> AgentRunResult:
        run = self._run_store.create_run(task_id=task.task_id)
        run = self._run_store.mark_run_running(run.run_id, started_at=_now())

        self._run_store.append_step(
            agent_run_id=run.run_id,
            task_id=task.task_id,
            step_type="thought",
            status=AgentStepStatus.SUCCESS.value,
            thought=self._build_thought(task),
            started_at=_now(),
            finished_at=_now(),
        )

        if self._max_tool_calls < 1:
            failed_run = self._run_store.fail_run(run.run_id, finished_at=_now())
            return AgentRunResult(
                run_id=failed_run.run_id,
                task_id=task.task_id,
                status=failed_run.status,
                completed_steps=1,
            )

        tool_input = self._build_tool_input(task)
        action_step = self._run_store.append_step(
            agent_run_id=run.run_id,
            task_id=task.task_id,
            step_type="action",
            tool_name="crawl_product_tool",
            tool_input=tool_input,
            status=AgentStepStatus.PENDING.value,
        )
        self._run_store.mark_step_running(action_step.step_id, started_at=_now())

        tool_result = self._tool_executor.execute(
            "crawl_product_tool",
            tool_input,
            context=ToolInvocationContext(
                task_id=task.task_id,
                trace_id=task.trace_id,
                agent_run_id=run.run_id,
                step_id=action_step.step_id,
                metadata={"source_type": task.source_type},
            ),
        )

        if tool_result.success:
            action_step = self._run_store.complete_step(
                action_step.step_id,
                tool_output=tool_result.model_dump(mode="json"),
                observation=self._build_observation(tool_result),
                finished_at=_now(),
            )
            self._run_store.append_step(
                agent_run_id=run.run_id,
                task_id=task.task_id,
                step_type="observation",
                status=AgentStepStatus.SUCCESS.value,
                observation=self._build_observation(tool_result),
                tool_output=tool_result.model_dump(mode="json"),
                finished_at=_now(),
            )
            completed_run = self._run_store.complete_run(run.run_id, finished_at=_now())
            return AgentRunResult(
                run_id=completed_run.run_id,
                task_id=task.task_id,
                status=completed_run.status,
                completed_steps=3,
                last_tool_name=action_step.tool_name,
            )

        action_step = self._run_store.fail_step(
            action_step.step_id,
            tool_output=tool_result.model_dump(mode="json"),
            observation=self._build_failed_observation(tool_result),
            error_message=tool_result.error.message if tool_result.error else "tool failed",
            finished_at=_now(),
        )
        self._run_store.append_step(
            agent_run_id=run.run_id,
            task_id=task.task_id,
            step_type="observation",
            status=AgentStepStatus.FAILED.value,
            observation=self._build_failed_observation(tool_result),
            tool_output=tool_result.model_dump(mode="json"),
            error_message=tool_result.error.message if tool_result.error else "tool failed",
            finished_at=_now(),
        )
        failed_run = self._run_store.fail_run(run.run_id, finished_at=_now())
        return AgentRunResult(
            run_id=failed_run.run_id,
            task_id=task.task_id,
            status=failed_run.status,
            completed_steps=3,
            last_tool_name=action_step.tool_name,
            last_error_code=tool_result.error.code if tool_result.error else None,
        )

    def _build_thought(self, task: AgentTaskInput) -> str:
        if task.source_type == "public_url":
            return f"需要先采集商品页 {task.target}，再判断是否存在评论证据。"
        return f"当前任务来源为 {task.source_type}，先检查是否需要工具调用。"

    def _build_tool_input(self, task: AgentTaskInput) -> dict[str, Any]:
        options = dict(task.options or {})
        html = options.get("fixture_html")
        fixture_path = options.get("fixture_path")
        return {
            "task_id": task.task_id,
            "url": task.target,
            "source_type": "html_fixture" if html or fixture_path else "public_url",
            "html": html,
            "fixture_path": fixture_path,
            "artifact_dir": options.get("artifact_dir"),
            "save_html_artifact": _read_bool_option(
                options.get("save_html_artifact"),
                default=True,
            ),
            "capture_screenshot": _read_bool_option(
                options.get("capture_screenshot"),
                default=False,
            ),
            "timeout_ms": int(options.get("crawl_timeout_ms") or 15_000),
            "user_agent": options.get("user_agent"),
        }

    def _build_observation(self, tool_result: ToolInvocationResult) -> str:
        data = tool_result.data or {}
        title = data.get("title") or "Unknown Title"
        reviews = data.get("reviews") or []
        return f"采集完成：{title}，共提取 {len(reviews)} 条评论证据。"

    def _build_failed_observation(self, tool_result: ToolInvocationResult) -> str:
        if tool_result.error is None:
            return "工具调用失败，未返回结构化错误。"
        return f"工具调用失败：{tool_result.error.code} - {tool_result.error.message}"


def _now() -> datetime:
    return datetime.now(UTC)


def _read_bool_option(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
