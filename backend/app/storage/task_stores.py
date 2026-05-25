from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.tasks import TaskEventData, TaskStatusData
from app.core.config import get_settings
from app.storage.models import Project, Task, TaskEvent, User
from app.tasks.event_store import TaskEventStore, TaskEventStoreUnavailableError
from app.tasks.status_store import TaskStatusStore, TaskStatusStoreUnavailableError


class SQLAlchemyTaskStatusStore:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        default_user_id: str | None = None,
        default_project_id: str | None = None,
        default_project_name: str | None = None,
        default_user_email: str | None = None,
    ) -> None:
        settings = get_settings()
        self._session_factory = session_factory
        self._default_user_id = default_user_id or settings.default_local_user_id
        self._default_project_id = default_project_id or settings.default_local_project_id
        self._default_project_name = default_project_name or settings.default_local_project_name
        self._default_user_email = default_user_email or settings.default_local_user_email

    def create(self, task: TaskStatusData) -> TaskStatusData:
        with self._session_scope() as session:
            with session.begin():
                self._ensure_default_workspace(session)
                task_row = self._upsert_task(session, task)
                session.flush()
                return self._to_data(task_row)

    def save(self, task: TaskStatusData) -> TaskStatusData:
        with self._session_scope() as session:
            with session.begin():
                self._ensure_default_workspace(session)
                task_row = self._upsert_task(session, task)
                session.flush()
                return self._to_data(task_row)

    def get(self, task_id: str) -> TaskStatusData | None:
        with self._session_scope() as session:
            task_row = session.get(Task, task_id)
            if task_row is None:
                return None
            return self._to_data(task_row)

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _ensure_default_workspace(self, session: Session) -> None:
        user = session.get(User, self._default_user_id)
        if user is None:
            session.add(
                User(
                    id=self._default_user_id,
                    email=self._default_user_email,
                    display_name="Local User",
                    role="local",
                )
            )
            session.flush()

        project = session.get(Project, self._default_project_id)
        if project is None:
            session.add(
                Project(
                    id=self._default_project_id,
                    user_id=self._default_user_id,
                    name=self._default_project_name,
                    description="Local development project",
                    settings={},
                )
            )
            session.flush()

    def _upsert_task(self, session: Session, task: TaskStatusData) -> Task:
        task_row = session.get(Task, task.task_id)
        if task_row is None:
            task_row = Task(
                id=task.task_id,
                user_id=self._default_user_id,
                project_id=self._default_project_id,
                target=task.target,
                mode=task.mode,
                status=task.status,
                priority=task.priority,
                source_type=task.source_type,
                trace_id=task.trace_id,
                queue_task_id=task.queue_task_id,
                started_at=task.started_at,
                finished_at=task.finished_at,
                error_code=task.error_code,
                error_message=task.error_message,
                options=task.options,
                created_at=task.created_at,
                updated_at=task.updated_at,
            )
            session.add(task_row)
            return task_row

        task_row.target = task.target
        task_row.mode = task.mode
        task_row.status = task.status
        task_row.priority = task.priority
        task_row.source_type = task.source_type
        task_row.trace_id = task.trace_id
        task_row.queue_task_id = task.queue_task_id
        task_row.started_at = task.started_at
        task_row.finished_at = task.finished_at
        task_row.error_code = task.error_code
        task_row.error_message = task.error_message
        task_row.options = task.options
        task_row.updated_at = task.updated_at
        return task_row

    def _to_data(self, task_row: Task) -> TaskStatusData:
        return TaskStatusData(
            task_id=task_row.id,
            status=task_row.status,
            trace_id=task_row.trace_id,
            target=task_row.target,
            mode=task_row.mode,
            priority=task_row.priority,
            source_type=task_row.source_type,
            options=dict(task_row.options or {}),
            queue_task_id=task_row.queue_task_id,
            error_code=task_row.error_code,
            error_message=task_row.error_message,
            started_at=task_row.started_at,
            finished_at=task_row.finished_at,
            created_at=task_row.created_at,
            updated_at=task_row.updated_at,
        )


class SQLAlchemyTaskEventStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def append(self, event: TaskEventData) -> TaskEventData:
        with self._session_scope() as session:
            with session.begin():
                event_row = session.get(TaskEvent, event.event_id)
                if event_row is None:
                    event_row = TaskEvent(
                        id=event.event_id,
                        task_id=event.task_id,
                        status=event.status,
                        message=event.message,
                        event_type=event.event_type,
                        payload=event.payload,
                        trace_id=event.trace_id,
                        created_at=event.created_at,
                    )
                    session.add(event_row)
                else:
                    event_row.task_id = event.task_id
                    event_row.status = event.status
                    event_row.message = event.message
                    event_row.event_type = event.event_type
                    event_row.payload = event.payload
                    event_row.trace_id = event.trace_id
                    event_row.created_at = event.created_at
                session.flush()
                return self._to_data(event_row)

    def list_for_task(self, task_id: str) -> list[TaskEventData]:
        with self._session_scope() as session:
            stmt = (
                select(TaskEvent)
                .where(TaskEvent.task_id == task_id)
                .order_by(TaskEvent.created_at.asc(), TaskEvent.id.asc())
            )
            rows = session.scalars(stmt).all()
            return [self._to_data(row) for row in rows]

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _to_data(self, event_row: TaskEvent) -> TaskEventData:
        return TaskEventData(
            event_id=event_row.id,
            task_id=event_row.task_id,
            status=event_row.status,
            event_type=event_row.event_type,
            message=event_row.message,
            payload=dict(event_row.payload or {}),
            trace_id=event_row.trace_id,
            created_at=event_row.created_at,
        )


class MirroredTaskStatusStore:
    def __init__(
        self,
        primary: TaskStatusStore,
        secondary: TaskStatusStore,
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    def create(self, task: TaskStatusData) -> TaskStatusData:
        secondary_task = self._secondary.create(task)
        try:
            return self._primary.create(secondary_task)
        except TaskStatusStoreUnavailableError:
            return secondary_task

    def save(self, task: TaskStatusData) -> TaskStatusData:
        secondary_task = self._secondary.save(task)
        try:
            return self._primary.save(secondary_task)
        except TaskStatusStoreUnavailableError:
            return secondary_task

    def get(self, task_id: str) -> TaskStatusData | None:
        try:
            primary_task = self._primary.get(task_id)
        except TaskStatusStoreUnavailableError:
            primary_task = None
        if primary_task is not None:
            return primary_task
        return self._secondary.get(task_id)


class MirroredTaskEventStore:
    def __init__(
        self,
        primary: TaskEventStore,
        secondary: TaskEventStore,
    ) -> None:
        self._primary = primary
        self._secondary = secondary

    def append(self, event: TaskEventData) -> TaskEventData:
        secondary_event = self._secondary.append(event)
        try:
            return self._primary.append(secondary_event)
        except TaskEventStoreUnavailableError:
            return secondary_event

    def list_for_task(self, task_id: str) -> list[TaskEventData]:
        try:
            primary_events = self._primary.list_for_task(task_id)
        except TaskEventStoreUnavailableError:
            primary_events = []
        if primary_events:
            return primary_events
        return self._secondary.list_for_task(task_id)
