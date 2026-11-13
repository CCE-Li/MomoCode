from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.modules.analytics.models import UserSkillStats
from app.modules.auth.models import User, UserPreference, UserSession
from app.modules.oj.models import OJAccount, Submission
from app.modules.practice.models import PracticeSession
from app.modules.review.models import ReviewLog, SkillMemory
from app.modules.settings.schemas import (
    PreferencesResponse,
    PreferencesUpdate,
    ProfileResponse,
    ProfileUpdate,
)


async def get_preferences(
    session: AsyncSession,
    user_id: UUID,
) -> UserPreference:
    row = await session.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
    if row is None:
        row = UserPreference(user_id=user_id)
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def update_preferences(
    session: AsyncSession,
    user_id: UUID,
    payload: PreferencesUpdate,
) -> PreferencesResponse:
    row = await get_preferences(session, user_id)

    if payload.timezone is not None:
        try:
            ZoneInfo(payload.timezone)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(
                code="INVALID_TIMEZONE",
                message="时区名称不合法。",
                status_code=422,
            ) from exc
        row.timezone = payload.timezone

    if payload.daily_review_limit is not None:
        row.daily_review_limit = payload.daily_review_limit
    if payload.desired_retention is not None:
        row.desired_retention = Decimal(str(payload.desired_retention))
    if payload.theme is not None:
        row.theme = payload.theme
    if payload.locale is not None:
        row.locale = payload.locale

    await session.commit()
    await session.refresh(row)
    return PreferencesResponse.model_validate(row)


async def update_profile(
    session: AsyncSession,
    user_id: UUID,
    payload: ProfileUpdate,
) -> ProfileResponse:
    user = await session.get(User, user_id)
    if user is None:
        raise DomainError(
            code="USER_NOT_FOUND",
            message="用户不存在。",
            status_code=404,
        )
    if payload.display_name is not None:
        user.display_name = payload.display_name.strip() or None
    await session.commit()
    await session.refresh(user)
    return ProfileResponse(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        status=user.status,
    )


def _dt(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _number(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


async def export_user_data(session: AsyncSession, user_id: UUID) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None:
        raise DomainError(
            code="USER_NOT_FOUND",
            message="用户不存在。",
            status_code=404,
        )
    preferences = await session.scalar(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    sessions = list(
        await session.scalars(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at)
        )
    )
    practice_sessions = list(
        await session.scalars(
            select(PracticeSession)
            .where(PracticeSession.user_id == user_id)
            .order_by(PracticeSession.created_at)
        )
    )
    review_logs = list(
        await session.scalars(
            select(ReviewLog).where(ReviewLog.user_id == user_id).order_by(ReviewLog.reviewed_at)
        )
    )
    submissions = list(
        await session.scalars(
            select(Submission).where(Submission.user_id == user_id).order_by(Submission.created_at)
        )
    )
    skill_memories = list(
        await session.scalars(select(SkillMemory).where(SkillMemory.user_id == user_id))
    )
    oj_accounts = list(await session.scalars(select(OJAccount).where(OJAccount.user_id == user_id)))
    skill_stats = list(
        await session.scalars(select(UserSkillStats).where(UserSkillStats.user_id == user_id))
    )

    return {
        "version": "export-v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "profile": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "status": user.status,
            "email_verified_at": _dt(user.email_verified_at),
            "created_at": _dt(user.created_at),
        },
        "preferences": (
            {
                "timezone": preferences.timezone,
                "daily_review_limit": preferences.daily_review_limit,
                "desired_retention": _number(preferences.desired_retention),
                "theme": preferences.theme,
                "locale": preferences.locale,
            }
            if preferences is not None
            else None
        ),
        "sessions": [
            {
                "id": str(row.id),
                "user_agent": row.user_agent,
                "created_at": _dt(row.created_at),
                "last_used_at": _dt(row.last_used_at),
                "expires_at": _dt(row.expires_at),
                "revoked_at": _dt(row.revoked_at),
            }
            for row in sessions
        ],
        "practice_sessions": [
            {
                "id": str(row.id),
                "task_id": str(row.task_id),
                "training_type": row.training_type,
                "mode": row.mode,
                "status": row.status,
                "task_snapshot": row.task_snapshot,
                "answer_payload": row.answer_payload,
                "auto_grade": row.auto_grade,
                "self_assessment": row.self_assessment,
                "self_assessment_note": row.self_assessment_note,
                "max_hint_level": row.max_hint_level,
                "error_types": row.error_types,
                "mark_as_review": row.mark_as_review,
                "time_spent_ms": row.time_spent_ms,
                "started_at": _dt(row.started_at),
                "submitted_at": _dt(row.submitted_at),
                "completed_at": _dt(row.completed_at),
                "created_at": _dt(row.created_at),
            }
            for row in practice_sessions
        ],
        "review_logs": [
            {
                "id": str(row.id),
                "session_id": str(row.session_id) if row.session_id else None,
                "skill_id": str(row.skill_id),
                "rating": row.rating,
                "reviewed_at": _dt(row.reviewed_at),
                "review_duration_ms": row.review_duration_ms,
                "scheduler_version": row.scheduler_version,
                "mapping_version": row.mapping_version,
                "evidence_snapshot": row.evidence_snapshot,
            }
            for row in review_logs
        ],
        "submissions": [
            {
                "id": str(row.id),
                "session_id": str(row.session_id) if row.session_id else None,
                "platform": row.platform,
                "external_id": row.external_id,
                "problem_ref": row.problem_ref,
                "problem_url": row.problem_url,
                "verdict": row.verdict,
                "verdict_raw": row.verdict_raw,
                "language": row.language,
                "time_ms": row.time_ms,
                "memory_kb": row.memory_kb,
                "submitted_at": _dt(row.submitted_at),
                "source": row.source,
                "raw_payload": row.raw_payload,
                "created_at": _dt(row.created_at),
            }
            for row in submissions
        ],
        "skill_memories": [
            {
                "skill_id": str(row.skill_id),
                "state": row.state,
                "step": row.step,
                "stability": row.stability,
                "difficulty": row.difficulty,
                "due_at": _dt(row.due_at),
                "last_review_at": _dt(row.last_review_at),
            }
            for row in skill_memories
        ],
        "oj_accounts": [
            {
                "id": str(row.id),
                "platform": row.platform,
                "handle": row.handle,
                "display_name": row.display_name,
                "is_active": row.is_active,
                "last_synced_at": _dt(row.last_synced_at),
                "created_at": _dt(row.created_at),
            }
            for row in oj_accounts
        ],
        "skill_stats": [
            {
                "skill_id": str(row.skill_id),
                "sample_size": row.sample_size,
                "correctness_rate": _number(row.correctness_rate),
                "independence_score": _number(row.independence_score),
                "hint_dependency": _number(row.hint_dependency),
                "avg_normalized_time": _number(row.avg_normalized_time),
                "skill_score": _number(row.skill_score),
                "score_version": row.score_version,
                "insufficient_data": row.insufficient_data,
                "computed_at": _dt(row.computed_at),
            }
            for row in skill_stats
        ],
    }
