import asyncio

from app.api.schemas.tasks import TaskStatusData
from app.core.config import get_settings
from app.crawler import CrawlError, CrawlRequest, crawl_product_page
from app.storage.crawl_stores import CrawlResultStore
from app.storage.statuses import TaskStatus
from app.tasks.dependencies import (
    get_crawl_result_store,
    get_task_event_store,
    get_task_status_store,
)
from app.tasks.event_store import TaskEventStore
from app.tasks.service import build_task_event
from app.tasks.status_store import TaskStatusStore, utc_now
from app.worker.celery_app import celery_app


@celery_app.task(name="marketmind.tasks.process_research_task")
def process_research_task(task_id: str, payload: dict, trace_id: str) -> dict:
    return run_research_task(
        task_id=task_id,
        payload=payload,
        trace_id=trace_id,
        status_store=get_task_status_store(),
        event_store=get_task_event_store(),
        crawl_result_store=get_crawl_result_store(),
    )


def run_research_task(
    task_id: str,
    payload: dict,
    trace_id: str,
    status_store: TaskStatusStore,
    event_store: TaskEventStore,
    crawl_result_store: CrawlResultStore | None = None,
) -> dict:
    current_task = status_store.get(task_id)
    if current_task is None:
        current_task = TaskStatusData(
            task_id=task_id,
            status=TaskStatus.QUEUED.value,
            trace_id=trace_id,
            target=str(payload.get("target", "")),
            mode=str(payload.get("mode", "")),
            priority=str(payload.get("priority", "")),
            source_type=str(payload.get("source_type", "")),
            options=dict(payload.get("options") or {}),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    running_task = current_task.model_copy(
        update={
            "status": TaskStatus.RUNNING.value,
            "started_at": current_task.started_at or utc_now(),
            "updated_at": utc_now(),
        }
    )
    status_store.save(running_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.RUNNING.value,
            event_type="status",
            message="task running",
            payload={},
            trace_id=trace_id,
        )
    )

    crawl_result_payload: dict = {}
    if _should_crawl(payload):
        event_store.append(
            build_task_event(
                task_id=task_id,
                status=TaskStatus.RUNNING.value,
                event_type="crawler",
                message="crawl started",
                payload={"target": running_task.target},
                trace_id=trace_id,
            )
        )
        try:
            crawl_result = asyncio.run(crawl_product_page(_build_crawl_request(task_id, payload)))
        except CrawlError as exc:
            failed_task = running_task.model_copy(
                update={
                    "status": TaskStatus.FAILED.value,
                    "error_code": exc.code.value,
                    "error_message": str(exc),
                    "finished_at": utc_now(),
                    "updated_at": utc_now(),
                }
            )
            status_store.save(failed_task)
            event_store.append(
                build_task_event(
                    task_id=task_id,
                    status=TaskStatus.FAILED.value,
                    event_type="crawler_error",
                    message="crawl failed",
                    payload={
                        "error_code": exc.code.value,
                        "reason": str(exc),
                        "details": exc.details,
                    },
                    trace_id=trace_id,
                )
            )
            return {
                "task_id": task_id,
                "status": failed_task.status,
                "trace_id": trace_id,
                "target": failed_task.target,
                "error_code": failed_task.error_code,
            }

        crawl_result_payload = {
            "url": crawl_result.url,
            "title": crawl_result.title,
            "price": crawl_result.price,
            "rating": crawl_result.rating,
            "source_type": crawl_result.source_type,
            "text_preview": crawl_result.extracted_text[:240],
            "artifacts": [
                artifact.model_dump(mode="json") for artifact in crawl_result.artifacts
            ],
            "reviews": [review.model_dump(mode="json") for review in crawl_result.reviews],
        }
        persisted_crawl = None
        if crawl_result_store is not None:
            try:
                persisted_crawl = crawl_result_store.persist_success(
                    task_id=task_id,
                    result=crawl_result,
                )
            except Exception as exc:
                failed_task = running_task.model_copy(
                    update={
                        "status": TaskStatus.FAILED.value,
                        "error_code": "CRAWL_PERSISTENCE_FAILED",
                        "error_message": str(exc),
                        "finished_at": utc_now(),
                        "updated_at": utc_now(),
                    }
                )
                status_store.save(failed_task)
                event_store.append(
                    build_task_event(
                        task_id=task_id,
                        status=TaskStatus.FAILED.value,
                        event_type="crawler_error",
                        message="crawl persistence failed",
                        payload={
                            "error_code": "CRAWL_PERSISTENCE_FAILED",
                            "reason": str(exc),
                        },
                        trace_id=trace_id,
                    )
                )
                return {
                    "task_id": task_id,
                    "status": failed_task.status,
                    "trace_id": trace_id,
                    "target": failed_task.target,
                    "error_code": failed_task.error_code,
                }
            crawl_result_payload["persisted"] = {
                "product_id": persisted_crawl.product_id,
                "page_id": persisted_crawl.page_id,
                "artifact_ids": persisted_crawl.artifact_ids,
                "review_ids": persisted_crawl.review_ids,
            }
        event_store.append(
            build_task_event(
                task_id=task_id,
                status=TaskStatus.RUNNING.value,
                event_type="crawler",
                message="crawl completed",
                payload=crawl_result_payload,
                trace_id=trace_id,
            )
        )

    completed_task = running_task.model_copy(
        update={
            "status": TaskStatus.COMPLETED.value,
            "finished_at": utc_now(),
            "updated_at": utc_now(),
        }
    )
    status_store.save(completed_task)
    event_store.append(
        build_task_event(
            task_id=task_id,
            status=TaskStatus.COMPLETED.value,
            event_type="status",
            message="task completed",
            payload={"target": completed_task.target, "crawl": crawl_result_payload},
            trace_id=trace_id,
        )
    )

    return {
        "task_id": task_id,
        "status": completed_task.status,
        "trace_id": trace_id,
        "target": completed_task.target,
    }


def _should_crawl(payload: dict) -> bool:
    return str(payload.get("source_type")) == "public_url"


def _build_crawl_request(task_id: str, payload: dict) -> CrawlRequest:
    options = dict(payload.get("options") or {})
    settings = get_settings()
    html = options.get("fixture_html")
    fixture_path = options.get("fixture_path")
    return CrawlRequest(
        task_id=task_id,
        url=str(payload.get("target", "")),
        source_type="html_fixture" if html or fixture_path else "public_url",
        html=html,
        fixture_path=fixture_path,
        artifact_dir=options.get("artifact_dir") or settings.crawler_artifact_dir,
        save_html_artifact=_read_bool_option(
            options.get("save_html_artifact"),
            default=settings.crawler_save_html_artifact,
        ),
        capture_screenshot=_read_bool_option(
            options.get("capture_screenshot"),
            default=settings.crawler_capture_screenshot,
        ),
        timeout_ms=int(options.get("crawl_timeout_ms") or 15_000),
        user_agent=options.get("user_agent"),
    )


def _read_bool_option(value: object, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
