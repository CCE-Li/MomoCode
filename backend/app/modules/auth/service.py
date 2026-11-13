import logging
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from urllib.parse import quote
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email import send_email
from app.core.errors import DomainError
from app.modules.analytics.models import UserSkillStats
from app.modules.auth.models import EmailToken, User, UserPreference, UserSession
from app.modules.auth.schemas import RegisterRequest
from app.modules.oj.models import OJAccount, Submission
from app.modules.practice.models import PracticeSession, SessionHint
from app.modules.review.models import (
    ReviewLog,
    SkillMemory,
    UserReviewItem,
    UserReviewLog,
    UserReviewMemory,
)
from app.modules.task_engine.models import PracticeTask

_settings = get_settings()
_password_hasher = PasswordHasher()
logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def hash_ip(ip_address: str) -> str:
    return sha256(f"{ip_address}:{_settings.session_secret}".encode()).hexdigest()


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def register_user(session: AsyncSession, payload: RegisterRequest) -> User:
    email = normalize_email(str(payload.email))
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise DomainError(
            code="AUTH_EMAIL_TAKEN",
            message="该邮箱已注册。",
            status_code=409,
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    session.add(user)
    try:
        await session.flush()
        session.add(UserPreference(user_id=user.id))
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DomainError(
            code="AUTH_EMAIL_TAKEN",
            message="该邮箱已注册。",
            status_code=409,
        ) from exc

    await session.refresh(user)
    await send_verification_email(session, user)
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User:
    normalized = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized))
    if user is None or not verify_password(password, user.password_hash):
        raise DomainError(
            code="AUTH_INVALID_CREDENTIALS",
            message="邮箱或密码不正确。",
            status_code=401,
        )
    if user.status != "active":
        raise DomainError(
            code="AUTH_DISABLED",
            message="账号已被禁用。",
            status_code=403,
        )

    user.last_login_at = utc_now()
    await session.commit()
    await session.refresh(user)
    return user


async def create_session(
    session: AsyncSession,
    user: User,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[str, UserSession]:
    token = token_urlsafe(32)
    row = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        user_agent=(user_agent or "")[:512] or None,
        ip_hash=hash_ip(ip_address) if ip_address else None,
        expires_at=utc_now() + timedelta(days=_settings.session_ttl_days),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return token, row


async def get_session_by_token(
    session: AsyncSession,
    token: str,
) -> UserSession | None:
    row = await session.scalar(
        select(UserSession).where(UserSession.token_hash == hash_token(token))
    )
    if row is None:
        return None
    if row.revoked_at is not None:
        return None
    if as_utc(row.expires_at) <= utc_now():
        return None
    return row


async def revoke_session(session: AsyncSession, row: UserSession) -> None:
    row.revoked_at = utc_now()
    await session.commit()


async def list_sessions(
    session: AsyncSession,
    user_id: UUID,
) -> list[UserSession]:
    rows = await session.scalars(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now(),
        )
        .order_by(UserSession.created_at.desc())
    )
    return list(rows)


async def revoke_session_by_id(
    session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> UserSession:
    row = await session.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    if row is None:
        raise DomainError(
            code="SESSION_NOT_FOUND",
            message="会话不存在。",
            status_code=404,
        )
    row.revoked_at = utc_now()
    await session.commit()
    await session.refresh(row)
    return row


async def revoke_other_sessions(
    session: AsyncSession,
    user_id: UUID,
    current_session_id: UUID,
) -> None:
    await session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.id != current_session_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )
    await session.commit()


async def revoke_all_sessions(
    session: AsyncSession,
    user_id: UUID,
) -> None:
    await session.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utc_now())
    )
    await session.commit()


async def change_password(
    session: AsyncSession,
    user: User,
    *,
    current_password: str,
    new_password: str,
    current_session_id: UUID,
) -> None:
    if not verify_password(current_password, user.password_hash):
        raise DomainError(
            code="AUTH_INVALID_CREDENTIALS",
            message="当前密码不正确。",
            status_code=401,
        )
    if verify_password(new_password, user.password_hash):
        raise DomainError(
            code="AUTH_PASSWORD_UNCHANGED",
            message="新密码不能与当前密码相同。",
            status_code=422,
        )
    user.password_hash = hash_password(new_password)
    await revoke_other_sessions(session, user.id, current_session_id)


_VERIFY_TTL = timedelta(hours=24)
_RESET_TTL = timedelta(hours=1)


async def create_email_token(
    session: AsyncSession,
    user_id: UUID,
    purpose: str,
    ttl: timedelta,
) -> str:
    await session.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == user_id,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=utc_now())
    )
    token = token_urlsafe(32)
    session.add(
        EmailToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_token(token),
            expires_at=utc_now() + ttl,
        )
    )
    await session.commit()
    return token


async def consume_email_token(
    session: AsyncSession,
    token: str,
    purpose: str,
) -> EmailToken:
    row = await session.scalar(select(EmailToken).where(EmailToken.token_hash == hash_token(token)))
    if (
        row is None
        or row.purpose != purpose
        or row.used_at is not None
        or as_utc(row.expires_at) <= utc_now()
    ):
        raise DomainError(
            code="EMAIL_TOKEN_INVALID",
            message="链接无效或已过期，请重新请求。",
            status_code=400,
        )
    return row


def _link(path: str, token: str) -> str:
    base = _settings.app_base_url.rstrip("/")
    return f"{base}{path}?token={quote(token)}"


async def send_verification_email(session: AsyncSession, user: User) -> None:
    if user.email_verified_at is not None:
        return
    token = await create_email_token(session, user.id, "verify_email", _VERIFY_TTL)
    link = _link("/verify-email", token)
    try:
        await send_email(
            to=user.email,
            subject="验证你的 MomoCode 邮箱",
            text=(
                "欢迎注册 MomoCode。\n\n"
                f"请打开以下链接验证邮箱（24 小时内有效）：\n{link}\n\n"
                "如果这不是你的操作，请忽略此邮件。"
            ),
        )
    except Exception:
        logger.warning(
            "Failed to send verification email to %s",
            user.email,
            exc_info=True,
        )


async def verify_email(session: AsyncSession, token: str) -> None:
    row = await consume_email_token(session, token, "verify_email")
    user = await session.get(User, row.user_id)
    if user is None:
        raise DomainError(
            code="EMAIL_TOKEN_INVALID",
            message="链接无效或已过期，请重新请求。",
            status_code=400,
        )
    user.email_verified_at = utc_now()
    row.used_at = utc_now()
    await session.commit()


async def request_password_reset(session: AsyncSession, email: str) -> None:
    normalized = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == normalized))
    if user is None:
        return
    token = await create_email_token(session, user.id, "reset_password", _RESET_TTL)
    link = _link("/reset-password", token)
    try:
        await send_email(
            to=user.email,
            subject="重置你的 MomoCode 密码",
            text=(
                "我们收到了重置密码的请求。\n\n"
                f"请打开以下链接设置新密码（1 小时内有效）：\n{link}\n\n"
                "如果这不是你的操作，请忽略此邮件。"
            ),
        )
    except Exception:
        logger.warning(
            "Failed to send password reset email to %s",
            user.email,
            exc_info=True,
        )


async def reset_password(
    session: AsyncSession,
    token: str,
    new_password: str,
) -> None:
    row = await consume_email_token(session, token, "reset_password")
    user = await session.get(User, row.user_id)
    if user is None:
        raise DomainError(
            code="EMAIL_TOKEN_INVALID",
            message="链接无效或已过期，请重新请求。",
            status_code=400,
        )
    user.password_hash = hash_password(new_password)
    row.used_at = utc_now()
    await revoke_all_sessions(session, user.id)


async def delete_account(
    session: AsyncSession,
    user: User,
    password: str,
) -> None:
    if not verify_password(password, user.password_hash):
        raise DomainError(
            code="AUTH_INVALID_CREDENTIALS",
            message="密码不正确，无法删除账号。",
            status_code=401,
        )

    user_id = user.id
    practice_session_ids = select(PracticeSession.id).where(PracticeSession.user_id == user_id)
    await session.execute(
        delete(SessionHint).where(SessionHint.session_id.in_(practice_session_ids))
    )
    await session.execute(delete(ReviewLog).where(ReviewLog.user_id == user_id))
    await session.execute(delete(Submission).where(Submission.user_id == user_id))
    await session.execute(delete(PracticeSession).where(PracticeSession.user_id == user_id))
    await session.execute(delete(PracticeTask).where(PracticeTask.created_by_user_id == user_id))
    await session.execute(delete(UserReviewLog).where(UserReviewLog.user_id == user_id))
    await session.execute(delete(UserReviewMemory).where(UserReviewMemory.user_id == user_id))
    await session.execute(delete(UserReviewItem).where(UserReviewItem.user_id == user_id))
    await session.execute(delete(SkillMemory).where(SkillMemory.user_id == user_id))
    await session.execute(delete(UserSkillStats).where(UserSkillStats.user_id == user_id))
    await session.execute(delete(EmailToken).where(EmailToken.user_id == user_id))
    await session.execute(delete(OJAccount).where(OJAccount.user_id == user_id))
    await session.execute(delete(UserPreference).where(UserPreference.user_id == user_id))
    await session.execute(delete(UserSession).where(UserSession.user_id == user_id))
    await session.delete(user)
    await session.commit()


def generate_csrf_token() -> str:
    return token_urlsafe(32)
