from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import enforce_rate_limit
from app.db.session import get_db_session
from app.modules.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.modules.auth.dependencies import (
    AuthContext,
    get_current_auth,
    get_current_user,
    require_csrf,
)
from app.modules.auth.models import User, UserSession
from app.modules.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    SessionResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.modules.auth.service import (
    authenticate_user,
    change_password,
    create_session,
    delete_account,
    generate_csrf_token,
    list_sessions,
    register_user,
    request_password_reset,
    reset_password,
    revoke_all_sessions,
    revoke_session,
    revoke_session_by_id,
    send_verification_email,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def _user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    await enforce_rate_limit(
        "register",
        f"{_client_ip(request)}:{payload.email}",
        limit=5,
        window_seconds=3600,
    )
    user = await register_user(session, payload)
    token, _ = await create_session(
        session,
        user,
        user_agent=_user_agent(request),
        ip_address=_client_ip(request),
    )
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, token, csrf_token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    await enforce_rate_limit(
        "login",
        f"{_client_ip(request)}:{payload.email}",
        limit=10,
        window_seconds=60,
    )
    user = await authenticate_user(session, str(payload.email), payload.password)
    token, _ = await create_session(
        session,
        user,
        user_agent=_user_agent(request),
        ip_address=_client_ip(request),
    )
    csrf_token = generate_csrf_token()
    set_auth_cookies(response, token, csrf_token)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def logout(
    response: Response,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await revoke_session(session, auth.session_row)
    clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


def _session_response(row: UserSession, current_session_id: UUID) -> SessionResponse:
    return SessionResponse(
        id=row.id,
        user_agent=row.user_agent,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        expires_at=row.expires_at,
        is_current=row.id == current_session_id,
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def sessions(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> list[SessionResponse]:
    rows = await list_sessions(session, auth.user.id)
    return [_session_response(row, auth.session_row.id) for row in rows]


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def revoke_one_session(
    session_id: UUID,
    response: Response,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    revoked = await revoke_session_by_id(session, auth.user.id, session_id)
    if revoked.id == auth.session_row.id:
        clear_auth_cookies(response)


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await change_password(
        session,
        auth.user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        current_session_id=auth.session_row.id,
    )


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def logout_all(
    response: Response,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await revoke_all_sessions(session, auth.user.id)
    clear_auth_cookies(response)


@router.post(
    "/verify-email",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def verify_email_endpoint(
    payload: VerifyEmailRequest,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await verify_email(session, payload.token)


@router.post(
    "/verify-email/resend",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def resend_verification(
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await enforce_rate_limit(
        "verify_email_resend",
        str(auth.user.id),
        limit=3,
        window_seconds=3600,
    )
    await send_verification_email(session, auth.user)


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def password_reset_request(
    payload: PasswordResetRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await enforce_rate_limit(
        "password_reset",
        f"{_client_ip(request)}:{payload.email}",
        limit=5,
        window_seconds=3600,
    )
    await request_password_reset(session, str(payload.email))
    return MessageResponse(message="如果该邮箱已注册，重置链接会发送到邮箱。")


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def password_reset_confirm(
    payload: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await reset_password(session, payload.token, payload.new_password)


@router.post(
    "/account/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_csrf)],
)
async def delete_account_endpoint(
    payload: DeleteAccountRequest,
    response: Response,
    auth: AuthContext = Depends(get_current_auth),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await delete_account(session, auth.user, payload.password)
    clear_auth_cookies(response)
