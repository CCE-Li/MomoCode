"""practice engine

Revision ID: 20261110_0003
Revises: 20261110_0002
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261110_0003"
down_revision: str | Sequence[str] | None = "20261110_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("task_snapshot", json_type, nullable=False),
        sa.Column("training_type", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'created'"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_spent_ms", sa.Integer(), nullable=True),
        sa.Column("answer_payload", json_type, nullable=True),
        sa.Column("auto_grade", json_type, nullable=True),
        sa.Column("self_assessment", sa.String(length=16), nullable=True),
        sa.Column("self_assessment_note", sa.Text(), nullable=True),
        sa.Column(
            "max_hint_level",
            sa.SmallInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "error_types",
            json_type,
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "mark_as_review",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "training_type IN ('recognition', 'template', 'variant', 'correction')",
            name=op.f("ck_practice_sessions_training_type_valid"),
        ),
        sa.CheckConstraint(
            "mode IN ('review', 'free')",
            name=op.f("ck_practice_sessions_mode_valid"),
        ),
        sa.CheckConstraint(
            "status IN ('created', 'in_progress', 'submitted', 'completed', 'abandoned')",
            name=op.f("ck_practice_sessions_status_valid"),
        ),
        sa.CheckConstraint(
            "self_assessment IS NULL OR self_assessment IN ('correct', 'partial', 'incorrect')",
            name=op.f("ck_practice_sessions_self_assessment_valid"),
        ),
        sa.CheckConstraint(
            "max_hint_level >= 0 AND max_hint_level <= 5",
            name=op.f("ck_practice_sessions_max_hint_level_range"),
        ),
        sa.CheckConstraint(
            "time_spent_ms IS NULL OR time_spent_ms >= 0",
            name=op.f("ck_practice_sessions_time_spent_non_negative"),
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
            name=op.f("ck_practice_sessions_completed_after_started"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["practice_tasks.id"],
            name=op.f("fk_practice_sessions_task_id_practice_tasks"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_practice_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_practice_sessions")),
    )
    op.create_index(
        "ix_practice_sessions_user_created",
        "practice_sessions",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_practice_sessions_user_status",
        "practice_sessions",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_practice_sessions_task",
        "practice_sessions",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_practice_sessions_user_type",
        "practice_sessions",
        ["user_id", "training_type", "created_at"],
        unique=False,
    )

    op.create_table(
        "session_hints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("level", sa.SmallInteger(), nullable=False),
        sa.Column("content_snapshot", json_type, nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "level >= 1 AND level <= 5",
            name=op.f("ck_session_hints_level_range"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["practice_sessions.id"],
            name=op.f("fk_session_hints_session_id_practice_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_hints")),
        sa.UniqueConstraint(
            "session_id",
            "level",
            name=op.f("uq_session_hints_session_level"),
        ),
    )
    op.create_index(
        "ix_session_hints_session",
        "session_hints",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_session_hints_session", table_name="session_hints")
    op.drop_table("session_hints")
    op.drop_index("ix_practice_sessions_user_type", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_task", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_user_status", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_user_created", table_name="practice_sessions")
    op.drop_table("practice_sessions")
