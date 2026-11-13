from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_csrf
from app.modules.auth.models import User
from app.modules.review import service
from app.modules.review.schemas import (
    CustomReviewItemCreate,
    CustomReviewItemResponse,
    CustomReviewItemUpdate,
    CustomReviewRequest,
    CustomReviewResponse,
    DueQueueResponse,
    ReviewHistoryItem,
    TodayReviewResponse,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/due", response_model=DueQueueResponse)
async def due_queue(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DueQueueResponse:
    return await service.get_due_queue(session, user.id)


@router.get("/today", response_model=TodayReviewResponse)
async def today(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TodayReviewResponse:
    return await service.get_today_summary(session, user.id)


@router.get("/history", response_model=list[ReviewHistoryItem])
async def history(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ReviewHistoryItem]:
    return await service.get_history(session, user.id, limit)


@router.get("/custom-items", response_model=list[CustomReviewItemResponse])
async def custom_items(
    include_inactive: bool = Query(default=False),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[CustomReviewItemResponse]:
    return await service.list_custom_items(
        session,
        user.id,
        include_inactive=include_inactive,
    )


@router.post(
    "/custom-items",
    response_model=CustomReviewItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_custom_item(
    payload: CustomReviewItemCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomReviewItemResponse:
    return await service.create_custom_item(session, user.id, payload)


@router.patch(
    "/custom-items/{item_id}",
    response_model=CustomReviewItemResponse,
    dependencies=[Depends(require_csrf)],
)
async def update_custom_item(
    item_id: UUID,
    payload: CustomReviewItemUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomReviewItemResponse:
    return await service.update_custom_item(session, user.id, item_id, payload)


@router.delete(
    "/custom-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
async def delete_custom_item(
    item_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.deactivate_custom_item(session, user.id, item_id)


@router.post(
    "/custom-items/{item_id}/review",
    response_model=CustomReviewResponse,
    dependencies=[Depends(require_csrf)],
)
async def review_custom_item(
    item_id: UUID,
    payload: CustomReviewRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CustomReviewResponse:
    return await service.review_custom_item(session, user.id, item_id, payload)
