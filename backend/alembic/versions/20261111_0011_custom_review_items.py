"""custom review items

Revision ID: 20261111_0011
Revises: 20261111_0010
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261111_0011"
down_revision: str | Sequence[str] | None = "20261111_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
id_type = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "user_review_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("tags", json_type, server_default=sa.text("'[]'"), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_review_items_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_review_items")),
    )
    op.create_index(
        "ix_user_review_items_user_created",
        "user_review_items",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_review_items_user_active",
        "user_review_items",
        ["user_id", "is_active"],
        unique=False,
    )

    op.create_table(
        "user_review_memories",
        sa.Column("id", id_type, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
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
            name=op.f("ck_user_review_memories_state_range"),
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["user_review_items.id"],
            name=op.f("fk_user_review_memories_item_id_user_review_items"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_review_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_review_memories")),
        sa.UniqueConstraint(
            "user_id",
            "item_id",
            name=op.f("uq_user_review_memories_user_item"),
        ),
    )
    op.create_index(
        "ix_user_review_memories_due",
        "user_review_memories",
        ["user_id", "due_at"],
        unique=False,
    )

    op.create_table(
        "user_review_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
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
            name=op.f("ck_user_review_logs_rating_range"),
        ),
        sa.CheckConstraint(
            "review_duration_ms IS NULL OR review_duration_ms >= 0",
            name=op.f("ck_user_review_logs_duration_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["user_review_items.id"],
            name=op.f("fk_user_review_logs_item_id_user_review_items"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_review_logs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_review_logs")),
    )
    op.create_index(
        "ix_user_review_logs_user_time",
        "user_review_logs",
        ["user_id", "reviewed_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_review_logs_user_item_time",
        "user_review_logs",
        ["user_id", "item_id", "reviewed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_review_logs_user_item_time", table_name="user_review_logs")
    op.drop_index("ix_user_review_logs_user_time", table_name="user_review_logs")
    op.drop_table("user_review_logs")

    op.drop_index("ix_user_review_memories_due", table_name="user_review_memories")
    op.drop_table("user_review_memories")

    op.drop_index("ix_user_review_items_user_active", table_name="user_review_items")
    op.drop_index("ix_user_review_items_user_created", table_name="user_review_items")
    op.drop_table("user_review_items")
