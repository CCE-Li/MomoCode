from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_rate_limit
from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_csrf
from app.modules.auth.models import User
from app.modules.practice import service
from app.modules.practice.schemas import (
    AiReviewRequest,
    AiReviewResponse,
    AnswerRequest,
    CompleteRequest,
    DraftRequest,
    HintRequest,
    HintResponse,
    ResultResponse,
    RunTestsRequest,
    RunTestsResponse,
    SessionCreateRequest,
    SessionResponse,
)

router = APIRouter(prefix="/sessions", tags=["practice"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_session(
    payload: SessionCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    return await service.create_session(
        session,
        user_id=user.id,
        task_id=payload.task_id,
        mode=payload.mode,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    return await service.get_session_response(
        session,
        user_id=user.id,
        session_id=session_id,
    )


@router.post(
    "/{session_id}/hints",
    response_model=HintResponse,
    dependencies=[Depends(require_csrf)],
)
async def request_hint(
    session_id: UUID,
    payload: HintRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> HintResponse:
    return await service.request_hint(
        session,
        user_id=user.id,
        session_id=session_id,
        level=payload.level,
    )


@router.post(
    "/{session_id}/answers",
    response_model=SessionResponse,
    dependencies=[Depends(require_csrf)],
)
async def submit_answer(
    session_id: UUID,
    payload: AnswerRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    return await service.submit_answer(
        session,
        user_id=user.id,
        session_id=session_id,
        payload=payload,
    )


@router.put(
    "/{session_id}/draft",
    response_model=SessionResponse,
    dependencies=[Depends(require_csrf)],
)
async def save_draft(
    session_id: UUID,
    payload: DraftRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    return await service.save_draft(
        session,
        user_id=user.id,
        session_id=session_id,
        code=payload.code,
    )


@router.post(
    "/{session_id}/run",
    response_model=RunTestsResponse,
    dependencies=[Depends(require_csrf)],
)
async def run_tests(
    session_id: UUID,
    payload: RunTestsRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> RunTestsResponse:
    await enforce_rate_limit(
        "code_run",
        str(user.id),
        limit=20,
        window_seconds=60,
    )
    return await service.run_tests(
        session,
        user_id=user.id,
        session_id=session_id,
        payload=payload,
    )


@router.post(
    "/{session_id}/ai-review",
    response_model=AiReviewResponse,
    dependencies=[Depends(require_csrf)],
)
async def ai_review(
    session_id: UUID,
    payload: AiReviewRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AiReviewResponse:
    await enforce_rate_limit(
        "code_ai_review",
        str(user.id),
        limit=10,
        window_seconds=300,
    )
    return await service.ai_review(
        session,
        user_id=user.id,
        session_id=session_id,
        payload=payload,
    )


@router.post(
    "/{session_id}/complete",
    response_model=ResultResponse,
    dependencies=[Depends(require_csrf)],
)
async def complete_session(
    session_id: UUID,
    payload: CompleteRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ResultResponse:
    return await service.complete_session(
        session,
        user_id=user.id,
        session_id=session_id,
        payload=payload,
    )


@router.get("/{session_id}/result", response_model=ResultResponse)
async def get_result(
    session_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ResultResponse:
    return await service.get_result(
        session,
        user_id=user.id,
        session_id=session_id,
    )
