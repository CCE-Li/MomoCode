from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
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

_ID_TYPE = BigInteger().with_variant(Integer(), "sqlite")


class SkillMemory(Base):
    __tablename__ = "skill_memories"

    id: Mapped[int] = mapped_column(_ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
    )
    state: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        server_default="1",
    )
    step: Mapped[int | None] = mapped_column(SmallInteger)
    stability: Mapped[float | None] = mapped_column(Float)
    difficulty: Mapped[float | None] = mapped_column(Float)
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        UniqueConstraint("user_id", "skill_id", name="uq_skill_memories_user_skill"),
        CheckConstraint("state >= 1 AND state <= 3", name="state_range"),
        Index("ix_skill_memories_due", "user_id", "due_at"),
        Index("ix_skill_memories_skill", "skill_id"),
    )


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
    )
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
    )
    rating: Mapped[int] = mapped_column(SmallInteger)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    review_duration_ms: Mapped[int | None] = mapped_column(Integer)
    scheduler_version: Mapped[str] = mapped_column(String(64))
    mapping_version: Mapped[str] = mapped_column(String(64))
    evidence_snapshot: Mapped[dict[str, object]] = mapped_column(JSONBType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 4", name="rating_range"),
        CheckConstraint(
            "review_duration_ms IS NULL OR review_duration_ms >= 0",
            name="duration_non_negative",
        ),
        Index(
            "uq_review_logs_session",
            "session_id",
            unique=True,
            postgresql_where=text("session_id IS NOT NULL"),
            sqlite_where=text("session_id IS NOT NULL"),
        ),
        Index("ix_review_logs_user_skill_time", "user_id", "skill_id", "reviewed_at"),
        Index("ix_review_logs_user_time", "user_id", "reviewed_at"),
    )


class UserReviewItem(Base):
    """User-authored review content that participates in the FSRS queue."""

    __tablename__ = "user_review_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str] = mapped_column(String(200))
    content_md: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(
        JSONBType,
        default=list,
        server_default="[]",
    )
    source_url: Mapped[str | None] = mapped_column(Text)
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
        Index("ix_user_review_items_user_created", "user_id", "created_at"),
        Index("ix_user_review_items_user_active", "user_id", "is_active"),
    )


class UserReviewMemory(Base):
    """FSRS state for one user-authored review item.

    Mirrors ``skill_memories`` but is keyed by ``user_review_items.id`` so the
    catalog skills stay global while custom content stays user-owned.
    """

    __tablename__ = "user_review_memories"

    id: Mapped[int] = mapped_column(_ID_TYPE, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    item_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_review_items.id", ondelete="CASCADE"),
    )
    state: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        server_default="1",
    )
    step: Mapped[int | None] = mapped_column(SmallInteger)
    stability: Mapped[float | None] = mapped_column(Float)
    difficulty: Mapped[float | None] = mapped_column(Float)
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        UniqueConstraint("user_id", "item_id", name="uq_user_review_memories_user_item"),
        CheckConstraint("state >= 1 AND state <= 3", name="state_range"),
        Index("ix_user_review_memories_due", "user_id", "due_at"),
    )


class UserReviewLog(Base):
    """Immutable review record for user-authored review content."""

    __tablename__ = "user_review_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    item_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_review_items.id", ondelete="CASCADE"),
    )
    rating: Mapped[int] = mapped_column(SmallInteger)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    review_duration_ms: Mapped[int | None] = mapped_column(Integer)
    scheduler_version: Mapped[str] = mapped_column(String(64))
    mapping_version: Mapped[str] = mapped_column(String(64))
    evidence_snapshot: Mapped[dict[str, object]] = mapped_column(JSONBType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 4", name="rating_range"),
        CheckConstraint(
            "review_duration_ms IS NULL OR review_duration_ms >= 0",
            name="duration_non_negative",
        ),
        Index("ix_user_review_logs_user_time", "user_id", "reviewed_at"),
        Index("ix_user_review_logs_user_item_time", "user_id", "item_id", "reviewed_at"),
    )
