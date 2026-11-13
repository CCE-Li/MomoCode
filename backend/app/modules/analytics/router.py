from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.analytics import service
from app.modules.analytics.galaxy import get_galaxy
from app.modules.analytics.schemas import (
    ErrorDistributionItem,
    ForgettingCurveResponse,
    GalaxyResponse,
    MetricDefinition,
    OverviewResponse,
    SkillStatResponse,
    TrendsResponse,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def overview(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OverviewResponse:
    return await service.overview(session, user.id, days)


@router.get("/trends", response_model=TrendsResponse)
async def trends(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TrendsResponse:
    return await service.trends(session, user.id, days)


@router.get("/errors", response_model=list[ErrorDistributionItem])
async def errors(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ErrorDistributionItem]:
    return await service.errors(session, user.id, days)


@router.get("/skills", response_model=list[SkillStatResponse])
async def skills(
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SkillStatResponse]:
    return await service.skills(session, user.id, days)


@router.get("/definitions", response_model=list[MetricDefinition])
async def definitions() -> list[MetricDefinition]:
    return service.definitions()


@router.get("/forgetting-curve", response_model=ForgettingCurveResponse)
async def forgetting_curve(
    horizon_days: int = Query(default=30, ge=7, le=60),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ForgettingCurveResponse:
    return await service.forgetting_curve(session, user.id, horizon_days)


@router.get("/galaxy", response_model=GalaxyResponse)
async def galaxy(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> GalaxyResponse:
    return await get_galaxy(session, user.id)
