from app.storage.base import Base
from app.storage.models import (
    AgentRun,
    AgentStep,
    Product,
    Report,
    Review,
    ReviewChunk,
    Task,
)
from app.storage.statuses import AgentRunStatus, AgentStepStatus, TaskStatus
from sqlalchemy import Index


def test_day3_core_tables_are_registered() -> None:
    expected_tables = {
        "users",
        "projects",
        "tasks",
        "task_events",
        "agent_runs",
        "agent_steps",
        "products",
        "crawled_pages",
        "reviews",
        "review_chunks",
        "reports",
        "artifacts",
        "error_logs",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_task_and_agent_status_defaults_match_state_machine() -> None:
    assert Task.status.default.arg == TaskStatus.RECEIVED.value
    assert AgentRun.status.default.arg == AgentRunStatus.PENDING.value
    assert AgentStep.status.default.arg == AgentStepStatus.PENDING.value


def test_agent_step_keeps_update_timestamp_for_resume_tracking() -> None:
    assert AgentStep.__table__.c.created_at.nullable is False
    assert AgentStep.__table__.c.updated_at.nullable is False
    assert AgentStep.__table__.c.updated_at.onupdate is not None


def test_day3_required_foreign_keys_are_present() -> None:
    foreign_keys = {
        fk.target_fullname
        for table in Base.metadata.tables.values()
        for column in table.columns
        for fk in column.foreign_keys
    }

    assert "users.id" in foreign_keys
    assert "projects.id" in foreign_keys
    assert "tasks.id" in foreign_keys
    assert "agent_runs.id" in foreign_keys
    assert "products.id" in foreign_keys
    assert "reviews.id" in foreign_keys


def test_vector_embedding_dimension_is_frozen_to_1536() -> None:
    embedding_column = ReviewChunk.__table__.c.embedding

    assert str(embedding_column.type) == "VECTOR(1536)"
    assert ReviewChunk.__table__.c.embedding_dimensions.default.arg == 1536
    assert ReviewChunk.__table__.c.embedding_model.default.arg == "text-embedding-3-small"


def test_day3_indexes_cover_status_timelines_and_vector_search() -> None:
    indexes: dict[str, Index] = {
        index.name: index for table in Base.metadata.tables.values() for index in table.indexes
    }

    for index_name in (
        "ix_tasks_status_created_at",
        "ix_task_events_task_id_created_at",
        "ix_agent_steps_agent_run_id_step_index",
        "ix_reviews_product_id",
        "ix_review_chunks_task_id",
        "ix_review_chunks_embedding_hnsw",
    ):
        assert index_name in indexes


def test_report_can_link_back_to_task_and_evidence() -> None:
    assert Report.__table__.c.task_id.foreign_keys
    assert Report.__table__.c.evidence_refs.nullable is False
    assert Product.__table__.c.task_id.foreign_keys
    assert Review.__table__.c.source_url.nullable is True
