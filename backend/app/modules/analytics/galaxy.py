from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import UserSkillStats
from app.modules.analytics.schemas import GalaxyResponse, GalaxySkillStar
from app.modules.auth.models import UserPreference
from app.modules.catalog.models import Algorithm, AlgorithmCategory, Skill
from app.modules.review.engine import card_from_memory, get_scheduler
from app.modules.review.models import ReviewLog, SkillMemory

LIT_THRESHOLD = 0.75
DARK_THRESHOLD = 0.30
DARK_BRIGHTNESS = 0.16


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def next_star_state(previous: str, retrievability: float) -> str:
    if retrievability >= LIT_THRESHOLD:
        return "lit"
    if retrievability < DARK_THRESHOLD:
        return "dark"
    if previous in {"dark", "lit"}:
        return previous
    return "dark"


def confidence_for(review_count: int) -> float:
    if review_count >= 3:
        return 1.0
    if review_count == 2:
        return 0.7
    if review_count == 1:
        return 0.45
    return 0.0


def star_brightness(state: str, retrievability: float, review_count: int) -> float:
    if state != "lit":
        return round(DARK_BRIGHTNESS + 0.12 * clamp(retrievability), 4)
    span = clamp((retrievability - DARK_THRESHOLD) / (1.0 - DARK_THRESHOLD))
    return round(clamp((0.35 + 0.65 * span) * confidence_for(review_count)), 4)


async def get_galaxy(session: AsyncSession, user_id: UUID) -> GalaxyResponse:
    preference = await session.scalar(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    desired_retention = float(preference.desired_retention) if preference is not None else 0.9
    scheduler = get_scheduler(desired_retention)
    now = datetime.now(UTC)

    skill_rows = (
        await session.execute(
            select(Skill, Algorithm, AlgorithmCategory)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .join(AlgorithmCategory, AlgorithmCategory.id == Algorithm.category_id)
            .where(
                Skill.is_active.is_(True),
                Algorithm.is_active.is_(True),
                AlgorithmCategory.is_active.is_(True),
            )
            .order_by(
                AlgorithmCategory.sort_order,
                AlgorithmCategory.name,
                Algorithm.name,
                Skill.sort_order,
                Skill.name,
            )
        )
    ).all()
    if not skill_rows:
        return GalaxyResponse(
            total_skills=0,
            lit_count=0,
            progress=0.0,
            skills=[],
            computed_at=now,
        )

    skill_ids = [skill.id for skill, _, _ in skill_rows]
    memories = {
        memory.skill_id: memory
        for memory in (
            await session.scalars(
                select(SkillMemory).where(
                    SkillMemory.user_id == user_id,
                    SkillMemory.skill_id.in_(skill_ids),
                )
            )
        ).all()
    }
    review_counts = {
        skill_id: int(count)
        for skill_id, count in (
            await session.execute(
                select(ReviewLog.skill_id, func.count())
                .where(
                    ReviewLog.user_id == user_id,
                    ReviewLog.skill_id.in_(skill_ids),
                )
                .group_by(ReviewLog.skill_id)
            )
        ).all()
    }
    stats_by_skill = {
        stats.skill_id: stats
        for stats in (
            await session.scalars(
                select(UserSkillStats).where(
                    UserSkillStats.user_id == user_id,
                    UserSkillStats.skill_id.in_(skill_ids),
                )
            )
        ).all()
    }

    items: list[GalaxySkillStar] = []
    changed = False
    for skill, algorithm, category in skill_rows:
        memory = memories.get(skill.id)
        retrievability = 0.0
        if (
            memory is not None
            and memory.stability is not None
            and memory.last_review_at is not None
        ):
            card = card_from_memory(memory)
            retrievability = clamp(float(scheduler.get_card_retrievability(card, now)))

        review_count = review_counts.get(skill.id, 0)
        stats = stats_by_skill.get(skill.id)
        previous = stats.star_state if stats is not None else "dark"
        state = next_star_state(previous, retrievability)

        if stats is None:
            stats = UserSkillStats(
                user_id=user_id,
                skill_id=skill.id,
                star_state=state,
                star_updated_at=now if state == "lit" else None,
            )
            session.add(stats)
            stats_by_skill[skill.id] = stats
            changed = True
        elif stats.star_state != state:
            stats.star_state = state
            stats.star_updated_at = now
            changed = True

        items.append(
            GalaxySkillStar(
                skill_id=skill.id,
                skill_slug=skill.slug,
                skill_name=skill.name,
                algorithm_slug=algorithm.slug,
                algorithm_name=algorithm.name,
                category_slug=category.slug,
                category_name=category.name,
                skill_type=skill.skill_type,
                retrievability=round(retrievability, 4),
                mastery=round(retrievability * 100, 1),
                review_count=review_count,
                star_state=state,
                brightness=star_brightness(state, retrievability, review_count),
                star_updated_at=stats.star_updated_at,
            )
        )

    if changed:
        await session.commit()

    lit_count = sum(1 for item in items if item.star_state == "lit")
    total = len(items)
    return GalaxyResponse(
        total_skills=total,
        lit_count=lit_count,
        progress=round(lit_count / total, 4) if total else 0.0,
        skills=items,
        computed_at=now,
    )
