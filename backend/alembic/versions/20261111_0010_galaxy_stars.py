"""galaxy star state

Revision ID: 20261111_0010
Revises: 20261111_0009
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261111_0010"
down_revision: str | Sequence[str] | None = "20261111_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_skill_stats",
        sa.Column(
            "star_state",
            sa.String(length=16),
            server_default=sa.text("'dark'"),
            nullable=False,
        ),
    )
    op.add_column(
        "user_skill_stats",
        sa.Column("star_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_user_skill_stats_star_state_valid"),
        "user_skill_stats",
        "star_state IN ('dark', 'lit')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_user_skill_stats_star_state_valid"),
        "user_skill_stats",
        type_="check",
    )
    op.drop_column("user_skill_stats", "star_updated_at")
    op.drop_column("user_skill_stats", "star_state")
