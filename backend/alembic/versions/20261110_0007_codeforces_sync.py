"""codeforces sync

Revision ID: 20261110_0007
Revises: 20261110_0006
Create Date: 2026-11-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261110_0007"
down_revision: str | Sequence[str] | None = "20261110_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "oj_accounts",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("oj_accounts", "last_synced_at")
