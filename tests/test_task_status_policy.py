import pytest
from app.storage.status_policy import (
    TERMINAL_TASK_STATUSES,
    can_transition_task_status,
    ensure_task_status_transition,
)
from app.storage.statuses import TaskStatus


@pytest.mark.parametrize(
    ("current", "next_status"),
    [
        (TaskStatus.RECEIVED.value, TaskStatus.QUEUED.value),
        (TaskStatus.QUEUED.value, TaskStatus.RUNNING.value),
        (TaskStatus.RUNNING.value, TaskStatus.COMPLETED.value),
        (TaskStatus.RUNNING.value, TaskStatus.FAILED.value),
        (TaskStatus.FAILED.value, TaskStatus.WAITING_RETRY.value),
        (TaskStatus.WAITING_RETRY.value, TaskStatus.QUEUED.value),
    ],
)
def test_can_transition_task_status_allows_expected_lifecycle_edges(
    current: str,
    next_status: str,
) -> None:
    assert can_transition_task_status(current, next_status) is True
    assert ensure_task_status_transition(current, next_status) == next_status


@pytest.mark.parametrize(
    ("current", "next_status"),
    [
        (TaskStatus.RECEIVED.value, TaskStatus.COMPLETED.value),
        (TaskStatus.QUEUED.value, TaskStatus.RECEIVED.value),
        (TaskStatus.COMPLETED.value, TaskStatus.RUNNING.value),
        (TaskStatus.CANCELLED.value, TaskStatus.QUEUED.value),
    ],
)
def test_can_transition_task_status_blocks_invalid_or_terminal_edges(
    current: str,
    next_status: str,
) -> None:
    assert can_transition_task_status(current, next_status) is False
    with pytest.raises(ValueError, match="invalid task status transition"):
        ensure_task_status_transition(current, next_status)


def test_terminal_task_statuses_are_explicit() -> None:
    assert TERMINAL_TASK_STATUSES == {
        TaskStatus.COMPLETED.value,
        TaskStatus.CANCELLED.value,
    }
