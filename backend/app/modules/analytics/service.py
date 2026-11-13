import math
import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import UserSkillStats
from app.modules.analytics.schemas import (
    ErrorDistributionItem,
    ForgettingCurvePoint,
    ForgettingCurveResponse,
    MetricDefinition,
    OverviewResponse,
    SkillStatResponse,
    TrainingTypeMetrics,
    TrendPoint,
    TrendsResponse,
)
from app.modules.auth.models import UserPreference
from app.modules.catalog.models import Algorithm, Skill
from app.modules.oj.models import Submission
from app.modules.practice.models import PracticeSession
from app.modules.review.models import ReviewLog, SkillMemory, UserReviewLog
from app.modules.review.service import get_today_summary

SKILL_SCORE_VERSION = "skill-score-v0"
TRAINING_TYPES = ("recognition", "template", "variant", "correction")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def _timezone(session: AsyncSession, user_id: UUID) -> ZoneInfo:
    preference = await session.scalar(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    name = preference.timezone if preference is not None else "UTC"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _range_start(timezone: ZoneInfo, days: int) -> datetime:
    now = datetime.now(UTC)
    local_now = now.astimezone(timezone)
    return (local_now - timedelta(days=days)).astimezone(UTC)


def _correctness(session: PracticeSession) -> float | None:
    auto_grade = session.auto_grade or {}
    result = auto_grade.get("result") if isinstance(auto_grade, dict) else None
    if result == "correct":
        return 1.0
    if result == "partial":
        return 0.5
    if result in {
        "incorrect",
        "compile_error",
        "runtime_error",
        "time_limit_exceeded",
    }:
        return 0.0
    if result is not None:
        return None

    if session.self_assessment == "correct":
        return 1.0
    if session.self_assessment == "partial":
        return 0.5
    if session.self_assessment == "incorrect":
        return 0.0
    return None


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _metrics(sessions: list[PracticeSession]) -> tuple[float | None, float | None, float | None]:
    correctness_values = [
        value for value in (_correctness(item) for item in sessions) if value is not None
    ]
    correctness = _mean(correctness_values)
    independent = (
        sum(1 for item in sessions if item.max_hint_level <= 1) / len(sessions)
        if sessions
        else None
    )
    hints = _mean([float(item.max_hint_level) for item in sessions])
    hint_dependency = hints / 5 if hints is not None else None
    return correctness, independent, hint_dependency


def _difficulty(item: PracticeSession) -> int:
    raw = item.task_snapshot.get("difficulty", 0)
    if isinstance(raw, (int, float, str)):
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0
    return 0


def _normalized_time(sessions: list[PracticeSession]) -> float | None:
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for item in sessions:
        if item.time_spent_ms is not None and item.time_spent_ms > 0:
            grouped[(item.training_type, _difficulty(item))].append(float(item.time_spent_ms))

    medians: dict[tuple[str, int], float] = {}
    for key, values in grouped.items():
        if len(values) >= 2:
            medians[key] = statistics.median(values)

    ratios: list[float] = []
    for item in sessions:
        if item.time_spent_ms is None or item.time_spent_ms <= 0:
            continue
        median = medians.get((item.training_type, _difficulty(item)))
        if median and median > 0:
            ratios.append(float(item.time_spent_ms) / median)
    return _mean(ratios)


def _consistency(sessions: list[PracticeSession]) -> float:
    values = [
        value
        for value in (
            _correctness(item) for item in sorted(sessions, key=lambda row: _as_utc(row.created_at))
        )
        if value is not None
    ]
    if len(values) < 2:
        return 0.5
    middle = len(values) // 2
    earlier = _mean(values[:middle]) or 0.0
    later = _mean(values[middle:]) or 0.0
    return max(0.0, min(1.0, 1.0 - abs(later - earlier)))


async def _oj_confidence(
    session: AsyncSession,
    user_id: UUID,
    session_ids: list[UUID],
) -> float:
    if not session_ids:
        return 0.5
    rows = (
        await session.scalars(
            select(Submission).where(
                Submission.user_id == user_id,
                Submission.session_id.in_(session_ids),
            )
        )
    ).all()
    if not rows:
        return 0.5
    accepted = sum(1 for row in rows if row.verdict == "accepted")
    return accepted / len(rows)


def _skill_score(
    correctness: float | None,
    independence: float | None,
    consistency: float,
    oj_confidence: float,
    variant_score: float | None,
    sample_size: int,
) -> float | None:
    if sample_size < 3 or correctness is None or independence is None:
        return None
    variant = variant_score if variant_score is not None else correctness
    weighted = (
        0.35 * correctness
        + 0.25 * independence
        + 0.15 * consistency
        + 0.15 * oj_confidence
        + 0.10 * variant
    )
    return round(max(0.0, min(1.0, weighted)) * 100, 2)


def _decimal(value: float | None, places: str = "0.0001") -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(round(value, 4))).quantize(Decimal(places))


def _session_skill_id(session: PracticeSession) -> UUID | None:
    items = session.task_snapshot.get("target_skills", [])
    if not isinstance(items, list) or not items:
        return None
    first = items[0]
    if not isinstance(first, dict) or first.get("id") is None:
        return None
    try:
        return UUID(str(first["id"]))
    except ValueError:
        return None


async def overview(
    session: AsyncSession,
    user_id: UUID,
    days: int,
) -> OverviewResponse:
    timezone = await _timezone(session, user_id)
    start = _range_start(timezone, days)
    sessions = list(
        await session.scalars(
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.status == "completed",
                PracticeSession.created_at >= start,
            )
            .order_by(PracticeSession.created_at)
        )
    )

    correctness, independent, hint_dependency = _metrics(sessions)
    reviewed_skills = await session.scalar(
        select(func.count())
        .select_from(ReviewLog)
        .where(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= start,
        )
    )
    reviewed_custom = await session.scalar(
        select(func.count())
        .select_from(UserReviewLog)
        .where(
            UserReviewLog.user_id == user_id,
            UserReviewLog.reviewed_at >= start,
        )
    )
    reviewed_count = (reviewed_skills or 0) + (reviewed_custom or 0)
    today = await get_today_summary(session, user_id)

    training_types: list[TrainingTypeMetrics] = []
    for training_type in TRAINING_TYPES:
        subset = [item for item in sessions if item.training_type == training_type]
        type_correctness, type_independent, type_hints = _metrics(subset)
        training_types.append(
            TrainingTypeMetrics(
                training_type=training_type,
                sessions=len(subset),
                correctness_rate=type_correctness,
                independent_rate=type_independent,
                avg_hint_level=(type_hints * 5 if type_hints is not None else None),
            )
        )

    return OverviewResponse(
        range_days=days,
        sample_size=len(sessions),
        insufficient_data=len(sessions) < 3,
        sessions_completed=len(sessions),
        correctness_rate=correctness,
        independent_rate=independent,
        hint_dependency=hint_dependency,
        avg_normalized_time=_normalized_time(sessions),
        reviewed_count=reviewed_count or 0,
        due_count=today.due_count,
        training_types=training_types,
    )


async def trends(
    session: AsyncSession,
    user_id: UUID,
    days: int,
) -> TrendsResponse:
    timezone = await _timezone(session, user_id)
    start = _range_start(timezone, days)
    sessions = list(
        await session.scalars(
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.status == "completed",
                PracticeSession.created_at >= start,
            )
            .order_by(PracticeSession.created_at)
        )
    )

    today_local = datetime.now(UTC).astimezone(timezone).date()
    buckets: dict[str, list[PracticeSession]] = {}
    for offset in range(days - 1, -1, -1):
        buckets[(today_local - timedelta(days=offset)).isoformat()] = []

    for item in sessions:
        day = _as_utc(item.created_at).astimezone(timezone).date().isoformat()
        if day in buckets:
            buckets[day].append(item)

    points: list[TrendPoint] = []
    for day, subset in buckets.items():
        correctness, independent, _ = _metrics(subset)
        points.append(
            TrendPoint(
                date=day,
                sessions=len(subset),
                correctness_rate=correctness,
                independent_rate=independent,
            )
        )
    return TrendsResponse(range_days=days, points=points)


async def errors(
    session: AsyncSession,
    user_id: UUID,
    days: int,
) -> list[ErrorDistributionItem]:
    timezone = await _timezone(session, user_id)
    start = _range_start(timezone, days)
    sessions = list(
        await session.scalars(
            select(PracticeSession).where(
                PracticeSession.user_id == user_id,
                PracticeSession.status == "completed",
                PracticeSession.created_at >= start,
            )
        )
    )
    counts: dict[str, int] = defaultdict(int)
    for item in sessions:
        for error_type in item.error_types:
            counts[error_type] += 1
    return [
        ErrorDistributionItem(error_type=error_type, count=count)
        for error_type, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    ]


async def skills(
    session: AsyncSession,
    user_id: UUID,
    days: int,
) -> list[SkillStatResponse]:
    timezone = await _timezone(session, user_id)
    start = _range_start(timezone, days)
    sessions = list(
        await session.scalars(
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.status == "completed",
                PracticeSession.created_at >= start,
            )
            .order_by(PracticeSession.created_at)
        )
    )

    by_skill: dict[UUID, list[PracticeSession]] = defaultdict(list)
    for item in sessions:
        skill_id = _session_skill_id(item)
        if skill_id is not None:
            by_skill[skill_id].append(item)

    if not by_skill:
        return []

    rows = (
        await session.execute(
            select(Skill, Algorithm)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(Skill.id.in_(by_skill.keys()))
        )
    ).all()
    metadata = {skill.id: (skill, algorithm) for skill, algorithm in rows}

    results: list[SkillStatResponse] = []
    for skill_id, subset in by_skill.items():
        skill, algorithm = metadata[skill_id]
        correctness, independence, hint_dependency = _metrics(subset)
        variant_sessions = [item for item in subset if item.training_type == "variant"]
        variant_correctness, _, _ = _metrics(variant_sessions)
        session_ids = [item.id for item in subset]
        oj_confidence = await _oj_confidence(session, user_id, session_ids)
        score = _skill_score(
            correctness,
            independence,
            _consistency(subset),
            oj_confidence,
            variant_correctness,
            len(subset),
        )
        error_counts: dict[str, int] = defaultdict(int)
        for item in subset:
            for error_type in item.error_types:
                error_counts[error_type] += 1
        normalized_time = _normalized_time(subset)
        insufficient = len(subset) < 3
        computed_at = datetime.now(UTC)

        stats = await session.scalar(
            select(UserSkillStats).where(
                UserSkillStats.user_id == user_id,
                UserSkillStats.skill_id == skill_id,
            )
        )
        if stats is None:
            stats = UserSkillStats(user_id=user_id, skill_id=skill_id)
            session.add(stats)
        stats.sample_size = len(subset)
        stats.correctness_rate = _decimal(correctness)
        stats.independence_score = _decimal(independence)
        stats.hint_dependency = _decimal(hint_dependency)
        stats.avg_normalized_time = _decimal(normalized_time, "0.0001")
        stats.error_distribution = dict(error_counts)
        stats.skill_score = _decimal(score, "0.01")
        stats.score_version = SKILL_SCORE_VERSION
        stats.insufficient_data = insufficient
        stats.computed_at = computed_at

        results.append(
            SkillStatResponse(
                skill_id=skill_id,
                skill_slug=skill.slug,
                skill_name=skill.name,
                algorithm_name=algorithm.name,
                sample_size=len(subset),
                correctness_rate=correctness,
                independence_score=independence,
                hint_dependency=hint_dependency,
                avg_normalized_time=normalized_time,
                skill_score=score,
                insufficient_data=insufficient,
                score_version=SKILL_SCORE_VERSION,
                computed_at=computed_at,
            )
        )

    await session.commit()
    return sorted(results, key=lambda item: (-(item.skill_score or 0), item.skill_name))


FSRS_FACTOR = 0.9803464944134797
FSRS_DECAY = -0.1542
FIBONACCI_INTERVALS = [1, 1, 2, 3, 5, 8, 13, 21]
FIBONACCI_STABILITY_DAYS = 1.5


def _fibonacci_retention(days_since_review: float) -> float:
    return max(0.0, min(1.0, math.exp(-max(0.0, days_since_review) / FIBONACCI_STABILITY_DAYS)))


def _retrievability(day: float, stability: float) -> float:
    if stability <= 0:
        return 0.0
    value: float = float((1 + FSRS_FACTOR * max(0.0, day) / stability) ** FSRS_DECAY)
    return max(0.0, min(1.0, value))


async def forgetting_curve(
    session: AsyncSession,
    user_id: UUID,
    horizon_days: int,
) -> ForgettingCurveResponse:
    review_days: list[int] = []
    total = 0
    for interval in FIBONACCI_INTERVALS:
        total += interval
        review_days.append(total)

    stabilities = [
        float(value)
        for value in (
            await session.scalars(
                select(SkillMemory.stability).where(
                    SkillMemory.user_id == user_id,
                    SkillMemory.stability.is_not(None),
                    SkillMemory.stability > 0,
                )
            )
        ).all()
        if value is not None
    ]
    avg_stability = statistics.mean(stabilities) if stabilities else None

    points: list[ForgettingCurvePoint] = []
    for day in range(horizon_days + 1):
        last_review = max((item for item in review_days if item <= day), default=0)
        points.append(
            ForgettingCurvePoint(
                day=day,
                fibonacci_retention=_fibonacci_retention(day - last_review),
                my_retention=(
                    _retrievability(day, avg_stability) if avg_stability is not None else None
                ),
            )
        )

    return ForgettingCurveResponse(
        horizon_days=horizon_days,
        sample_size=len(stabilities),
        insufficient_data=len(stabilities) < 3,
        avg_stability_days=avg_stability,
        fibonacci_intervals=FIBONACCI_INTERVALS,
        fibonacci_review_days=[item for item in review_days if item <= horizon_days],
        points=points,
        notes=(
            "Fibonacci 计划按 1/1/2/3/5/8/13/21 天复习，使用 1.5 天稳定度的指数遗忘；"
            "我的曲线取当前技能 FSRS 稳定度均值。"
        ),
    )


def definitions() -> list[MetricDefinition]:
    return [
        MetricDefinition(
            key="correctness_rate",
            name="正确率",
            formula="正确=1，部分正确=0.5，错误=0；识别用自动判分，编码类用自评；对有效样本取平均。",
            source="practice_sessions.auto_grade / self_assessment",
            time_range="所选时间范围",
            notes="自评与客观证据分开；单次通过不代表掌握。",
        ),
        MetricDefinition(
            key="independent_rate",
            name="独立完成比例",
            formula="最高提示等级 <= 1 的已完成训练会话 / 已完成训练会话。",
            source="practice_sessions.max_hint_level",
            time_range="所选时间范围",
            notes="提示等级越低，独立程度越高。",
        ),
        MetricDefinition(
            key="hint_dependency",
            name="提示依赖",
            formula="平均最高提示等级 / 5。",
            source="practice_sessions.max_hint_level",
            time_range="所选时间范围",
            notes="0 表示无提示；1 表示最高提示。",
        ),
        MetricDefinition(
            key="normalized_time",
            name="归一化耗时",
            formula="训练会话耗时 / 同一训练类型与难度的个人中位耗时，再取平均。",
            source="practice_sessions.time_spent_ms、training_type、task difficulty",
            time_range="所选时间范围",
            notes="不跨算法做绝对耗时比较。",
        ),
        MetricDefinition(
            key="skill_score",
            name="技能分数",
            formula=(
                "0.35*正确率 + 0.25*独立比例 + 0.15*一致性 + "
                "0.15*OJ 证据 + 0.10*变体表现，乘以 100。"
            ),
            source="practice_sessions、submissions",
            time_range="所选时间范围",
            notes="与 FSRS 难度无关；样本 <3 显示样本不足。",
        ),
        MetricDefinition(
            key="due_count",
            name="今日到期",
            formula="按用户 × 技能维护的 FSRS 到期时间早于用户时区今日结束时间的技能数。",
            source="skill_memories",
            time_range="今日（用户时区）",
            notes="只统计有可用训练任务的技能。",
        ),
        MetricDefinition(
            key="reviewed_count",
            name="复习次数",
            formula="所选时间范围内复习记录数量。",
            source="review_logs + user_review_logs",
            time_range="所选时间范围",
            notes="正式复习与自定义内容复习都会产生记录。",
        ),
    ]
