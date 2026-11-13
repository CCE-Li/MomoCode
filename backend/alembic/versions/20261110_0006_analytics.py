"""analytics stats

Revision ID: 20261110_0006
Revises: 20261110_0005
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261110_0006"
down_revision: str | Sequence[str] | None = "20261110_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "user_skill_stats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column("sample_size", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("correctness_rate", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("independence_score", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("hint_dependency", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("avg_normalized_time", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column(
            "error_distribution",
            json_type,
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("skill_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "score_version",
            sa.String(length=32),
            server_default=sa.text("'skill-score-v0'"),
            nullable=False,
        ),
        sa.Column(
            "insufficient_data",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_user_skill_stats_skill_id_skills"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_skill_stats_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_skill_stats")),
        sa.UniqueConstraint(
            "user_id",
            "skill_id",
            name=op.f("uq_user_skill_stats_user_skill"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_skill_stats")
