"""content catalog

Revision ID: 20261110_0002
Revises: 20261110_0001
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261110_0002"
down_revision: str | Sequence[str] | None = "20261110_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "algorithm_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_algorithm_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_algorithm_categories_slug")),
    )
    op.create_index(
        "ix_algorithm_categories_sort",
        "algorithm_categories",
        ["sort_order"],
        unique=False,
    )

    op.create_table(
        "algorithms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description_md", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("prerequisites", json_type, server_default=sa.text("'[]'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5",
            name=op.f("ck_algorithms_difficulty_range"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["algorithm_categories.id"],
            name=op.f("fk_algorithms_category_id_algorithm_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_algorithms")),
        sa.UniqueConstraint("slug", name=op.f("uq_algorithms_slug")),
    )
    op.create_index(
        "ix_algorithms_category_difficulty",
        "algorithms",
        ["category_id", "difficulty"],
        unique=False,
    )

    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("algorithm_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("skill_type", sa.String(length=32), nullable=False),
        sa.Column("description_md", sa.Text(), nullable=True),
        sa.Column("learning_objective", sa.Text(), nullable=True),
        sa.Column("mastery_evidence_md", sa.Text(), nullable=True),
        sa.Column("common_mistakes_md", sa.Text(), nullable=True),
        sa.Column("prerequisites", json_type, server_default=sa.text("'[]'"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "skill_type IN ('recognition', 'base_implementation', 'variant', 'common_error')",
            name=op.f("ck_skills_skill_type_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["algorithm_id"],
            ["algorithms.id"],
            name=op.f("fk_skills_algorithm_id_algorithms"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skills")),
        sa.UniqueConstraint("slug", name=op.f("uq_skills_slug")),
    )
    op.create_index(
        "ix_skills_algorithm_sort",
        "skills",
        ["algorithm_id", "sort_order"],
        unique=False,
    )
    op.create_index(
        "ix_skills_type_active",
        "skills",
        ["skill_type", "is_active"],
        unique=False,
    )

    op.create_table(
        "practice_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("training_type", sa.String(length=32), nullable=False),
        sa.Column("evaluation_mode", sa.String(length=32), nullable=False),
        sa.Column("difficulty", sa.SmallInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "source_type",
            sa.String(length=32),
            server_default=sa.text("'original'"),
            nullable=False,
        ),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("oj_platform", sa.String(length=32), nullable=True),
        sa.Column("oj_problem_ref", sa.String(length=200), nullable=True),
        sa.Column("oj_problem_url", sa.Text(), nullable=True),
        sa.Column("statement_md", sa.Text(), nullable=False),
        sa.Column("constraints_md", sa.Text(), nullable=True),
        sa.Column("input_spec", json_type, nullable=True),
        sa.Column("expected_output_spec", json_type, nullable=True),
        sa.Column("code_scaffold", sa.Text(), nullable=True),
        sa.Column("reference_solution_md", sa.Text(), nullable=True),
        sa.Column(
            "language",
            sa.String(length=32),
            server_default=sa.text("'cpp17'"),
            nullable=False,
        ),
        sa.Column("hints", json_type, server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "max_hint_level",
            sa.SmallInteger(),
            server_default=sa.text("5"),
            nullable=False,
        ),
        sa.Column("error_types", json_type, server_default=sa.text("'[]'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "training_type IN ('recognition', 'template', 'variant', 'correction')",
            name=op.f("ck_practice_tasks_training_type_valid"),
        ),
        sa.CheckConstraint(
            "evaluation_mode IN ('auto_recognition', 'self_assessment')",
            name=op.f("ck_practice_tasks_evaluation_mode_valid"),
        ),
        sa.CheckConstraint(
            "source_type IN ('original', 'oj_reference', 'user')",
            name=op.f("ck_practice_tasks_source_type_valid"),
        ),
        sa.CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5",
            name=op.f("ck_practice_tasks_difficulty_range"),
        ),
        sa.CheckConstraint(
            "max_hint_level >= 0 AND max_hint_level <= 5",
            name=op.f("ck_practice_tasks_max_hint_level_range"),
        ),
        sa.CheckConstraint(
            "oj_platform IS NULL OR oj_platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name=op.f("ck_practice_tasks_oj_platform_valid"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_practice_tasks")),
        sa.UniqueConstraint("slug", name=op.f("uq_practice_tasks_slug")),
    )
    op.create_index(
        "ix_practice_tasks_filter",
        "practice_tasks",
        ["training_type", "difficulty", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_practice_tasks_source",
        "practice_tasks",
        ["source_type", "oj_platform"],
        unique=False,
    )

    op.create_table(
        "task_skills",
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.Column(
            "relation_type",
            sa.String(length=16),
            server_default=sa.text("'target'"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "relation_type IN ('target', 'related')",
            name=op.f("ck_task_skills_relation_type_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name=op.f("fk_task_skills_skill_id_skills"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["practice_tasks.id"],
            name=op.f("fk_task_skills_task_id_practice_tasks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("task_id", "skill_id", name=op.f("pk_task_skills")),
    )
    op.create_index(
        "ix_task_skills_skill_relation",
        "task_skills",
        ["skill_id", "relation_type"],
        unique=False,
    )
    op.create_index(
        "uq_task_skills_primary",
        "task_skills",
        ["task_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
        sqlite_where=sa.text("is_primary"),
    )

    op.create_table(
        "content_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("applied_by", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_versions")),
        sa.UniqueConstraint("version", name=op.f("uq_content_versions_version")),
    )


def downgrade() -> None:
    op.drop_table("content_versions")
    op.drop_index("uq_task_skills_primary", table_name="task_skills")
    op.drop_index("ix_task_skills_skill_relation", table_name="task_skills")
    op.drop_table("task_skills")
    op.drop_index("ix_practice_tasks_source", table_name="practice_tasks")
    op.drop_index("ix_practice_tasks_filter", table_name="practice_tasks")
    op.drop_table("practice_tasks")
    op.drop_index("ix_skills_type_active", table_name="skills")
    op.drop_index("ix_skills_algorithm_sort", table_name="skills")
    op.drop_table("skills")
    op.drop_index("ix_algorithms_category_difficulty", table_name="algorithms")
    op.drop_table("algorithms")
    op.drop_index("ix_algorithm_categories_sort", table_name="algorithm_categories")
    op.drop_table("algorithm_categories")
