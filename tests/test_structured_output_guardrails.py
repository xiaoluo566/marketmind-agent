from datetime import UTC, datetime

import pytest
from app.agent.guardrails import (
    AgentToolDecision,
    ReportStructure,
    StructuredOutputGuardrail,
    StructuredOutputGuardrailError,
)
from app.api.schemas.tasks import TaskStatusData
from app.storage.agent_stores import SQLAlchemyAgentRunStore
from app.storage.base import Base
from app.storage.models import AgentRun, Project, Task, User
from app.storage.statuses import TaskStatus
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
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def seed_task(session_factory, task_id: str = "tsk_guard_001") -> None:
    now = datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    ).create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            trace_id="trc_guard_001",
            target="https://example.com/product/espresso",
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            created_at=now,
            updated_at=now,
        )
    )


def test_guardrail_accepts_clean_json_output() -> None:
    guardrail = StructuredOutputGuardrail()

    result = guardrail.parse(
        """
        {
          "thought": "需要先采集商品页。",
          "action": "call_tool",
          "tool_name": "crawl_product_tool",
          "tool_input": {"url": "https://example.com/product/espresso"}
        }
        """,
        schema=AgentToolDecision,
        prompt_name="planner.tool_decision",
    )

    assert result.output.tool_name == "crawl_product_tool"
    assert result.validation_error_count == 0
    assert result.self_heal_count == 0
    assert result.self_healed is False


def test_guardrail_validates_report_structure_schema() -> None:
    guardrail = StructuredOutputGuardrail()

    result = guardrail.parse(
        """
        {
          "title": "Portable Espresso Maker Risk Report",
          "summary": "质量相关差评集中在水泵失效。",
          "sections": ["核心结论", "差评证据", "运营建议"]
        }
        """,
        schema=ReportStructure,
        prompt_name="report.structure",
    )

    assert result.output.title == "Portable Espresso Maker Risk Report"
    assert result.output.sections == ["核心结论", "差评证据", "运营建议"]


def test_guardrail_self_heals_bad_json_and_records_attempts() -> None:
    prompts: list[str] = []

    def repair(prompt: str) -> str:
        prompts.append(prompt)
        return """
        {
          "thought": "原始输出缺少 JSON 包装，修复为工具调用。",
          "action": "call_tool",
          "tool_name": "crawl_product_tool",
          "tool_input": {"url": "https://example.com/product/espresso"}
        }
        """

    guardrail = StructuredOutputGuardrail(max_self_heal_attempts=1)

    result = guardrail.parse(
        "tool_name=crawl_product_tool url=https://example.com/product/espresso",
        schema=AgentToolDecision,
        prompt_name="planner.tool_decision",
        repair=repair,
    )

    assert result.output.tool_name == "crawl_product_tool"
    assert result.validation_error_count == 1
    assert result.self_heal_count == 1
    assert result.self_healed is True
    assert "AgentToolDecision" in prompts[0]
    assert "tool_name=crawl_product_tool" in prompts[0]


def test_guardrail_retries_transient_repair_failure() -> None:
    calls = 0

    def flaky_repair(prompt: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary model timeout")
        return """
        {
          "thought": "第二次修复成功。",
          "action": "call_tool",
          "tool_name": "crawl_product_tool",
          "tool_input": {"url": "https://example.com/product/espresso"}
        }
        """

    guardrail = StructuredOutputGuardrail(max_self_heal_attempts=1, repair_retry_attempts=2)

    result = guardrail.parse(
        "not json",
        schema=AgentToolDecision,
        prompt_name="planner.tool_decision",
        repair=flaky_repair,
    )

    assert calls == 2
    assert result.self_heal_count == 1
    assert result.output.tool_name == "crawl_product_tool"


def test_guardrail_fails_with_original_output_and_error_details() -> None:
    guardrail = StructuredOutputGuardrail(max_self_heal_attempts=1)

    with pytest.raises(StructuredOutputGuardrailError) as exc_info:
        guardrail.parse(
            "```json\n{\"thought\":\"missing action\"}\n```",
            schema=AgentToolDecision,
            prompt_name="planner.tool_decision",
            repair=lambda _prompt: "{\"still\":\"invalid\"}",
        )

    error = exc_info.value
    assert error.prompt_name == "planner.tool_decision"
    assert "missing action" in error.original_output
    assert error.validation_error_count == 2
    assert error.self_heal_count == 0
    assert error.details["attempts"]


def test_agent_run_store_records_guardrail_metrics() -> None:
    session_factory = build_session_factory()
    seed_task(session_factory)
    store = SQLAlchemyAgentRunStore(session_factory=session_factory)
    run = store.create_run(task_id="tsk_guard_001")

    updated = store.record_guardrail_metrics(
        run.run_id,
        validation_error_count=2,
        self_heal_count=1,
    )

    assert updated.validation_error_count == 2
    assert updated.self_heal_count == 1
    with session_factory() as session:
        row = session.get(AgentRun, run.run_id)
    assert row is not None
    assert row.validation_error_count == 2
    assert row.self_heal_count == 1
