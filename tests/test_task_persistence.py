from datetime import UTC, datetime, timedelta

from app.api.schemas.tasks import TaskEventData, TaskStatusData
from app.storage.base import Base
from app.storage.models import Project, Task, TaskEvent, User
from app.storage.task_stores import (
    MirroredTaskEventStore,
    MirroredTaskStatusStore,
    SQLAlchemyTaskEventStore,
    SQLAlchemyTaskStatusStore,
)
from app.tasks.event_store import TaskEventStoreUnavailableError
from app.tasks.status_store import TaskStatusStoreUnavailableError
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
            TaskEvent.__table__,
        ],
    )
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def build_task_status(status: str = "received") -> TaskStatusData:
    now = datetime(2026, 5, 25, 10, 0, tzinfo=UTC)
    return TaskStatusData(
        task_id="tsk_persist_001",
        status=status,
        trace_id="trc_persist_001",
        target="demo product",
        mode="competitive_research",
        priority="normal",
        source_type="demo_dataset",
        options={"dataset": "sample"},
        created_at=now,
        updated_at=now,
    )


class FailingPrimaryStatusStore:
    def create(self, task: TaskStatusData) -> TaskStatusData:
        raise TaskStatusStoreUnavailableError("redis status store is unavailable")

    def save(self, task: TaskStatusData) -> TaskStatusData:
        raise TaskStatusStoreUnavailableError("redis status store is unavailable")

    def get(self, task_id: str) -> TaskStatusData | None:
        raise TaskStatusStoreUnavailableError("redis status store is unavailable")


class FailingPrimaryEventStore:
    def append(self, event: TaskEventData) -> TaskEventData:
        raise TaskEventStoreUnavailableError("redis event store is unavailable")

    def list_for_task(self, task_id: str) -> list[TaskEventData]:
        raise TaskEventStoreUnavailableError("redis event store is unavailable")


def test_sqlalchemy_status_store_creates_default_workspace_and_task() -> None:
    session_factory = build_session_factory()
    store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )

    created = store.create(build_task_status())

    assert created.task_id == "tsk_persist_001"
    with session_factory() as session:
        assert session.get(User, "usr_local") is not None
        assert session.get(Project, "prj_default") is not None
        task = session.get(Task, "tsk_persist_001")

    assert task is not None
    assert task.status == "received"
    assert task.options == {"dataset": "sample"}


def test_sqlalchemy_status_store_updates_task_lifecycle_fields() -> None:
    session_factory = build_session_factory()
    store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )

    created = store.create(build_task_status())
    queued = created.model_copy(
        update={
            "status": "queued",
            "queue_task_id": "celery-task-001",
            "updated_at": created.updated_at + timedelta(seconds=1),
        }
    )
    store.save(queued)

    persisted = store.get("tsk_persist_001")

    assert persisted is not None
    assert persisted.status == "queued"
    assert persisted.queue_task_id == "celery-task-001"
    with session_factory() as session:
        task = session.get(Task, "tsk_persist_001")
    assert task is not None
    assert task.queue_task_id == "celery-task-001"


def test_sqlalchemy_event_store_appends_and_lists_task_events_in_order() -> None:
    session_factory = build_session_factory()
    status_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    event_store = SQLAlchemyTaskEventStore(session_factory=session_factory)
    status_store.create(build_task_status())

    first = TaskEventData(
        event_id="evt_first",
        task_id="tsk_persist_001",
        status="received",
        event_type="status",
        message="task received",
        payload={"source": "api"},
        trace_id="trc_persist_001",
        created_at=datetime(2026, 5, 25, 10, 0, tzinfo=UTC),
    )
    second = first.model_copy(
        update={
            "event_id": "evt_second",
            "status": "queued",
            "message": "task queued",
            "created_at": datetime(2026, 5, 25, 10, 1, tzinfo=UTC),
        }
    )

    event_store.append(second)
    event_store.append(first)

    events = event_store.list_for_task("tsk_persist_001")

    assert [event.event_id for event in events] == ["evt_first", "evt_second"]
    with session_factory() as session:
        persisted_count = len(session.scalars(select(TaskEvent)).all())
    assert persisted_count == 2


def test_mirrored_status_store_keeps_durable_write_when_realtime_store_is_down() -> None:
    session_factory = build_session_factory()
    database_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    mirrored_store = MirroredTaskStatusStore(
        primary=FailingPrimaryStatusStore(),
        secondary=database_store,
    )

    created = mirrored_store.create(build_task_status())
    persisted = mirrored_store.get("tsk_persist_001")

    assert created.task_id == "tsk_persist_001"
    assert persisted is not None
    assert persisted.status == "received"


def test_mirrored_event_store_keeps_durable_event_when_realtime_store_is_down() -> None:
    session_factory = build_session_factory()
    status_store = SQLAlchemyTaskStatusStore(
        session_factory=session_factory,
        default_user_id="usr_local",
        default_project_id="prj_default",
    )
    database_event_store = SQLAlchemyTaskEventStore(session_factory=session_factory)
    mirrored_event_store = MirroredTaskEventStore(
        primary=FailingPrimaryEventStore(),
        secondary=database_event_store,
    )
    status_store.create(build_task_status())
    event = TaskEventData(
        event_id="evt_realtime_down",
        task_id="tsk_persist_001",
        status="received",
        event_type="status",
        message="task received",
        payload={},
        trace_id="trc_persist_001",
        created_at=datetime(2026, 5, 25, 10, 0, tzinfo=UTC),
    )

    appended = mirrored_event_store.append(event)
    events = mirrored_event_store.list_for_task("tsk_persist_001")

    assert appended.event_id == "evt_realtime_down"
    assert [stored.event_id for stored in events] == ["evt_realtime_down"]
