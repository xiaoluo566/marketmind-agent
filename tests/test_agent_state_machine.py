from datetime import UTC, datetime

from app.agent.state_machine import AgentStateMachine, AgentTaskInput
from app.agent.tools.builtin import build_default_tool_registry
from app.agent.tools.executor import ToolExecutor
from app.api.schemas.tasks import TaskStatusData
from app.storage.agent_stores import SQLAlchemyAgentRunStore
from app.storage.base import Base
from app.storage.models import AgentRun, AgentStep, Project, Task, User
from app.storage.statuses import AgentRunStatus, AgentStepStatus, TaskStatus
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def build_session_factory():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(
        bind=engine,
        tables=[
            User.__table__,
            Project.__table__,
            Task.__table__,
            AgentRun.__table__,
            AgentStep.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_task(
    session_factory,
    *,
    task_id: str = "tsk_agent_001",
    target: str = "https://example.com/product/espresso",
) -> None:
    now = datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            trace_id="trc_agent_001",
            target=target,
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def build_state_machine(session_factory) -> AgentStateMachine:
    return AgentStateMachine(
        run_store=SQLAlchemyAgentRunStore(session_factory=session_factory),
        tool_executor=ToolExecutor(build_default_tool_registry()),
    )


def test_agent_run_store_appends_steps_in_order() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    store = SQLAlchemyAgentRunStore(session_factory=session_factory)

    run = store.create_run(task_id="tsk_agent_001")
    first = store.append_step(
        agent_run_id=run.run_id,
        task_id="tsk_agent_001",
        step_type="thought",
        thought="需要先采集商品页。",
        status=AgentStepStatus.SUCCESS.value,
    )
    second = store.append_step(
        agent_run_id=run.run_id,
        task_id="tsk_agent_001",
        step_type="action",
        tool_name="crawl_product_tool",
        tool_input={"url": "https://example.com/product/espresso"},
    )

    assert first.step_index == 1
    assert second.step_index == 2
    assert [step.step_index for step in store.list_steps(run.run_id)] == [1, 2]


def test_react_state_machine_persists_successful_tool_action_and_observation(tmp_path) -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    state_machine = build_state_machine(session_factory)

    result = state_machine.run(
        AgentTaskInput(
            task_id="tsk_agent_001",
            trace_id="trc_agent_001",
            target="https://example.com/product/espresso",
            source_type="public_url",
            options={
                "artifact_dir": str(tmp_path),
                "fixture_html": """
                    <html>
                      <body>
                        <h1>Portable Espresso Maker</h1>
                        <article class="review" data-review-id="rev-001">
                          <p>The pump stopped working after three days.</p>
                          <span>1 out of 5</span>
                        </article>
                      </body>
                    </html>
                """,
            },
        )
    )

    assert result.status == AgentRunStatus.COMPLETED.value
    assert result.completed_steps == 3
    with session_factory() as session:
        run = session.get(AgentRun, result.run_id)
        steps = session.scalars(
            select(AgentStep).where(AgentStep.agent_run_id == result.run_id).order_by(
                AgentStep.step_index
            )
        ).all()

    assert run is not None
    assert run.status == AgentRunStatus.COMPLETED.value
    assert [step.step_type for step in steps] == ["thought", "action", "observation"]
    assert steps[1].tool_name == "crawl_product_tool"
    assert steps[1].status == AgentStepStatus.SUCCESS.value
    assert steps[1].tool_output["success"] is True
    assert steps[1].tool_output["data"]["title"] == "Portable Espresso Maker"
    assert "Portable Espresso Maker" in (steps[2].observation or "")


def test_react_state_machine_persists_failed_tool_action_without_overwriting_steps(
    tmp_path,
) -> None:
    session_factory = build_session_factory()
    seed_task(
        session_factory,
        task_id="tsk_agent_blocked",
        target="https://example.com/product/blocked",
    )
    state_machine = build_state_machine(session_factory)

    result = state_machine.run(
        AgentTaskInput(
            task_id="tsk_agent_blocked",
            trace_id="trc_agent_blocked",
            target="https://example.com/product/blocked",
            source_type="public_url",
            options={
                "artifact_dir": str(tmp_path),
                "fixture_html": "<html><body><h1>Access Denied</h1><p>captcha</p></body></html>",
            },
        )
    )

    assert result.status == AgentRunStatus.FAILED.value
    with session_factory() as session:
        steps = session.scalars(
            select(AgentStep).where(AgentStep.agent_run_id == result.run_id).order_by(
                AgentStep.step_index
            )
        ).all()

    assert [step.step_index for step in steps] == [1, 2, 3]
    assert steps[1].step_type == "action"
    assert steps[1].status == AgentStepStatus.FAILED.value
    assert steps[1].tool_output["error"]["code"] == "ACCESS_BLOCKED"
    assert steps[2].step_type == "observation"
    assert steps[2].status == AgentStepStatus.FAILED.value
    assert "ACCESS_BLOCKED" in (steps[2].observation or "")


def test_react_state_machine_respects_max_tool_call_limit() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory, task_id="tsk_agent_limit")
    state_machine = AgentStateMachine(
        run_store=SQLAlchemyAgentRunStore(session_factory=session_factory),
        tool_executor=ToolExecutor(build_default_tool_registry()),
        max_tool_calls=0,
    )

    result = state_machine.run(
        AgentTaskInput(
            task_id="tsk_agent_limit",
            trace_id="trc_agent_limit",
            target="https://example.com/product/espresso",
            source_type="public_url",
            options={},
        )
    )

    assert result.status == AgentRunStatus.FAILED.value
    with session_factory() as session:
        steps = session.scalars(
            select(AgentStep).where(AgentStep.agent_run_id == result.run_id).order_by(
                AgentStep.step_index
            )
        ).all()

    assert [step.step_type for step in steps] == ["thought"]
