from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType


class AlgorithmCategory(Base):
    __tablename__ = "algorithm_categories"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
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

    __table_args__ = (UniqueConstraint("slug", name="uq_algorithm_categories_slug"),)


class Algorithm(Base):
    __tablename__ = "algorithms"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("algorithm_categories.id", ondelete="RESTRICT"),
    )
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text)
    description_md: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        server_default="1",
    )
    prerequisites: Mapped[list[str]] = mapped_column(
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
        UniqueConstraint("slug", name="uq_algorithms_slug"),
        CheckConstraint(
            "difficulty >= 1 AND difficulty <= 5",
            name="difficulty_range",
        ),
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    algorithm_id: Mapped[UUID] = mapped_column(
        ForeignKey("algorithms.id", ondelete="RESTRICT"),
    )
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120))
    skill_type: Mapped[str] = mapped_column(String(32))
    description_md: Mapped[str | None] = mapped_column(Text)
    learning_objective: Mapped[str | None] = mapped_column(Text)
    mastery_evidence_md: Mapped[str | None] = mapped_column(Text)
    common_mistakes_md: Mapped[str | None] = mapped_column(Text)
    prerequisites: Mapped[list[str]] = mapped_column(
        JSONBType,
        default=list,
        server_default="[]",
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
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
        UniqueConstraint("slug", name="uq_skills_slug"),
        CheckConstraint(
            "skill_type IN ('recognition', 'base_implementation', 'variant', 'common_error')",
            name="skill_type_valid",
        ),
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    version: Mapped[str] = mapped_column(String(64))
    checksum: Mapped[str] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    applied_by: Mapped[str | None] = mapped_column(String(120))

    __table_args__ = (UniqueConstraint("version", name="uq_content_versions_version"),)
