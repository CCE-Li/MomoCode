from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType


class OJAccount(Base):
    __tablename__ = "oj_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    platform: Mapped[str] = mapped_column(String(32))
    handle: Mapped[str] = mapped_column(String(120))
    display_name: Mapped[str | None] = mapped_column(String(120))
    credentials_encrypted: Mapped[bytes | None] = mapped_column()
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        UniqueConstraint(
            "user_id",
            "platform",
            "handle",
            name="uq_oj_accounts_user_platform_handle",
        ),
        CheckConstraint(
            "platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name="platform_valid",
        ),
        Index("ix_oj_accounts_user", "user_id"),
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
    )
    oj_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("oj_accounts.id", ondelete="SET NULL"),
    )
    platform: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str | None] = mapped_column(String(200))
    problem_ref: Mapped[str | None] = mapped_column(String(200))
    problem_url: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str | None] = mapped_column(String(32))
    verdict_raw: Mapped[str | None] = mapped_column(String(120))
    language: Mapped[str | None] = mapped_column(String(64))
    time_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(
        String(16),
        default="manual",
        server_default="manual",
    )
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSONBType)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "platform",
            "external_id",
            name="uq_submissions_user_platform_external",
        ),
        CheckConstraint(
            "platform IN ('codeforces', 'luogu', 'atcoder', 'other')",
            name="platform_valid",
        ),
        CheckConstraint("source IN ('manual', 'oj_sync')", name="source_valid"),
        CheckConstraint(
            "verdict IS NULL OR verdict IN "
            "('accepted', 'wrong_answer', 'time_limit_exceeded', "
            "'memory_limit_exceeded', 'runtime_error', 'compilation_error', "
            "'partially_accepted', 'other')",
            name="verdict_valid",
        ),
        CheckConstraint("time_ms IS NULL OR time_ms >= 0", name="time_non_negative"),
        CheckConstraint(
            "memory_kb IS NULL OR memory_kb >= 0",
            name="memory_non_negative",
        ),
        Index(
            "uq_submissions_user_platform_external_active",
            "user_id",
            "platform",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
            sqlite_where=text("external_id IS NOT NULL"),
        ),
        Index(
            "ix_submissions_user_submitted",
            "user_id",
            "submitted_at",
        ),
        Index("ix_submissions_session", "session_id"),
        Index("ix_submissions_user_platform", "user_id", "platform"),
    )
