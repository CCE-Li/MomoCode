from datetime import UTC, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fsrs import Rating
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.tags import normalize_tags
from app.modules.auth.models import UserPreference
from app.modules.catalog.models import Algorithm, Skill
from app.modules.practice.models import PracticeSession
from app.modules.review.engine import (
    CUSTOM_MAPPING_VERSION,
    MAPPING_VERSION,
    SCHEDULER_VERSION,
    apply_card,
    card_from_memory,
    ensure_utc,
    evidence_snapshot,
    evidence_to_rating,
    get_scheduler,
)
from app.modules.review.models import (
    ReviewLog,
    SkillMemory,
    UserReviewItem,
    UserReviewLog,
    UserReviewMemory,
)
from app.modules.review.schemas import (
    CustomReviewItemCreate,
    CustomReviewItemResponse,
    CustomReviewItemUpdate,
    CustomReviewRequest,
    CustomReviewResponse,
    DueItem,
    DueQueueResponse,
    ReviewHistoryItem,
    TodayReviewResponse,
)
from app.modules.task_engine.models import PracticeTask, TaskSkill


async def _preferences(session: AsyncSession, user_id: UUID) -> UserPreference | None:
    return await session.scalar(select(UserPreference).where(UserPreference.user_id == user_id))


def _timezone(name: str | None) -> ZoneInfo:
    if not name:
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _day_bounds(timezone: ZoneInfo, now: datetime) -> tuple[datetime, datetime, datetime]:
    local_now = now.astimezone(timezone)
    start_local = datetime.combine(local_now.date(), time.min, tzinfo=timezone)
    end_local = start_local + timedelta(days=1)
    return (
        start_local.astimezone(UTC),
        end_local.astimezone(UTC),
        local_now,
    )


async def _task_for_skill(
    session: AsyncSession,
    skill_id: UUID,
    user_id: UUID,
) -> PracticeTask | None:
    return await session.scalar(
        select(PracticeTask)
        .join(TaskSkill, TaskSkill.task_id == PracticeTask.id)
        .where(
            TaskSkill.skill_id == skill_id,
            TaskSkill.relation_type == "target",
            PracticeTask.is_active.is_(True),
            or_(
                PracticeTask.source_type != "user",
                PracticeTask.created_by_user_id == user_id,
            ),
        )
        .order_by(PracticeTask.difficulty, PracticeTask.title)
        .limit(1)
    )


def _content_preview(content: str, limit: int = 160) -> str:
    text = " ".join(content.replace("\r", " ").replace("\n", " ").split())
    return text[:limit] + ("…" if len(text) > limit else "")


def _validate_source_url(value: str | None) -> str | None:
    if value is None:
        return None
    url = value.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        raise DomainError(
            code="INVALID_SOURCE_URL",
            message="来源链接必须是 http/https URL。",
            status_code=422,
        )
    return url


async def _custom_item_response(
    session: AsyncSession,
    item: UserReviewItem,
    memory: UserReviewMemory | None = None,
) -> CustomReviewItemResponse:
    if memory is None:
        memory = await session.scalar(
            select(UserReviewMemory).where(
                UserReviewMemory.user_id == item.user_id,
                UserReviewMemory.item_id == item.id,
            )
        )
    return CustomReviewItemResponse(
        id=item.id,
        title=item.title,
        content_md=item.content_md,
        tags=item.tags or [],
        source_url=item.source_url,
        is_active=item.is_active,
        due_at=ensure_utc(memory.due_at) if memory is not None else None,
        last_review_at=(
            ensure_utc(memory.last_review_at)
            if memory is not None and memory.last_review_at is not None
            else None
        ),
        created_at=ensure_utc(item.created_at),
        updated_at=ensure_utc(item.updated_at),
    )


async def _get_custom_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
    *,
    include_inactive: bool = False,
) -> UserReviewItem:
    conditions = [
        UserReviewItem.id == item_id,
        UserReviewItem.user_id == user_id,
    ]
    if not include_inactive:
        conditions.append(UserReviewItem.is_active.is_(True))
    item = await session.scalar(select(UserReviewItem).where(*conditions))
    if item is None:
        raise DomainError(
            code="CUSTOM_REVIEW_NOT_FOUND",
            message="自定义复习内容不存在。",
            status_code=404,
        )
    return item


async def list_custom_items(
    session: AsyncSession,
    user_id: UUID,
    *,
    include_inactive: bool = False,
) -> list[CustomReviewItemResponse]:
    statement = select(UserReviewItem).where(UserReviewItem.user_id == user_id)
    if not include_inactive:
        statement = statement.where(UserReviewItem.is_active.is_(True))
    items = (await session.scalars(statement.order_by(UserReviewItem.created_at.desc()))).all()
    if not items:
        return []

    memories = (
        await session.scalars(
            select(UserReviewMemory).where(
                UserReviewMemory.user_id == user_id,
                UserReviewMemory.item_id.in_([item.id for item in items]),
            )
        )
    ).all()
    memory_by_item = {memory.item_id: memory for memory in memories}
    return [
        await _custom_item_response(session, item, memory_by_item.get(item.id)) for item in items
    ]


async def create_custom_item(
    session: AsyncSession,
    user_id: UUID,
    payload: CustomReviewItemCreate,
) -> CustomReviewItemResponse:
    now = datetime.now(UTC)
    item = UserReviewItem(
        user_id=user_id,
        title=payload.title.strip(),
        content_md=payload.content_md,
        tags=normalize_tags(payload.tags),
        source_url=_validate_source_url(payload.source_url),
        is_active=True,
    )
    session.add(item)
    await session.flush()

    session.add(
        UserReviewMemory(
            user_id=user_id,
            item_id=item.id,
            state=1,
            step=0,
            due_at=now,
        )
    )
    await session.commit()
    await session.refresh(item)
    return await _custom_item_response(session, item)


async def update_custom_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
    payload: CustomReviewItemUpdate,
) -> CustomReviewItemResponse:
    item = await _get_custom_item(session, user_id, item_id, include_inactive=True)
    changes = payload.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is not None:
        item.title = str(changes["title"]).strip()
    if "content_md" in changes and changes["content_md"] is not None:
        item.content_md = str(changes["content_md"])
    if "tags" in changes and changes["tags"] is not None:
        item.tags = normalize_tags([str(tag) for tag in changes["tags"]])
    if "source_url" in changes:
        item.source_url = _validate_source_url(changes["source_url"])
    if "is_active" in changes and changes["is_active"] is not None:
        item.is_active = bool(changes["is_active"])
        if item.is_active:
            memory = await session.scalar(
                select(UserReviewMemory).where(
                    UserReviewMemory.user_id == user_id,
                    UserReviewMemory.item_id == item.id,
                )
            )
            if memory is None:
                session.add(
                    UserReviewMemory(
                        user_id=user_id,
                        item_id=item.id,
                        state=1,
                        step=0,
                        due_at=datetime.now(UTC),
                    )
                )

    await session.commit()
    await session.refresh(item)
    return await _custom_item_response(session, item)


async def deactivate_custom_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
) -> None:
    item = await _get_custom_item(session, user_id, item_id, include_inactive=True)
    item.is_active = False
    await session.commit()


async def review_custom_item(
    session: AsyncSession,
    user_id: UUID,
    item_id: UUID,
    payload: CustomReviewRequest,
) -> CustomReviewResponse:
    item = await _get_custom_item(session, user_id, item_id)
    now = datetime.now(UTC)
    memory = await session.scalar(
        select(UserReviewMemory).where(
            UserReviewMemory.user_id == user_id,
            UserReviewMemory.item_id == item.id,
        )
    )
    if memory is None:
        memory = UserReviewMemory(
            user_id=user_id,
            item_id=item.id,
            state=1,
            step=0,
            due_at=now,
        )
        session.add(memory)
        await session.flush()

    preferences = await _preferences(session, user_id)
    desired_retention = float(preferences.desired_retention) if preferences is not None else 0.9
    scheduler = get_scheduler(desired_retention)
    updated_card, review_log = scheduler.review_card(
        card_from_memory(memory),
        Rating(payload.rating),
        review_datetime=now,
        review_duration=payload.review_duration_ms,
    )
    apply_card(memory, updated_card)

    session.add(
        UserReviewLog(
            user_id=user_id,
            item_id=item.id,
            rating=payload.rating,
            reviewed_at=ensure_utc(review_log.review_datetime),
            review_duration_ms=review_log.review_duration,
            scheduler_version=SCHEDULER_VERSION,
            mapping_version=CUSTOM_MAPPING_VERSION,
            evidence_snapshot={
                "source": "custom_review",
                "item_id": str(item.id),
                "title": item.title,
                "tags": item.tags,
            },
        )
    )
    await session.commit()
    return CustomReviewResponse(
        item_id=item.id,
        rating=payload.rating,
        reviewed_at=ensure_utc(review_log.review_datetime),
        next_due_at=ensure_utc(memory.due_at),
    )


async def get_due_queue(session: AsyncSession, user_id: UUID) -> DueQueueResponse:
    preferences = await _preferences(session, user_id)
    timezone = _timezone(preferences.timezone if preferences else None)
    daily_limit = preferences.daily_review_limit if preferences else 50
    now = datetime.now(UTC)
    start_utc, end_utc, _ = _day_bounds(timezone, now)

    task_exists = (
        select(TaskSkill.skill_id)
        .join(PracticeTask, PracticeTask.id == TaskSkill.task_id)
        .where(
            TaskSkill.skill_id == SkillMemory.skill_id,
            TaskSkill.relation_type == "target",
            PracticeTask.is_active.is_(True),
            or_(
                PracticeTask.source_type != "user",
                PracticeTask.created_by_user_id == user_id,
            ),
        )
        .exists()
    )

    rows = (
        await session.execute(
            select(SkillMemory, Skill, Algorithm)
            .join(Skill, Skill.id == SkillMemory.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(
                SkillMemory.user_id == user_id,
                SkillMemory.due_at <= end_utc,
                task_exists,
            )
            .order_by(SkillMemory.due_at)
            .limit(daily_limit)
        )
    ).all()

    items: list[DueItem] = []
    for memory, skill, algorithm in rows:
        task = await _task_for_skill(session, skill.id, user_id)
        if task is None:
            continue
        due_at = ensure_utc(memory.due_at)
        items.append(
            DueItem(
                kind="skill",
                skill_id=skill.id,
                skill_slug=skill.slug,
                skill_name=skill.name,
                algorithm_slug=algorithm.slug,
                algorithm_name=algorithm.name,
                due_at=due_at,
                overdue=due_at < start_utc,
                task_id=task.id,
                task_slug=task.slug,
                task_title=task.title,
                max_hint_level=task.max_hint_level,
            )
        )

    custom_rows = (
        await session.execute(
            select(UserReviewMemory, UserReviewItem)
            .join(UserReviewItem, UserReviewItem.id == UserReviewMemory.item_id)
            .where(
                UserReviewMemory.user_id == user_id,
                UserReviewMemory.due_at <= end_utc,
                UserReviewItem.user_id == user_id,
                UserReviewItem.is_active.is_(True),
            )
            .order_by(UserReviewMemory.due_at)
            .limit(daily_limit)
        )
    ).all()
    for custom_memory, custom_item in custom_rows:
        due_at = ensure_utc(custom_memory.due_at)
        items.append(
            DueItem(
                kind="custom",
                custom_item_id=custom_item.id,
                title=custom_item.title,
                content_preview=_content_preview(custom_item.content_md),
                due_at=due_at,
                overdue=due_at < start_utc,
            )
        )

    items.sort(key=lambda item: item.due_at)
    items = items[:daily_limit]

    skill_due_count = await session.scalar(
        select(func.count())
        .select_from(SkillMemory)
        .where(
            SkillMemory.user_id == user_id,
            SkillMemory.due_at <= end_utc,
            task_exists,
        )
    )
    custom_due_count = await session.scalar(
        select(func.count())
        .select_from(UserReviewMemory)
        .join(UserReviewItem, UserReviewItem.id == UserReviewMemory.item_id)
        .where(
            UserReviewMemory.user_id == user_id,
            UserReviewMemory.due_at <= end_utc,
            UserReviewItem.user_id == user_id,
            UserReviewItem.is_active.is_(True),
        )
    )

    return DueQueueResponse(
        items=items,
        due_count=(skill_due_count or 0) + (custom_due_count or 0),
        daily_limit=daily_limit,
        timezone=str(timezone),
    )


async def get_today_summary(session: AsyncSession, user_id: UUID) -> TodayReviewResponse:
    preferences = await _preferences(session, user_id)
    timezone = _timezone(preferences.timezone if preferences else None)
    now = datetime.now(UTC)
    start_utc, end_utc, _ = _day_bounds(timezone, now)

    task_exists = (
        select(TaskSkill.skill_id)
        .join(PracticeTask, PracticeTask.id == TaskSkill.task_id)
        .where(
            TaskSkill.skill_id == SkillMemory.skill_id,
            TaskSkill.relation_type == "target",
            PracticeTask.is_active.is_(True),
            or_(
                PracticeTask.source_type != "user",
                PracticeTask.created_by_user_id == user_id,
            ),
        )
        .exists()
    )

    skill_due = await session.scalar(
        select(func.count())
        .select_from(SkillMemory)
        .where(
            SkillMemory.user_id == user_id,
            SkillMemory.due_at <= end_utc,
            task_exists,
        )
    )
    skill_overdue = await session.scalar(
        select(func.count())
        .select_from(SkillMemory)
        .where(
            SkillMemory.user_id == user_id,
            SkillMemory.due_at < start_utc,
            task_exists,
        )
    )
    custom_due = await session.scalar(
        select(func.count())
        .select_from(UserReviewMemory)
        .join(UserReviewItem, UserReviewItem.id == UserReviewMemory.item_id)
        .where(
            UserReviewMemory.user_id == user_id,
            UserReviewMemory.due_at <= end_utc,
            UserReviewItem.user_id == user_id,
            UserReviewItem.is_active.is_(True),
        )
    )
    custom_overdue = await session.scalar(
        select(func.count())
        .select_from(UserReviewMemory)
        .join(UserReviewItem, UserReviewItem.id == UserReviewMemory.item_id)
        .where(
            UserReviewMemory.user_id == user_id,
            UserReviewMemory.due_at < start_utc,
            UserReviewItem.user_id == user_id,
            UserReviewItem.is_active.is_(True),
        )
    )
    reviewed_skills = await session.scalar(
        select(func.count())
        .select_from(ReviewLog)
        .where(
            ReviewLog.user_id == user_id,
            ReviewLog.reviewed_at >= start_utc,
        )
    )
    reviewed_custom = await session.scalar(
        select(func.count())
        .select_from(UserReviewLog)
        .where(
            UserReviewLog.user_id == user_id,
            UserReviewLog.reviewed_at >= start_utc,
        )
    )

    skill_next_due = await session.scalar(
        select(func.min(SkillMemory.due_at)).where(
            SkillMemory.user_id == user_id,
            SkillMemory.due_at > end_utc,
        )
    )
    custom_next_due = await session.scalar(
        select(func.min(UserReviewMemory.due_at)).where(
            UserReviewMemory.user_id == user_id,
            UserReviewMemory.due_at > end_utc,
        )
    )
    candidates = [
        ensure_utc(value) for value in (skill_next_due, custom_next_due) if value is not None
    ]
    next_due_at = min(candidates) if candidates else None

    return TodayReviewResponse(
        due_count=(skill_due or 0) + (custom_due or 0),
        overdue_count=(skill_overdue or 0) + (custom_overdue or 0),
        reviewed_today=(reviewed_skills or 0) + (reviewed_custom or 0),
        timezone=str(timezone),
        next_due_at=next_due_at,
    )


async def get_history(
    session: AsyncSession,
    user_id: UUID,
    limit: int = 50,
) -> list[ReviewHistoryItem]:
    skill_rows = (
        await session.execute(
            select(ReviewLog, Skill, Algorithm)
            .join(Skill, Skill.id == ReviewLog.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(ReviewLog.user_id == user_id)
            .order_by(ReviewLog.reviewed_at.desc())
            .limit(limit)
        )
    ).all()
    custom_rows = (
        await session.execute(
            select(UserReviewLog, UserReviewItem)
            .join(UserReviewItem, UserReviewItem.id == UserReviewLog.item_id)
            .where(UserReviewLog.user_id == user_id)
            .order_by(UserReviewLog.reviewed_at.desc())
            .limit(limit)
        )
    ).all()

    history: list[ReviewHistoryItem] = [
        ReviewHistoryItem(
            kind="skill",
            id=log.id,
            skill_slug=skill.slug,
            skill_name=skill.name,
            algorithm_name=algorithm.name,
            rating=log.rating,
            reviewed_at=ensure_utc(log.reviewed_at),
            review_duration_ms=log.review_duration_ms,
        )
        for log, skill, algorithm in skill_rows
    ]
    history.extend(
        ReviewHistoryItem(
            kind="custom",
            id=log.id,
            custom_item_id=item.id,
            title=item.title,
            rating=log.rating,
            reviewed_at=ensure_utc(log.reviewed_at),
            review_duration_ms=log.review_duration_ms,
        )
        for log, item in custom_rows
    )
    history.sort(key=lambda item: item.reviewed_at, reverse=True)
    return history[:limit]


async def get_next_review_at(session: AsyncSession, session_id: UUID) -> datetime | None:
    log = await session.scalar(select(ReviewLog).where(ReviewLog.session_id == session_id))
    if log is None:
        return None
    memory = await session.scalar(
        select(SkillMemory).where(
            SkillMemory.user_id == log.user_id,
            SkillMemory.skill_id == log.skill_id,
        )
    )
    return ensure_utc(memory.due_at) if memory is not None else None


async def record_formal_review(
    session: AsyncSession,
    session_row: PracticeSession,
) -> datetime | None:
    existing_log = await session.scalar(
        select(ReviewLog).where(ReviewLog.session_id == session_row.id)
    )
    if existing_log is not None:
        memory = await session.scalar(
            select(SkillMemory).where(
                SkillMemory.user_id == session_row.user_id,
                SkillMemory.skill_id == existing_log.skill_id,
            )
        )
        return ensure_utc(memory.due_at) if memory is not None else None

    target_items = session_row.task_snapshot.get("target_skills", [])
    if not isinstance(target_items, list) or not target_items:
        return None
    first_target = target_items[0]
    if not isinstance(first_target, dict) or first_target.get("id") is None:
        return None
    try:
        skill_id = UUID(str(first_target["id"]))
    except ValueError:
        return None

    memory = await session.scalar(
        select(SkillMemory).where(
            SkillMemory.user_id == session_row.user_id,
            SkillMemory.skill_id == skill_id,
        )
    )
    now = datetime.now(UTC)
    if memory is None:
        memory = SkillMemory(
            user_id=session_row.user_id,
            skill_id=skill_id,
            state=1,
            step=0,
            due_at=now,
        )
        session.add(memory)
        await session.flush()

    preferences = await _preferences(session, session_row.user_id)
    desired_retention = float(preferences.desired_retention) if preferences is not None else 0.9
    scheduler = get_scheduler(desired_retention)
    card = card_from_memory(memory)
    rating = evidence_to_rating(session_row)
    updated_card, review_log = scheduler.review_card(
        card,
        rating,
        review_datetime=now,
        review_duration=session_row.time_spent_ms,
    )
    apply_card(memory, updated_card)

    session.add(
        ReviewLog(
            user_id=session_row.user_id,
            skill_id=memory.skill_id,
            session_id=session_row.id,
            rating=int(review_log.rating),
            reviewed_at=ensure_utc(review_log.review_datetime),
            review_duration_ms=review_log.review_duration,
            scheduler_version=SCHEDULER_VERSION,
            mapping_version=MAPPING_VERSION,
            evidence_snapshot=evidence_snapshot(session_row),
        )
    )
    await session.flush()
    return ensure_utc(memory.due_at)
