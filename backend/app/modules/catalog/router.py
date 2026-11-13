from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.catalog import service
from app.modules.catalog.schemas import (
    AlgorithmDetail,
    AlgorithmSummary,
    CategoryResponse,
    SkillDetail,
    SkillSummary,
    TagSummary,
    TaskDetail,
    TaskSummary,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
async def categories(
    session: AsyncSession = Depends(get_db_session),
) -> list[CategoryResponse]:
    return await service.list_categories(session)


@router.get("/algorithms", response_model=list[AlgorithmSummary])
async def algorithms(
    category: str | None = Query(default=None, max_length=120),
    search: str | None = Query(default=None, max_length=120),
    session: AsyncSession = Depends(get_db_session),
) -> list[AlgorithmSummary]:
    return await service.list_algorithms(
        session,
        category_slug=category,
        search=search,
    )


@router.get("/algorithms/{slug}", response_model=AlgorithmDetail)
async def algorithm_detail(
    slug: str,
    session: AsyncSession = Depends(get_db_session),
) -> AlgorithmDetail:
    return await service.get_algorithm(session, slug)


@router.get("/skills", response_model=list[SkillSummary])
async def skills(
    algorithm: str | None = Query(default=None, max_length=120),
    skill_type: Literal["recognition", "base_implementation", "variant", "common_error"]
    | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[SkillSummary]:
    return await service.list_skills(
        session,
        algorithm_slug=algorithm,
        skill_type=skill_type,
    )


@router.get("/skills/{slug}", response_model=SkillDetail)
async def skill_detail(
    slug: str,
    session: AsyncSession = Depends(get_db_session),
) -> SkillDetail:
    return await service.get_skill(session, slug)


@router.get("/tags", response_model=list[TagSummary])
async def tags(
    session: AsyncSession = Depends(get_db_session),
) -> list[TagSummary]:
    return await service.list_tags(session)


@router.get("/tasks", response_model=list[TaskSummary])
async def tasks(
    training_type: Literal["recognition", "template", "variant", "correction"] | None = None,
    difficulty: int | None = Query(default=None, ge=1, le=5),
    algorithm: str | None = Query(default=None, max_length=120),
    skill: str | None = Query(default=None, max_length=120),
    tag: str | None = Query(default=None, max_length=64),
    search: str | None = Query(default=None, max_length=120),
    session: AsyncSession = Depends(get_db_session),
) -> list[TaskSummary]:
    return await service.list_tasks(
        session,
        training_type=training_type,
        difficulty=difficulty,
        algorithm_slug=algorithm,
        skill_slug=skill,
        tag=tag,
        search=search,
    )


@router.get("/tasks/{slug}", response_model=TaskDetail)
async def task_detail(
    slug: str,
    session: AsyncSession = Depends(get_db_session),
) -> TaskDetail:
    return await service.get_task(session, slug)
