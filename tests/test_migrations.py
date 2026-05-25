from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_has_initial_schema_head() -> None:
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)

    assert script.get_current_head() == "0002_task_queue_id"


def test_initial_migration_enables_pgvector() -> None:
    migration = Path("migrations/versions/0001_initial_schema.py").read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector" in migration
    assert "Vector(1536)" in migration


def test_day7_migration_persists_queue_task_id() -> None:
    migration = Path("migrations/versions/0002_task_queue_id.py").read_text(encoding="utf-8")

    assert "down_revision = \"0001_initial_schema\"" in migration
    assert "queue_task_id" in migration
