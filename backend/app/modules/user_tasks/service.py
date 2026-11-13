from __future__ import annotations

import re
from uuid import UUID, uuid4

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.tags import normalize_tags
from app.modules.catalog.models import Skill
from app.modules.catalog.schemas import TaskDetail, TaskSummary
from app.modules.catalog.service import get_task, skill_refs, tag_map
from app.modules.task_engine.models import PracticeTask, TaskSkill, TaskTag
from app.modules.user_tasks.schemas import UserTaskInput, UserTaskUpdate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "task"


def _generate_slug(user_id: UUID, title: str) -> str:
    return f"user-{user_id.hex[:8]}-{_slugify(title)}-{uuid4().hex[:8]}"[:140]


async def _owned_task(
    session: AsyncSession,
    user_id: UUID,
    task_id: UUID,
) -> PracticeTask:
    task = await session.scalar(
        select(PracticeTask).where(
            PracticeTask.id == task_id,
            PracticeTask.created_by_user_id == user_id,
            PracticeTask.source_type == "user",
            PracticeTask.is_active.is_(True),
        )
    )
    if task is None:
        raise DomainError(
            code="USER_TASK_NOT_FOUND",
            message="自定义题目不存在。",
            status_code=404,
        )
    return task


async def _resolve_skills(
    session: AsyncSession,
    slugs: list[str],
) -> dict[str, Skill]:
    unique = list(dict.fromkeys(slugs))
    if not unique:
        return {}
    rows = (await session.scalars(select(Skill).where(Skill.slug.in_(unique)))).all()
    found = {skill.slug: skill for skill in rows}
    missing = [slug for slug in unique if slug not in found]
    if missing:
        raise DomainError(
            code="UNKNOWN_SKILL",
            message=f"未知技能：{', '.join(missing)}",
            status_code=422,
            details={"missing_skills": missing},
        )
    return found


async def _current_skill_slugs(
    session: AsyncSession,
    task_id: UUID,
) -> tuple[list[str], list[str]]:
    rows = (
        await session.execute(
            select(TaskSkill.relation_type, Skill.slug)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .where(TaskSkill.task_id == task_id)
            .order_by(TaskSkill.relation_type, Skill.sort_order, Skill.name)
        )
    ).all()
    target = [slug for relation, slug in rows if relation == "target"]
    related = [slug for relation, slug in rows if relation == "related"]
    return target, related


def _apply_input(task: PracticeTask, payload: UserTaskInput, user_id: UUID) -> None:
    task.title = payload.title.strip()
    task.training_type = payload.training_type
    task.evaluation_mode = payload.evaluation_mode
    task.difficulty = payload.difficulty
    task.source_type = "user"
    task.created_by_user_id = user_id
    task.source_ref = payload.source_ref
    task.oj_platform = payload.oj_platform
    task.oj_problem_ref = payload.oj_problem_ref
    task.oj_problem_url = payload.oj_problem_url
    task.statement_md = payload.statement_md
    task.constraints_md = payload.constraints_md
    task.input_spec = payload.input_spec
    task.expected_output_spec = payload.expected_output_spec
    task.code_scaffold = payload.code_scaffold
    task.reference_solution_md = payload.reference_solution_md
    task.language = payload.language
    task.hints = payload.hints
    task.max_hint_level = payload.max_hint_level
    task.error_types = payload.error_types
    task.is_active = True


async def _replace_task_tags(
    session: AsyncSession,
    task_id: UUID,
    tags: list[str],
) -> None:
    await session.execute(delete(TaskTag).where(TaskTag.task_id == task_id))
    for tag in normalize_tags(tags):
        session.add(TaskTag(task_id=task_id, tag=tag))


async def _replace_task_skills(
    session: AsyncSession,
    task_id: UUID,
    target_skills: list[str],
    related_skills: list[str],
    skill_map: dict[str, Skill],
) -> None:
    await session.execute(delete(TaskSkill).where(TaskSkill.task_id == task_id))
    for index, slug in enumerate(target_skills):
        session.add(
            TaskSkill(
                task_id=task_id,
                skill_id=skill_map[slug].id,
                relation_type="target",
                is_primary=index == 0,
            )
        )
    for slug in related_skills:
        session.add(
            TaskSkill(
                task_id=task_id,
                skill_id=skill_map[slug].id,
                relation_type="related",
                is_primary=False,
            )
        )


async def _summary(
    session: AsyncSession,
    task: PracticeTask,
) -> TaskSummary:
    refs = await skill_refs(session, [task.id])
    tags = await tag_map(session, [task.id])
    return TaskSummary(
        id=task.id,
        slug=task.slug,
        title=task.title,
        training_type=task.training_type,
        evaluation_mode=task.evaluation_mode,
        difficulty=task.difficulty,
        source_type=task.source_type,
        language=task.language,
        max_hint_level=task.max_hint_level,
        oj_platform=task.oj_platform,
        oj_problem_url=task.oj_problem_url,
        target_skills=[] if task.training_type == "recognition" else refs.get(task.id, []),
        tags=tags.get(task.id, []),
    )


async def _create_one(
    session: AsyncSession,
    user_id: UUID,
    payload: UserTaskInput,
    skill_map: dict[str, Skill],
) -> PracticeTask:
    task = PracticeTask(slug=_generate_slug(user_id, payload.title))
    _apply_input(task, payload, user_id)
    session.add(task)
    await session.flush()
    await _replace_task_skills(
        session,
        task.id,
        payload.target_skills,
        payload.related_skills,
        skill_map,
    )
    await _replace_task_tags(session, task.id, payload.tags)
    return task


async def create_task(
    session: AsyncSession,
    user_id: UUID,
    payload: UserTaskInput,
) -> TaskSummary:
    skill_map = await _resolve_skills(
        session,
        [*payload.target_skills, *payload.related_skills],
    )
    task = await _create_one(session, user_id, payload, skill_map)
    await session.commit()
    await session.refresh(task)
    return await _summary(session, task)


async def import_tasks(
    session: AsyncSession,
    user_id: UUID,
    payloads: list[UserTaskInput],
) -> list[TaskSummary]:
    skill_map = await _resolve_skills(
        session,
        [
            slug
            for payload in payloads
            for slug in [*payload.target_skills, *payload.related_skills]
        ],
    )
    created: list[PracticeTask] = []
    try:
        for payload in payloads:
            created.append(await _create_one(session, user_id, payload, skill_map))
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    return [await _summary(session, task) for task in created]


async def list_tasks(
    session: AsyncSession,
    user_id: UUID,
    *,
    training_type: str | None = None,
    difficulty: int | None = None,
    skill_slug: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[TaskSummary]:
    statement = select(PracticeTask).where(
        PracticeTask.is_active.is_(True),
        PracticeTask.source_type == "user",
        PracticeTask.created_by_user_id == user_id,
    )
    if skill_slug is not None:
        statement = (
            statement.join(TaskSkill, TaskSkill.task_id == PracticeTask.id)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .where(
                Skill.slug == skill_slug,
                TaskSkill.relation_type == "target",
            )
        )
    if tag is not None:
        normalized = normalize_tags([tag])
        if normalized:
            statement = statement.join(
                TaskTag,
                TaskTag.task_id == PracticeTask.id,
            ).where(TaskTag.tag == normalized[0])
    if training_type is not None:
        statement = statement.where(PracticeTask.training_type == training_type)
    if difficulty is not None:
        statement = statement.where(PracticeTask.difficulty == difficulty)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                PracticeTask.title.ilike(pattern),
                PracticeTask.slug.ilike(pattern),
            )
        )

    tasks = (
        await session.scalars(
            statement.distinct().order_by(
                PracticeTask.difficulty,
                PracticeTask.training_type,
                PracticeTask.title,
            )
        )
    ).all()
    return [await _summary(session, task) for task in tasks]


async def get_my_task(
    session: AsyncSession,
    user_id: UUID,
    task_id: UUID,
) -> TaskDetail:
    task = await _owned_task(session, user_id, task_id)
    return await get_task(session, task.slug, user_id=user_id)


async def update_task(
    session: AsyncSession,
    user_id: UUID,
    task_id: UUID,
    payload: UserTaskUpdate,
) -> TaskSummary:
    task = await _owned_task(session, user_id, task_id)
    target_slugs, related_slugs = await _current_skill_slugs(session, task.id)
    current_tags = (await tag_map(session, [task.id])).get(task.id, [])
    changes = payload.model_dump(exclude_unset=True)

    merged: dict[str, object] = {
        "title": task.title,
        "training_type": task.training_type,
        "evaluation_mode": task.evaluation_mode,
        "difficulty": task.difficulty,
        "source_ref": task.source_ref,
        "oj_platform": task.oj_platform,
        "oj_problem_ref": task.oj_problem_ref,
        "oj_problem_url": task.oj_problem_url,
        "statement_md": task.statement_md,
        "constraints_md": task.constraints_md,
        "input_spec": task.input_spec,
        "expected_output_spec": task.expected_output_spec,
        "code_scaffold": task.code_scaffold,
        "reference_solution_md": task.reference_solution_md,
        "language": task.language,
        "hints": task.hints,
        "max_hint_level": task.max_hint_level,
        "error_types": task.error_types,
        "tags": current_tags,
        "target_skills": target_slugs,
        "related_skills": related_slugs,
    }
    merged.update(changes)
    validated = UserTaskInput.model_validate(merged)

    skill_map = await _resolve_skills(
        session,
        [*validated.target_skills, *validated.related_skills],
    )
    _apply_input(task, validated, user_id)
    await _replace_task_skills(
        session,
        task.id,
        validated.target_skills,
        validated.related_skills,
        skill_map,
    )
    await _replace_task_tags(session, task.id, validated.tags)
    await session.commit()
    await session.refresh(task)
    return await _summary(session, task)


async def delete_task(
    session: AsyncSession,
    user_id: UUID,
    task_id: UUID,
) -> None:
    task = await _owned_task(session, user_id, task_id)
    task.is_active = False
    await session.commit()
