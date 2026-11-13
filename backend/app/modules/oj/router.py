from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_rate_limit
from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_csrf
from app.modules.auth.models import User
from app.modules.oj import service
from app.modules.oj.schemas import (
    LinkSubmissionRequest,
    ManualSubmissionCreate,
    ManualSubmissionResult,
    OJAccountCreate,
    OJAccountResponse,
    SubmissionResponse,
    SyncResult,
)

router = APIRouter(tags=["oj"])


@router.get("/oj/accounts", response_model=list[OJAccountResponse])
async def list_accounts(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[OJAccountResponse]:
    rows = await service.list_accounts(session, user.id)
    return [OJAccountResponse.model_validate(row) for row in rows]


@router.post(
    "/oj/accounts",
    response_model=OJAccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_account(
    payload: OJAccountCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OJAccountResponse:
    row = await service.create_account(session, user.id, payload)
    return OJAccountResponse.model_validate(row)


@router.delete(
    "/oj/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
async def delete_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await service.delete_account(session, user.id, account_id)


@router.post(
    "/oj/accounts/{account_id}/sync",
    response_model=SyncResult,
    dependencies=[Depends(require_csrf)],
)
async def sync_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SyncResult:
    await enforce_rate_limit(
        "oj_sync",
        str(user.id),
        limit=5,
        window_seconds=300,
    )
    return await service.sync_account(session, user.id, account_id)


@router.get("/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    platform: str | None = Query(default=None, max_length=32),
    session_id: UUID | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SubmissionResponse]:
    rows = await service.list_submissions(
        session,
        user.id,
        platform=platform,
        session_id=session_id,
    )
    return [SubmissionResponse.model_validate(row) for row in rows]


@router.post(
    "/submissions/manual",
    response_model=ManualSubmissionResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_manual_submission(
    payload: ManualSubmissionCreate,
    response: Response,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ManualSubmissionResult:
    row, duplicate = await service.create_manual_submission(session, user.id, payload)
    if duplicate:
        response.status_code = status.HTTP_200_OK
    return ManualSubmissionResult(
        submission=SubmissionResponse.model_validate(row),
        duplicate=duplicate,
    )


@router.get(
    "/sessions/{session_id}/submissions",
    response_model=list[SubmissionResponse],
)
async def session_submissions(
    session_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SubmissionResponse]:
    rows = await service.session_submissions(session, user.id, session_id)
    return [SubmissionResponse.model_validate(row) for row in rows]


@router.post(
    "/sessions/{session_id}/submissions",
    response_model=SubmissionResponse,
    dependencies=[Depends(require_csrf)],
)
async def link_submission(
    session_id: UUID,
    payload: LinkSubmissionRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SubmissionResponse:
    row = await service.link_submission(
        session,
        user.id,
        session_id,
        payload.submission_id,
    )
    return SubmissionResponse.model_validate(row)
