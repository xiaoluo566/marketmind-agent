from __future__ import annotations

from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_prefixed_id
from app.storage.base import Base
from app.storage.statuses import AgentRunStatus, AgentStepStatus, TaskStatus


def new_id(prefix: str) -> str:
    return new_prefixed_id(prefix)


def utc_now() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("usr"))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    display_name: Mapped[str] = mapped_column(String(120), default="Local User")
    role: Mapped[str] = mapped_column(String(32), default="local")

    projects: Mapped[list[Project]] = relationship(back_populates="user")
    tasks: Mapped[list[Task]] = relationship(back_populates="user")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("prj"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), default="Default Project")
    description: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="projects")
    tasks: Mapped[list[Task]] = relationship(back_populates="project")


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_status_created_at", "status", "created_at"),
        Index("ix_tasks_trace_id", "trace_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("tsk"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    target: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.RECEIVED.value)
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    source_type: Mapped[str] = mapped_column(String(32), default="demo_dataset")
    trace_id: Mapped[str] = mapped_column(String(80), nullable=False)
    queue_task_id: Mapped[str | None] = mapped_column(String(120))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    options: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped[User] = relationship(back_populates="tasks")
    project: Mapped[Project] = relationship(back_populates="tasks")
    events: Mapped[list[TaskEvent]] = relationship(back_populates="task")
    agent_runs: Mapped[list[AgentRun]] = relationship(back_populates="task")
    products: Mapped[list[Product]] = relationship(back_populates="task")
    reviews: Mapped[list[Review]] = relationship(back_populates="task")
    review_chunks: Mapped[list[ReviewChunk]] = relationship(back_populates="task")
    reports: Mapped[list[Report]] = relationship(back_populates="task")


class TaskEvent(Base):
    __tablename__ = "task_events"
    __table_args__ = (Index("ix_task_events_task_id_created_at", "task_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("evt"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="status")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    trace_id: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    task: Mapped[Task] = relationship(back_populates="events")


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("run"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=AgentRunStatus.PENDING.value)
    model_provider: Mapped[str] = mapped_column(String(80), default="openai-compatible")
    model_name: Mapped[str] = mapped_column(String(120), default="gpt-5.4-mini")
    report_model_name: Mapped[str] = mapped_column(String(120), default="gpt-5.5")
    prompt_version: Mapped[str] = mapped_column(String(80), default="v1")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    validation_error_count: Mapped[int] = mapped_column(Integer, default=0)
    self_heal_count: Mapped[int] = mapped_column(Integer, default=0)

    task: Mapped[Task] = relationship(back_populates="agent_runs")
    steps: Mapped[list[AgentStep]] = relationship(back_populates="agent_run")


class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = (
        Index("ix_agent_steps_agent_run_id_step_index", "agent_run_id", "step_index"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("stp"))
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    thought: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(120))
    tool_input: Mapped[dict] = mapped_column(JSON, default=dict)
    tool_output: Mapped[dict] = mapped_column(JSON, default=dict)
    observation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=AgentStepStatus.PENDING.value)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    agent_run: Mapped[AgentRun] = relationship(back_populates="steps")


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("prd"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(12))
    rating: Mapped[float | None] = mapped_column(Float)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    task: Mapped[Task] = relationship(back_populates="products")
    pages: Mapped[list[CrawledPage]] = relationship(back_populates="product")
    reviews: Mapped[list[Review]] = relationship(back_populates="product")


class CrawledPage(TimestampMixin, Base):
    __tablename__ = "crawled_pages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("pg"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer)
    html_artifact_id: Mapped[str | None] = mapped_column(String(64))
    screenshot_artifact_id: Mapped[str | None] = mapped_column(String(64))
    extracted_text: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    product: Mapped[Product | None] = relationship(back_populates="pages")


class Review(TimestampMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_product_id", "product_id"),
        Index("ix_reviews_task_id", "task_id"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("rev"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(160))
    source_url: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), default="manual_upload")
    rating: Mapped[float | None] = mapped_column(Float)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_hash: Mapped[str | None] = mapped_column(String(160))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    product: Mapped[Product] = relationship(back_populates="reviews")
    task: Mapped[Task] = relationship(back_populates="reviews")
    chunks: Mapped[list[ReviewChunk]] = relationship(back_populates="review")


class ReviewChunk(TimestampMixin, Base):
    __tablename__ = "review_chunks"
    __table_args__ = (
        Index("ix_review_chunks_task_id", "task_id"),
        Index(
            "ix_review_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("chk"))
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    embedding_model: Mapped[str] = mapped_column(String(120), default="text-embedding-3-small")
    embedding_dimensions: Mapped[int] = mapped_column(Integer, default=1536)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    review: Mapped[Review] = relationship(back_populates="chunks")
    task: Mapped[Task] = relationship(back_populates="review_chunks")


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("rpt"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    summary: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    evidence_refs: Mapped[list] = mapped_column(JSON, default=list)
    schema_version: Mapped[str] = mapped_column(String(32), default="v1")

    task: Mapped[Task] = relationship(back_populates="reports")


class Artifact(TimestampMixin, Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("art"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(120))
    checksum: Mapped[str | None] = mapped_column(String(160))
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class ErrorLog(Base):
    __tablename__ = "error_logs"
    __table_args__ = (Index("ix_error_logs_task_id_created_at", "task_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("err"))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    trace_id: Mapped[str | None] = mapped_column(String(80))
    layer: Mapped[str] = mapped_column(String(64), nullable=False)
    error_code: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


__all__ = [
    "AgentRun",
    "AgentStep",
    "Artifact",
    "CrawledPage",
    "ErrorLog",
    "Product",
    "Project",
    "Report",
    "Review",
    "ReviewChunk",
    "Task",
    "TaskEvent",
    "User",
]
