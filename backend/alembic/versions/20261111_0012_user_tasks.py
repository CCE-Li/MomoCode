"""user-created practice tasks

Revision ID: 20261111_0012
Revises: 20261111_0011
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261111_0012"
down_revision: str | Sequence[str] | None = "20261111_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "practice_tasks",
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_practice_tasks_created_by_user_id_users"),
        "practice_tasks",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_practice_tasks_creator",
        "practice_tasks",
        ["created_by_user_id", "is_active"],
        unique=False,
    )
    op.create_check_constraint(
        op.f("ck_practice_tasks_creator_requires_user_source"),
        "practice_tasks",
        "created_by_user_id IS NULL OR source_type = 'user'",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_practice_tasks_creator_requires_user_source"),
        "practice_tasks",
        type_="check",
    )
    op.drop_index("ix_practice_tasks_creator", table_name="practice_tasks")
    op.drop_constraint(
        op.f("fk_practice_tasks_created_by_user_id_users"),
        "practice_tasks",
        type_="foreignkey",
    )
    op.drop_column("practice_tasks", "created_by_user_id")
