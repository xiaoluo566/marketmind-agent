from app.storage.statuses import TaskStatus

TERMINAL_TASK_STATUSES = {
    TaskStatus.COMPLETED.value,
    TaskStatus.CANCELLED.value,
}

ALLOWED_TASK_STATUS_TRANSITIONS = {
    TaskStatus.RECEIVED.value: {
        TaskStatus.QUEUED.value,
        TaskStatus.FAILED.value,
        TaskStatus.CANCELLED.value,
    },
    TaskStatus.QUEUED.value: {
        TaskStatus.RUNNING.value,
        TaskStatus.FAILED.value,
        TaskStatus.CANCELLED.value,
    },
    TaskStatus.RUNNING.value: {
        TaskStatus.COMPLETED.value,
        TaskStatus.FAILED.value,
        TaskStatus.CANCELLED.value,
    },
    TaskStatus.FAILED.value: {
        TaskStatus.WAITING_RETRY.value,
    },
    TaskStatus.WAITING_RETRY.value: {
        TaskStatus.QUEUED.value,
        TaskStatus.FAILED.value,
        TaskStatus.CANCELLED.value,
    },
    TaskStatus.COMPLETED.value: set(),
    TaskStatus.CANCELLED.value: set(),
}


def can_transition_task_status(current: str, next_status: str) -> bool:
    if current == next_status:
        return True
    return next_status in ALLOWED_TASK_STATUS_TRANSITIONS.get(current, set())


def ensure_task_status_transition(current: str, next_status: str) -> str:
    if can_transition_task_status(current, next_status):
        return next_status
    raise ValueError(f"invalid task status transition: {current} -> {next_status}")
