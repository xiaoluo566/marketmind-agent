from app.core.config import get_settings
from app.worker.celery_app import celery_app
from app.worker.tasks import process_research_task


def test_celery_uses_redis_configuration_from_settings() -> None:
    settings = get_settings()

    assert celery_app.conf.broker_url == settings.celery_broker_url
    assert celery_app.conf.result_backend == settings.celery_result_backend
    assert celery_app.conf.task_default_queue == "marketmind"


def test_minimal_research_task_is_registered() -> None:
    assert process_research_task.name == "marketmind.tasks.process_research_task"
    assert "marketmind.tasks.process_research_task" in celery_app.tasks
