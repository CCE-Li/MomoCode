"""auth foundation

Revision ID: 20261110_0001
Revises:
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261110_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=True),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'active'"), nullable=False
        ),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
            "status IN ('active', 'disabled')",
            name=op.f("ck_users_status_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_status"), "users", ["status"], unique=False)

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "timezone", sa.String(length=64), server_default=sa.text("'UTC'"), nullable=False
        ),
        sa.Column("daily_review_limit", sa.Integer(), server_default=sa.text("50"), nullable=False),
        sa.Column(
            "desired_retention",
            sa.Numeric(precision=3, scale=2),
            server_default=sa.text("0.90"),
            nullable=False,
        ),
        sa.Column("theme", sa.String(length=16), server_default=sa.text("'dark'"), nullable=False),
        sa.Column(
            "locale", sa.String(length=16), server_default=sa.text("'zh-CN'"), nullable=False
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
            "daily_review_limit >= 1 AND daily_review_limit <= 500",
            name=op.f("ck_user_preferences_daily_review_limit_range"),
        ),
        sa.CheckConstraint(
            "desired_retention >= 0.70 AND desired_retention <= 0.99",
            name=op.f("ck_user_preferences_desired_retention_range"),
        ),
        sa.CheckConstraint(
            "theme IN ('dark', 'light', 'system')",
            name=op.f("ck_user_preferences_theme_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_preferences_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_preferences")),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_user_sessions_token_hash")),
    )
    op.create_index(
        "ix_user_sessions_user_expires",
        "user_sessions",
        ["user_id", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_sessions_expires",
        "user_sessions",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_sessions_expires", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_expires", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_users_status"), table_name="users")
    op.drop_table("users")
