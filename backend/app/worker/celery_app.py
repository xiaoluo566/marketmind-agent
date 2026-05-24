from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "marketmind_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_default_queue="marketmind",
    task_track_started=True,
    result_expires=3600,
)
