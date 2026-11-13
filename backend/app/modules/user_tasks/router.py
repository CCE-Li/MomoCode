from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_csrf
from app.modules.auth.models import User
from app.modules.catalog.schemas import TaskDetail, TaskSummary
from app.modules.user_tasks import service
from app.modules.user_tasks.schemas import (
    UserTaskImportRequest,
    UserTaskImportResult,
    UserTaskInput,
    UserTaskUpdate,
)

router = APIRouter(prefix="/user-tasks", tags=["user-tasks"])


@router.get("", response_model=list[TaskSummary])
async def list_user_tasks(
    training_type: Literal["recognition", "template", "variant", "correction"] | None = None,
    difficulty: int | None = Query(default=None, ge=1, le=5),
    skill: str | None = Query(default=None, max_length=120),
    tag: str | None = Query(default=None, max_length=64),
    search: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[TaskSummary]:
    return await service.list_tasks(
        session,
        user.id,
        training_type=training_type,
        difficulty=difficulty,
        skill_slug=skill,
        tag=tag,
        search=search,
    )


@router.post(
    "",
    response_model=TaskSummary,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_user_task(
    payload: UserTaskInput,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TaskSummary:
    return await service.create_task(session, user.id, payload)


@router.post(
    "/import",
    response_model=UserTaskImportResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def import_user_tasks(
    payload: UserTaskImportRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserTaskImportResult:
    created = await service.import_tasks(session, user.id, payload.tasks)
    return UserTaskImportResult(created=created, total=len(created))


@router.get("/{task_id}", response_model=TaskDetail)
async def get_user_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TaskDetail:
    return await service.get_my_task(session, user.id, task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskSummary,
    dependencies=[Depends(require_csrf)],
)
async def update_user_task(
    task_id: UUID,
    payload: UserTaskUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TaskSummary:
    return await service.update_task(session, user.id, task_id, payload)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
async def delete_user_task(
    task_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_task(session, user.id, task_id)
