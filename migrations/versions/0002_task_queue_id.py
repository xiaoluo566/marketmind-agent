"""add queue task id to tasks

Revision ID: 0002_task_queue_id
Revises: 0001_initial_schema
Create Date: 2026-05-25 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_task_queue_id"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("queue_task_id", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "queue_task_id")
