import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_csrf
from app.modules.auth.models import User
from app.modules.settings import service
from app.modules.settings.schemas import (
    PreferencesResponse,
    PreferencesUpdate,
    ProfileResponse,
    ProfileUpdate,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/preferences", response_model=PreferencesResponse)
async def get_preferences(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PreferencesResponse:
    row = await service.get_preferences(session, user.id)
    return PreferencesResponse.model_validate(row)


@router.patch(
    "/preferences",
    response_model=PreferencesResponse,
    dependencies=[Depends(require_csrf)],
)
async def update_preferences(
    payload: PreferencesUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> PreferencesResponse:
    return await service.update_preferences(session, user.id, payload)


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    dependencies=[Depends(require_csrf)],
)
async def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
    return await service.update_profile(session, user.id, payload)


@router.get("/export")
async def export_data(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    data = await service.export_user_data(session, user.id)
    filename = f"momocode-export-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
