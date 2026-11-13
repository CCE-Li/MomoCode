"""fsrs scheduling

Revision ID: 20261110_0004
Revises: 20261110_0003
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261110_0004"
down_revision: str | Sequence[str] | None = "20261110_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
id_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "skill_memories",
        sa.Column("id", id_type, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("step", sa.SmallInteger(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column(
            "due_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_review_at", sa.DateTime(timezone=True), nullable=True),
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
            "state >= 1 AND state <= 3",
            name=op.f("ck_skill_memories_state_range"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_skill_memories_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_skill_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_memories")),
        sa.UniqueConstraint(
            "user_id",
            "skill_id",
            name=op.f("uq_skill_memories_user_skill"),
        ),
    )
    op.create_index(
        "ix_skill_memories_due",
        "skill_memories",
        ["user_id", "due_at"],
        unique=False,
    )
    op.create_index(
        "ix_skill_memories_skill",
        "skill_memories",
        ["skill_id"],
        unique=False,
    )

    op.create_table(
        "review_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("review_duration_ms", sa.Integer(), nullable=True),
        sa.Column("scheduler_version", sa.String(length=64), nullable=False),
        sa.Column("mapping_version", sa.String(length=64), nullable=False),
        sa.Column("evidence_snapshot", json_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 4",
            name=op.f("ck_review_logs_rating_range"),
        ),
        sa.CheckConstraint(
            "review_duration_ms IS NULL OR review_duration_ms >= 0",
            name=op.f("ck_review_logs_duration_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["practice_sessions.id"],
            name=op.f("fk_review_logs_session_id_practice_sessions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_review_logs_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_review_logs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_logs")),
    )
    op.create_index(
        "uq_review_logs_session",
        "review_logs",
        ["session_id"],
        unique=True,
        postgresql_where=sa.text("session_id IS NOT NULL"),
        sqlite_where=sa.text("session_id IS NOT NULL"),
    )
    op.create_index(
        "ix_review_logs_user_skill_time",
        "review_logs",
        ["user_id", "skill_id", "reviewed_at"],
        unique=False,
    )
    op.create_index(
        "ix_review_logs_user_time",
        "review_logs",
        ["user_id", "reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_logs_user_time", table_name="review_logs")
    op.drop_index("ix_review_logs_user_skill_time", table_name="review_logs")
    op.drop_index("uq_review_logs_session", table_name="review_logs")
    op.drop_table("review_logs")
    op.drop_index("ix_skill_memories_skill", table_name="skill_memories")
    op.drop_index("ix_skill_memories_due", table_name="skill_memories")
    op.drop_table("skill_memories")
