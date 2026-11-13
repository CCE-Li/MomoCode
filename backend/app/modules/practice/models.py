from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_tasks.id", ondelete="RESTRICT"),
    )
    task_snapshot: Mapped[dict[str, object]] = mapped_column(JSONBType)
    training_type: Mapped[str] = mapped_column(String(32))
    mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(
        String(16),
        default="created",
        server_default="created",
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    time_spent_ms: Mapped[int | None] = mapped_column(Integer)
    answer_payload: Mapped[dict[str, object] | None] = mapped_column(JSONBType)
    auto_grade: Mapped[dict[str, object] | None] = mapped_column(JSONBType)
    self_assessment: Mapped[str | None] = mapped_column(String(16))
    self_assessment_note: Mapped[str | None] = mapped_column(Text)
    max_hint_level: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        server_default="0",
    )
    error_types: Mapped[list[str]] = mapped_column(
        JSONBType,
        default=list,
        server_default="[]",
    )
    mark_as_review: Mapped[bool] = mapped_column(default=False, server_default="false")
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
        CheckConstraint(
            "training_type IN ('recognition', 'template', 'variant', 'correction')",
            name="training_type_valid",
        ),
        CheckConstraint("mode IN ('review', 'free')", name="mode_valid"),
        CheckConstraint(
            "status IN ('created', 'in_progress', 'submitted', 'completed', 'abandoned')",
            name="status_valid",
        ),
        CheckConstraint(
            "self_assessment IS NULL OR self_assessment IN ('correct', 'partial', 'incorrect')",
            name="self_assessment_valid",
        ),
        CheckConstraint(
            "max_hint_level >= 0 AND max_hint_level <= 5",
            name="max_hint_level_range",
        ),
        CheckConstraint(
            "time_spent_ms IS NULL OR time_spent_ms >= 0",
            name="time_spent_non_negative",
        ),
        CheckConstraint(
            "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
            name="completed_after_started",
        ),
        Index("ix_practice_sessions_user_created", "user_id", "created_at"),
        Index("ix_practice_sessions_user_status", "user_id", "status"),
        Index("ix_practice_sessions_task", "task_id"),
        Index("ix_practice_sessions_user_type", "user_id", "training_type", "created_at"),
    )


class SessionHint(Base):
    __tablename__ = "session_hints"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
    )
    level: Mapped[int] = mapped_column(SmallInteger)
    content_snapshot: Mapped[dict[str, object]] = mapped_column(JSONBType)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("session_id", "level", name="uq_session_hints_session_level"),
        CheckConstraint("level >= 1 AND level <= 5", name="level_range"),
        Index("ix_session_hints_session", "session_id"),
    )
