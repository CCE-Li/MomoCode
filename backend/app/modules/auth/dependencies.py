from dataclasses import dataclass
from secrets import compare_digest

from fastapi import Cookie, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_db_session
from app.modules.auth.models import User, UserSession
from app.modules.auth.service import get_session_by_token, utc_now

_settings = get_settings()


@dataclass(slots=True)
class AuthContext:
    user: User
    session_row: UserSession


async def get_current_auth(
    session: AsyncSession = Depends(get_db_session),
    token: str | None = Cookie(default=None, alias=_settings.session_cookie_name),
) -> AuthContext:
    if not token:
        raise DomainError(
            code="AUTH_REQUIRED",
            message="请先登录。",
            status_code=401,
        )

    row = await get_session_by_token(session, token)
    if row is None:
        raise DomainError(
            code="AUTH_REQUIRED",
            message="会话已过期，请重新登录。",
            status_code=401,
        )

    user = await session.get(User, row.user_id)
    if user is None or user.status != "active":
        raise DomainError(
            code="AUTH_REQUIRED",
            message="会话已失效，请重新登录。",
            status_code=401,
        )

    row.last_used_at = utc_now()
    await session.commit()
    return AuthContext(user=user, session_row=row)


async def get_current_user(
    auth: AuthContext = Depends(get_current_auth),
) -> User:
    return auth.user


async def require_csrf(
    request: Request,
    csrf_cookie: str | None = Cookie(default=None, alias=_settings.csrf_cookie_name),
) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    header = request.headers.get("X-CSRF-Token")
    if not csrf_cookie or not header or not compare_digest(csrf_cookie, header):
        raise DomainError(
            code="CSRF_INVALID",
            message="CSRF 校验失败，请刷新页面后重试。",
            status_code=403,
        )
