"""practice session draft code

Revision ID: 20261112_0014
Revises: 20261111_0013
Create Date: 2026-11-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261112_0014"
down_revision: str | Sequence[str] | None = "20261111_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "practice_sessions",
        sa.Column("draft_code", sa.Text(), nullable=True),
    )
    op.add_column(
        "practice_sessions",
        sa.Column(
            "draft_saved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("practice_sessions", "draft_saved_at")
    op.drop_column("practice_sessions", "draft_code")
