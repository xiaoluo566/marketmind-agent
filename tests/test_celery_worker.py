from app.api.schemas.tasks import TaskStatusData
from app.core.config import get_settings
from app.storage.statuses import TaskStatus
from app.tasks.event_store import InMemoryTaskEventStore
from app.tasks.status_store import InMemoryTaskStatusStore, utc_now
from app.worker.celery_app import celery_app
from app.worker.tasks import process_research_task, run_research_task


def test_celery_uses_redis_configuration_from_settings() -> None:
    settings = get_settings()

    assert celery_app.conf.broker_url == settings.celery_broker_url
    assert celery_app.conf.result_backend == settings.celery_result_backend
    assert celery_app.conf.task_default_queue == "marketmind"


def test_minimal_research_task_is_registered() -> None:
    assert process_research_task.name == "marketmind.tasks.process_research_task"
    assert "marketmind.tasks.process_research_task" in celery_app.tasks


def test_minimal_research_task_advances_status_to_completed() -> None:
    store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    created_at = utc_now()
    task_id = "tsk_worker_unit"
    store.create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            trace_id="trc_worker_unit",
            target="demo://portable-espresso-maker-negative-reviews",
            mode="competitive_research",
            priority="normal",
            source_type="demo_dataset",
            options={},
            queue_task_id="celery_worker_unit",
            created_at=created_at,
            updated_at=created_at,
        )
    )
    result = run_research_task(
        task_id=task_id,
        payload={
            "target": "demo://portable-espresso-maker-negative-reviews",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "demo_dataset",
            "options": {},
        },
        trace_id="trc_worker_unit",
        status_store=store,
        event_store=event_store,
    )

    stored_task = store.get(task_id)
    assert stored_task is not None
    assert stored_task.status == TaskStatus.COMPLETED.value
    assert result["status"] == TaskStatus.COMPLETED.value
    assert result["task_id"] == task_id
    assert [event.status for event in event_store.list_for_task(task_id)] == [
        TaskStatus.RUNNING.value,
        TaskStatus.COMPLETED.value,
    ]


def test_public_url_task_runs_crawler_and_records_crawl_event(tmp_path) -> None:
    store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    created_at = utc_now()
    task_id = "tsk_worker_crawl"
    store.create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            trace_id="trc_worker_crawl",
            target="https://example.com/product/espresso",
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            queue_task_id="celery_worker_crawl",
            created_at=created_at,
            updated_at=created_at,
        )
    )

    result = run_research_task(
        task_id=task_id,
        payload={
            "target": "https://example.com/product/espresso",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "artifact_dir": str(tmp_path),
                "fixture_html": """
                    <html>
                      <body>
                        <h1>Portable Espresso Maker</h1>
                        <p>Travel ready.</p>
                        <p>$39.99</p>
                        <p>4.6 out of 5</p>
                      </body>
                    </html>
                """,
            },
        },
        trace_id="trc_worker_crawl",
        status_store=store,
        event_store=event_store,
    )

    stored_task = store.get(task_id)
    events = event_store.list_for_task(task_id)

    assert stored_task is not None
    assert stored_task.status == TaskStatus.COMPLETED.value
    assert result["status"] == TaskStatus.COMPLETED.value
    assert [event.message for event in events] == [
        "task running",
        "crawl started",
        "crawl completed",
        "task completed",
    ]
    assert events[2].payload["title"] == "Portable Espresso Maker"
    assert events[2].payload["price"] == 39.99
    assert events[2].payload["artifacts"][0]["artifact_type"] == "crawler_html"


def test_public_url_task_marks_failed_when_crawler_is_blocked(tmp_path) -> None:
    store = InMemoryTaskStatusStore()
    event_store = InMemoryTaskEventStore()
    created_at = utc_now()
    task_id = "tsk_worker_crawl_blocked"
    store.create(
        TaskStatusData(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            trace_id="trc_worker_crawl_blocked",
            target="https://example.com/product/blocked",
            mode="competitive_research",
            priority="normal",
            source_type="public_url",
            options={},
            queue_task_id="celery_worker_crawl_blocked",
            created_at=created_at,
            updated_at=created_at,
        )
    )

    result = run_research_task(
        task_id=task_id,
        payload={
            "target": "https://example.com/product/blocked",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "artifact_dir": str(tmp_path),
                "fixture_html": "<html><body><h1>Access Denied</h1><p>captcha</p></body></html>",
            },
        },
        trace_id="trc_worker_crawl_blocked",
        status_store=store,
        event_store=event_store,
    )

    stored_task = store.get(task_id)
    events = event_store.list_for_task(task_id)

    assert stored_task is not None
    assert stored_task.status == TaskStatus.FAILED.value
    assert stored_task.error_code == "ACCESS_BLOCKED"
    assert result["status"] == TaskStatus.FAILED.value
    assert [event.message for event in events] == [
        "task running",
        "crawl started",
        "crawl failed",
    ]
    assert events[-1].payload["error_code"] == "ACCESS_BLOCKED"
    assert events[-1].payload["details"]["artifacts"][0]["artifact_type"] == (
        "crawler_failure_html"
    )
