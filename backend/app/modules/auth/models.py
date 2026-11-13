from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(
        String(16),
        default="active",
        server_default="active",
        index=True,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    preferences: Mapped[UserPreference | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint("status IN ('active', 'disabled')", name="status_valid"),
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        default="UTC",
        server_default="UTC",
    )
    daily_review_limit: Mapped[int] = mapped_column(
        Integer,
        default=50,
        server_default="50",
    )
    desired_retention: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        default=Decimal("0.90"),
        server_default="0.90",
    )
    theme: Mapped[str] = mapped_column(
        String(16),
        default="dark",
        server_default="dark",
    )
    locale: Mapped[str] = mapped_column(
        String(16),
        default="zh-CN",
        server_default="zh-CN",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="preferences")

    __table_args__ = (
        CheckConstraint(
            "daily_review_limit >= 1 AND daily_review_limit <= 500",
            name="daily_review_limit_range",
        ),
        CheckConstraint(
            "desired_retention >= 0.70 AND desired_retention <= 0.99",
            name="desired_retention_range",
        ),
        CheckConstraint(
            "theme IN ('dark', 'light', 'system')",
            name="theme_valid",
        ),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    token_hash: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="sessions")

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_user_sessions_token_hash"),
        Index("ix_user_sessions_user_expires", "user_id", "expires_at"),
        Index("ix_user_sessions_expires", "expires_at"),
    )


class EmailToken(Base):
    __tablename__ = "email_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    purpose: Mapped[str] = mapped_column(String(32))
    token_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_email_tokens_token_hash"),
        CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')",
            name="purpose_valid",
        ),
        Index("ix_email_tokens_user_purpose", "user_id", "purpose"),
        Index("ix_email_tokens_expires", "expires_at"),
    )
