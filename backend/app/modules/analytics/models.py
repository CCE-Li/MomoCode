from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import JSONBType


class UserSkillStats(Base):
    __tablename__ = "user_skill_stats"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    skill_id: Mapped[UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
    )
    sample_size: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    correctness_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    independence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    hint_dependency: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    avg_normalized_time: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    error_distribution: Mapped[dict[str, int]] = mapped_column(
        JSONBType,
        default=dict,
        server_default="{}",
    )
    skill_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    score_version: Mapped[str] = mapped_column(
        String(32),
        default="skill-score-v0",
        server_default="skill-score-v0",
    )
    insufficient_data: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
    star_state: Mapped[str] = mapped_column(
        String(16),
        default="dark",
        server_default="dark",
    )
    star_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_id",
            name="uq_user_skill_stats_user_skill",
        ),
        CheckConstraint(
            "star_state IN ('dark', 'lit')",
            name="star_state_valid",
        ),
    )
