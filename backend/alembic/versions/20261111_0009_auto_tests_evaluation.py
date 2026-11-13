"""allow auto_tests evaluation mode

Revision ID: 20261111_0009
Revises: 20261110_0008
Create Date: 2026-11-11
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261111_0009"
down_revision: str | Sequence[str] | None = "20261110_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("ck_practice_tasks_evaluation_mode_valid"),
        "practice_tasks",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_practice_tasks_evaluation_mode_valid"),
        "practice_tasks",
        "evaluation_mode IN ('auto_recognition', 'self_assessment', 'auto_tests')",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_practice_tasks_evaluation_mode_valid"),
        "practice_tasks",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_practice_tasks_evaluation_mode_valid"),
        "practice_tasks",
        "evaluation_mode IN ('auto_recognition', 'self_assessment')",
    )
