from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.tags import normalize_tags
from app.modules.catalog.models import Algorithm, AlgorithmCategory, Skill
from app.modules.catalog.schemas import (
    AlgorithmDetail,
    AlgorithmSummary,
    CategoryResponse,
    SkillDetail,
    SkillRef,
    SkillSummary,
    TagSummary,
    TaskDetail,
    TaskSummary,
)
from app.modules.judge.spec import public_expected_output_spec, read_sample_cases
from app.modules.task_engine.models import PracticeTask, TaskSkill, TaskTag


async def list_categories(session: AsyncSession) -> list[CategoryResponse]:
    rows = await session.scalars(
        select(AlgorithmCategory)
        .where(AlgorithmCategory.is_active.is_(True))
        .order_by(AlgorithmCategory.sort_order, AlgorithmCategory.name)
    )
    return [CategoryResponse.model_validate(row) for row in rows]


async def list_algorithms(
    session: AsyncSession,
    *,
    category_slug: str | None = None,
    search: str | None = None,
) -> list[AlgorithmSummary]:
    statement = (
        select(
            Algorithm,
            AlgorithmCategory.slug,
            AlgorithmCategory.name,
            func.count(Skill.id),
        )
        .join(AlgorithmCategory, Algorithm.category_id == AlgorithmCategory.id)
        .outerjoin(Skill, Skill.algorithm_id == Algorithm.id)
        .where(
            Algorithm.is_active.is_(True),
            AlgorithmCategory.is_active.is_(True),
        )
        .group_by(
            Algorithm.id,
            AlgorithmCategory.id,
            AlgorithmCategory.sort_order,
        )
        .order_by(AlgorithmCategory.sort_order, Algorithm.difficulty, Algorithm.name)
    )
    if category_slug is not None:
        statement = statement.where(AlgorithmCategory.slug == category_slug)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(Algorithm.name.ilike(pattern), Algorithm.slug.ilike(pattern))
        )

    rows = (await session.execute(statement)).all()
    return [
        AlgorithmSummary(
            id=algorithm.id,
            slug=algorithm.slug,
            name=algorithm.name,
            category_slug=category_slug_value,
            category_name=category_name_value,
            summary=algorithm.summary,
            difficulty=algorithm.difficulty,
            skill_count=skill_count,
        )
        for algorithm, category_slug_value, category_name_value, skill_count in rows
    ]


async def get_algorithm(session: AsyncSession, slug: str) -> AlgorithmDetail:
    row = (
        await session.execute(
            select(Algorithm, AlgorithmCategory)
            .join(AlgorithmCategory, Algorithm.category_id == AlgorithmCategory.id)
            .where(
                Algorithm.slug == slug,
                Algorithm.is_active.is_(True),
                AlgorithmCategory.is_active.is_(True),
            )
        )
    ).first()
    if row is None:
        raise DomainError(
            code="ALGORITHM_NOT_FOUND",
            message="算法不存在。",
            status_code=404,
        )

    algorithm, category = row
    skills = (
        await session.scalars(
            select(Skill)
            .where(Skill.algorithm_id == algorithm.id, Skill.is_active.is_(True))
            .order_by(Skill.sort_order, Skill.name)
        )
    ).all()
    skill_summaries = [
        SkillSummary(
            id=skill.id,
            slug=skill.slug,
            name=skill.name,
            skill_type=skill.skill_type,
            algorithm_slug=algorithm.slug,
            algorithm_name=algorithm.name,
            learning_objective=skill.learning_objective,
        )
        for skill in skills
    ]
    return AlgorithmDetail(
        id=algorithm.id,
        slug=algorithm.slug,
        name=algorithm.name,
        category_slug=category.slug,
        category_name=category.name,
        summary=algorithm.summary,
        difficulty=algorithm.difficulty,
        skill_count=len(skill_summaries),
        description_md=algorithm.description_md,
        prerequisites=algorithm.prerequisites,
        skills=skill_summaries,
    )


async def list_skills(
    session: AsyncSession,
    *,
    algorithm_slug: str | None = None,
    skill_type: str | None = None,
) -> list[SkillSummary]:
    statement = (
        select(Skill, Algorithm)
        .join(Algorithm, Skill.algorithm_id == Algorithm.id)
        .where(Skill.is_active.is_(True), Algorithm.is_active.is_(True))
        .order_by(Algorithm.name, Skill.sort_order, Skill.name)
    )
    if algorithm_slug is not None:
        statement = statement.where(Algorithm.slug == algorithm_slug)
    if skill_type is not None:
        statement = statement.where(Skill.skill_type == skill_type)

    rows = (await session.execute(statement)).all()
    return [
        SkillSummary(
            id=skill.id,
            slug=skill.slug,
            name=skill.name,
            skill_type=skill.skill_type,
            algorithm_slug=algorithm.slug,
            algorithm_name=algorithm.name,
            learning_objective=skill.learning_objective,
        )
        for skill, algorithm in rows
    ]


async def get_skill(session: AsyncSession, slug: str) -> SkillDetail:
    row = (
        await session.execute(
            select(Skill, Algorithm)
            .join(Algorithm, Skill.algorithm_id == Algorithm.id)
            .where(
                Skill.slug == slug,
                Skill.is_active.is_(True),
                Algorithm.is_active.is_(True),
            )
        )
    ).first()
    if row is None:
        raise DomainError(
            code="SKILL_NOT_FOUND",
            message="技能不存在。",
            status_code=404,
        )

    skill, algorithm = row
    return SkillDetail(
        id=skill.id,
        slug=skill.slug,
        name=skill.name,
        skill_type=skill.skill_type,
        algorithm_slug=algorithm.slug,
        algorithm_name=algorithm.name,
        learning_objective=skill.learning_objective,
        description_md=skill.description_md,
        mastery_evidence_md=skill.mastery_evidence_md,
        common_mistakes_md=skill.common_mistakes_md,
        prerequisites=skill.prerequisites,
    )


async def skill_refs(
    session: AsyncSession,
    task_ids: list[UUID],
) -> dict[UUID, list[SkillRef]]:
    if not task_ids:
        return {}

    rows = (
        await session.execute(
            select(TaskSkill.task_id, Skill, Algorithm)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(
                TaskSkill.task_id.in_(task_ids),
                TaskSkill.relation_type == "target",
            )
            .order_by(Skill.sort_order, Skill.name)
        )
    ).all()

    result: dict[UUID, list[SkillRef]] = {task_id: [] for task_id in task_ids}
    for task_id, skill, algorithm in rows:
        result[task_id].append(
            SkillRef(
                id=skill.id,
                slug=skill.slug,
                name=skill.name,
                skill_type=skill.skill_type,
                algorithm_slug=algorithm.slug,
                algorithm_name=algorithm.name,
            )
        )
    return result


async def tag_map(
    session: AsyncSession,
    task_ids: list[UUID],
) -> dict[UUID, list[str]]:
    if not task_ids:
        return {}
    rows = (
        await session.execute(
            select(TaskTag.task_id, TaskTag.tag)
            .where(TaskTag.task_id.in_(task_ids))
            .order_by(TaskTag.tag)
        )
    ).all()
    result: dict[UUID, list[str]] = {task_id: [] for task_id in task_ids}
    for task_id, tag in rows:
        result[task_id].append(tag)
    return result


async def list_tasks(
    session: AsyncSession,
    *,
    training_type: str | None = None,
    difficulty: int | None = None,
    algorithm_slug: str | None = None,
    skill_slug: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[TaskSummary]:
    statement = select(PracticeTask).where(
        PracticeTask.is_active.is_(True),
        PracticeTask.source_type != "user",
    )

    if algorithm_slug is not None:
        statement = (
            statement.join(TaskSkill, TaskSkill.task_id == PracticeTask.id)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(
                Algorithm.slug == algorithm_slug,
                TaskSkill.relation_type == "target",
            )
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
            or_(PracticeTask.title.ilike(pattern), PracticeTask.slug.ilike(pattern))
        )

    statement = statement.distinct().order_by(
        PracticeTask.difficulty,
        PracticeTask.training_type,
        PracticeTask.title,
    )
    tasks = (await session.scalars(statement)).all()
    task_ids = [task.id for task in tasks]
    refs = await skill_refs(session, task_ids)
    tags = await tag_map(session, task_ids)
    return [
        TaskSummary(
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
        for task in tasks
    ]


async def get_task(
    session: AsyncSession,
    slug: str,
    *,
    user_id: UUID | None = None,
) -> TaskDetail:
    conditions = [
        PracticeTask.slug == slug,
        PracticeTask.is_active.is_(True),
    ]
    if user_id is None:
        conditions.append(PracticeTask.source_type != "user")
    else:
        conditions.append(
            or_(
                PracticeTask.source_type != "user",
                PracticeTask.created_by_user_id == user_id,
            )
        )
    task = await session.scalar(select(PracticeTask).where(*conditions))
    if task is None:
        raise DomainError(
            code="TASK_NOT_FOUND",
            message="训练任务不存在。",
            status_code=404,
        )

    rows = (
        await session.execute(
            select(TaskSkill, Skill, Algorithm)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(TaskSkill.task_id == task.id)
            .order_by(TaskSkill.relation_type, Skill.sort_order, Skill.name)
        )
    ).all()

    target_skills: list[SkillRef] = []
    related_skills: list[SkillRef] = []
    for link, skill, algorithm in rows:
        ref = SkillRef(
            id=skill.id,
            slug=skill.slug,
            name=skill.name,
            skill_type=skill.skill_type,
            algorithm_slug=algorithm.slug,
            algorithm_name=algorithm.name,
        )
        if link.relation_type == "target":
            target_skills.append(ref)
        else:
            related_skills.append(ref)

    tags = await tag_map(session, [task.id])
    return TaskDetail(
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
        target_skills=[] if task.training_type == "recognition" else target_skills,
        statement_md=task.statement_md,
        constraints_md=task.constraints_md,
        input_spec=task.input_spec,
        expected_output_spec=public_expected_output_spec(task.expected_output_spec),
        code_scaffold=task.code_scaffold,
        error_types=task.error_types,
        related_skills=[] if task.training_type == "recognition" else related_skills,
        sample_cases=read_sample_cases(task.expected_output_spec),
        tags=tags.get(task.id, []),
    )


async def list_tags(session: AsyncSession) -> list[TagSummary]:
    rows = (
        await session.execute(
            select(TaskTag.tag, func.count())
            .join(PracticeTask, PracticeTask.id == TaskTag.task_id)
            .where(
                PracticeTask.is_active.is_(True),
                PracticeTask.source_type != "user",
            )
            .group_by(TaskTag.tag)
            .order_by(func.count().desc(), TaskTag.tag)
            .limit(100)
        )
    ).all()
    return [TagSummary(tag=tag, task_count=count) for tag, count in rows]
