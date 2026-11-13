"""task hashtag tags

Revision ID: 20261111_0013
Revises: 20261111_0012
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261111_0013"
down_revision: str | Sequence[str] | None = "20261111_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "task_tags",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["practice_tasks.id"],
            name=op.f("fk_task_tags_task_id_practice_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "tag", name=op.f("pk_task_tags")),
    )
    op.create_index("ix_task_tags_tag", "task_tags", ["tag"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_tags_tag", table_name="task_tags")
    op.drop_table("task_tags")
