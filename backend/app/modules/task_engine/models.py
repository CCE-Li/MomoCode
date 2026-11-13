from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType


class PracticeTask(Base):
    __tablename__ = "practice_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(140))
    title: Mapped[str] = mapped_column(String(200))
    training_type: Mapped[str] = mapped_column(String(32))
    evaluation_mode: Mapped[str] = mapped_column(String(32))
    difficulty: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        server_default="1",
    )
    source_type: Mapped[str] = mapped_column(
        String(32),
        default="original",
        server_default="original",
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    source_ref: Mapped[str | None] = mapped_column(Text)
    oj_platform: Mapped[str | None] = mapped_column(String(32))
    oj_problem_ref: Mapped[str | None] = mapped_column(String(200))
    oj_problem_url: Mapped[str | None] = mapped_column(Text)
    statement_md: Mapped[str] = mapped_column(Text)
    constraints_md: Mapped[str | None] = mapped_column(Text)
    input_spec: Mapped[dict[str, object] | None] = mapped_column(JSONBType)
    expected_output_spec: Mapped[dict[str, object] | None] = mapped_column(JSONBType)
    code_scaffold: Mapped[str | None] = mapped_column(Text)
    reference_solution_md: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(
        String(32),
        default="cpp17",
        server_default="cpp17",
    )
    hints: Mapped[dict[str, str]] = mapped_column(
        JSONBType,
        default=dict,
        server_default="{}",
    )
    max_hint_level: Mapped[int] = mapped_column(
        SmallInteger,
        default=5,
        server_default="5",
    )
    error_types: Mapped[list[str]] = mapped_column(
        JSONBType,
        default=list,
        server_default="[]",
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("slug", name="uq_practice_tasks_slug"),
        CheckConstraint(
            "training_type IN ('recognition', 'template', 'variant', 'correction')",
            name="training_type_valid",
        ),
        CheckConstraint(
            "evaluation_mode IN ('auto_recognition', 'self_assessment', 'auto_tests')",
            name="evaluation_mode_valid",
        ),
        CheckConstraint(
            "source_type IN ('original', 'oj_reference', 'user')",
            name="source_type_valid",
        ),
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5",
            name="difficulty_range",
        ),
        CheckConstraint(
            "max_hint_level >= 0 AND max_hint_level <= 5",
            name="max_hint_level_range",
        ),
        CheckConstraint(
            "oj_platform IS NULL OR oj_platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name="oj_platform_valid",
        ),
        CheckConstraint(
            "created_by_user_id IS NULL OR source_type = 'user'",
            name="creator_requires_user_source",
        ),
        Index("ix_practice_tasks_creator", "created_by_user_id", "is_active"),
    )


class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (Index("ix_task_tags_tag", "tag"),)


class TaskSkill(Base):
    __tablename__ = "task_skills"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_tasks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(16),
        default="target",
        server_default="target",
    )
    is_primary: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('target', 'related')",
            name="relation_type_valid",
        ),
        Index(
            "uq_task_skills_primary",
            "task_id",
            unique=True,
            postgresql_where=text("is_primary"),
            sqlite_where=text("is_primary"),
        ),
    )
