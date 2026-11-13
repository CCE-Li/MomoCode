"""oj manual linking

Revision ID: 20261110_0005
Revises: 20261110_0004
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261110_0005"
down_revision: str | Sequence[str] | None = "20261110_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "oj_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("handle", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=True),
        sa.Column("credentials_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
            "platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name=op.f("ck_oj_accounts_platform_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_oj_accounts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oj_accounts")),
        sa.UniqueConstraint(
            "user_id",
            "platform",
            "handle",
            name=op.f("uq_oj_accounts_user_platform_handle"),
        ),
    )
    op.create_index("ix_oj_accounts_user", "oj_accounts", ["user_id"], unique=False)

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("oj_account_id", sa.Uuid(), nullable=True),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=True),
        sa.Column("problem_ref", sa.String(length=200), nullable=True),
        sa.Column("problem_url", sa.Text(), nullable=True),
        sa.Column("verdict", sa.String(length=32), nullable=True),
        sa.Column("verdict_raw", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "source",
            sa.String(length=16),
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column("raw_payload", json_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name=op.f("ck_submissions_platform_valid"),
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'oj_sync')",
            name=op.f("ck_submissions_source_valid"),
        ),
        sa.CheckConstraint(
            "verdict IS NULL OR verdict IN "
            "('accepted', 'wrong_answer', 'time_limit_exceeded', "
            "'memory_limit_exceeded', 'runtime_error', 'compilation_error', "
            "'partially_accepted', 'other')",
            name=op.f("ck_submissions_verdict_valid"),
        ),
        sa.CheckConstraint(
            "time_ms IS NULL OR time_ms >= 0",
            name=op.f("ck_submissions_time_non_negative"),
        ),
        sa.CheckConstraint(
            "memory_kb IS NULL OR memory_kb >= 0",
            name=op.f("ck_submissions_memory_non_negative"),
        ),
        sa.ForeignKeyConstraint(
            ["oj_account_id"],
            ["oj_accounts.id"],
            name=op.f("fk_submissions_oj_account_id_oj_accounts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["practice_sessions.id"],
            name=op.f("fk_submissions_session_id_practice_sessions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_submissions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
        sa.UniqueConstraint(
            "user_id",
            "platform",
            "external_id",
            name=op.f("uq_submissions_user_platform_external"),
        ),
    )
    op.create_index(
        "uq_submissions_user_platform_external_active",
        "submissions",
        ["user_id", "platform", "external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
        sqlite_where=sa.text("external_id IS NOT NULL"),
    )
    op.create_index(
        "ix_submissions_user_submitted",
        "submissions",
        ["user_id", "submitted_at"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_session",
        "submissions",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_submissions_user_platform",
        "submissions",
        ["user_id", "platform"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_submissions_user_platform", table_name="submissions")
    op.drop_index("ix_submissions_session", table_name="submissions")
    op.drop_index("ix_submissions_user_submitted", table_name="submissions")
    op.drop_index(
        "uq_submissions_user_platform_external_active",
        table_name="submissions",
    )
    op.drop_table("submissions")
    op.drop_index("ix_oj_accounts_user", table_name="oj_accounts")
    op.drop_table("oj_accounts")
