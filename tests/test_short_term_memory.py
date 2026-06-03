from datetime import UTC, datetime

from app.agent.memory import (
    AgentMemoryEntry,
    AgentShortTermMemory,
    InMemoryAgentMemoryStore,
)
from app.agent.state_machine import AgentStateMachine, AgentTaskInput
from app.agent.tools.builtin import build_default_tool_registry
from app.agent.tools.executor import ToolExecutor
from app.api.schemas.tasks import TaskStatusData
from app.storage.agent_stores import AgentStepData, SQLAlchemyAgentRunStore
from app.storage.base import Base
from app.storage.models import AgentRun, AgentStep, Project, Task, User
from app.storage.statuses import AgentStepStatus, TaskStatus
from app.storage.task_stores import SQLAlchemyTaskStatusStore
from sqlalchemy import create_engine
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


def seed_task(session_factory, *, task_id: str = "tsk_memory_001") -> None:
    now = datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            trace_id="trc_memory_001",
            target="https://example.com/product/espresso",
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def test_short_term_memory_keeps_recent_window_and_compacts_older_entries() -> None:
    memory = AgentShortTermMemory(store=InMemoryAgentMemoryStore(), window_size=3)

    for index in range(1, 6):
        memory.append_entry(
            "tsk_memory_001",
            AgentMemoryEntry(
                sequence=index,
                step_type="observation",
                content=f"第 {index} 轮观察：评论里出现了质量问题。",
                evidence_refs=[f"rev-{index:03d}"],
            ),
        )

    snapshot = memory.load_context("tsk_memory_001")

    assert [entry.sequence for entry in snapshot.recent_entries] == [3, 4, 5]
    assert "第 1 轮观察" in snapshot.summary
    assert "第 2 轮观察" in snapshot.summary
    assert snapshot.summary_evidence_refs == ["rev-001", "rev-002"]


def test_short_term_memory_prompt_context_has_stable_budget_and_evidence_refs() -> None:
    memory = AgentShortTermMemory(
        store=InMemoryAgentMemoryStore(),
        window_size=2,
        max_summary_chars=120,
    )

    memory.append_entry(
        "tsk_memory_001",
        AgentMemoryEntry(
            sequence=1,
            step_type="observation",
            content="物流慢、包装破损、客服没有解决问题。" * 20,
            evidence_refs=["rev-slow-shipping", "art-html-001"],
        ),
    )
    memory.append_entry(
        "tsk_memory_001",
        AgentMemoryEntry(
            sequence=2,
            step_type="thought",
            content="下一步应该检索退货相关评论。",
        ),
    )
    memory.append_entry(
        "tsk_memory_001",
        AgentMemoryEntry(
            sequence=3,
            step_type="observation",
            content="最近一轮工具返回 3 条退货证据。",
            evidence_refs=["chk-return-001"],
        ),
    )

    prompt_context = memory.build_prompt_context("tsk_memory_001")

    assert len(prompt_context.summary) <= 120
    assert [entry.sequence for entry in prompt_context.recent_entries] == [2, 3]
    assert prompt_context.evidence_refs == [
        "rev-slow-shipping",
        "art-html-001",
        "chk-return-001",
    ]
    assert "历史摘要" in prompt_context.to_prompt_text()


def test_short_term_memory_can_restore_context_from_persisted_agent_steps() -> None:
    memory = AgentShortTermMemory(store=InMemoryAgentMemoryStore(), window_size=2)
    steps = [
        build_step(step_index=1, step_type="thought", thought="先采集商品页。"),
        build_step(
            step_index=2,
            step_type="action",
            tool_name="crawl_product_tool",
            tool_input={"url": "https://example.com/product/espresso"},
            tool_output={
                "success": True,
                "artifacts": [{"uri": "artifacts/html/page.html", "checksum": "abc"}],
            },
        ),
        build_step(
            step_index=3,
            step_type="observation",
            observation="采集完成，共提取 4 条评论证据。",
            tool_output={"data": {"review_ids": ["rev-001", "rev-002"]}},
        ),
    ]

    snapshot = memory.restore_from_steps(task_id="tsk_memory_001", steps=steps)

    assert [entry.sequence for entry in snapshot.recent_entries] == [2, 3]
    assert snapshot.summary.startswith("step 1 thought")
    assert snapshot.evidence_refs == ["artifact:abc", "rev-001", "rev-002"]


def test_state_machine_updates_short_term_memory_during_react_run(tmp_path) -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    memory = AgentShortTermMemory(store=InMemoryAgentMemoryStore(), window_size=3)
    state_machine = AgentStateMachine(
        run_store=SQLAlchemyAgentRunStore(session_factory=session_factory),
        tool_executor=ToolExecutor(build_default_tool_registry()),
        short_term_memory=memory,
    )

    result = state_machine.run(
        AgentTaskInput(
            task_id="tsk_memory_001",
            trace_id="trc_memory_001",
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
                        </article>
                      </body>
                    </html>
                """,
            },
        )
    )

    snapshot = memory.load_context("tsk_memory_001")

    assert result.completed_steps == 3
    assert [entry.step_type for entry in snapshot.recent_entries] == [
        "thought",
        "action",
        "observation",
    ]
    assert any("Portable Espresso Maker" in entry.content for entry in snapshot.recent_entries)


def build_step(
    *,
    step_index: int,
    step_type: str,
    thought: str | None = None,
    tool_name: str | None = None,
    tool_input: dict | None = None,
    tool_output: dict | None = None,
    observation: str | None = None,
) -> AgentStepData:
    return AgentStepData(
        step_id=f"stp_{step_index}",
        agent_run_id="run_memory_001",
        task_id="tsk_memory_001",
        step_index=step_index,
        step_type=step_type,
        status=AgentStepStatus.SUCCESS.value,
        thought=thought,
        tool_name=tool_name,
        tool_input=tool_input or {},
        tool_output=tool_output or {},
        observation=observation,
        error_message=None,
        started_at=None,
        finished_at=None,
    )
