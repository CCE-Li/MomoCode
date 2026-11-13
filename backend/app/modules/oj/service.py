from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.modules.oj.adapter import get_adapter
from app.modules.oj.codeforces import CodeforcesAdapter
from app.modules.oj.models import OJAccount, Submission
from app.modules.oj.schemas import ManualSubmissionCreate, OJAccountCreate, SyncResult
from app.modules.practice.models import PracticeSession


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def list_accounts(session: AsyncSession, user_id: UUID) -> list[OJAccount]:
    rows = await session.scalars(
        select(OJAccount)
        .where(OJAccount.user_id == user_id, OJAccount.is_active.is_(True))
        .order_by(OJAccount.platform, OJAccount.handle)
    )
    return list(rows)


async def create_account(
    session: AsyncSession,
    user_id: UUID,
    payload: OJAccountCreate,
) -> OJAccount:
    get_adapter(payload.platform)
    row = OJAccount(
        user_id=user_id,
        platform=payload.platform,
        handle=payload.handle.strip(),
        display_name=payload.display_name,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DomainError(
            code="OJ_ACCOUNT_DUPLICATE",
            message="该 OJ 账号已关联。",
            status_code=409,
        ) from exc
    await session.refresh(row)
    return row


async def delete_account(
    session: AsyncSession,
    user_id: UUID,
    account_id: UUID,
) -> None:
    row = await session.scalar(
        select(OJAccount).where(
            OJAccount.id == account_id,
            OJAccount.user_id == user_id,
        )
    )
    if row is None:
        raise DomainError(
            code="OJ_ACCOUNT_NOT_FOUND",
            message="OJ 账号不存在。",
            status_code=404,
        )
    await session.delete(row)
    await session.commit()


async def _existing_submission(
    session: AsyncSession,
    user_id: UUID,
    platform: str,
    external_id: str,
) -> Submission | None:
    return await session.scalar(
        select(Submission).where(
            Submission.user_id == user_id,
            Submission.platform == platform,
            Submission.external_id == external_id,
        )
    )


async def create_manual_submission(
    session: AsyncSession,
    user_id: UUID,
    payload: ManualSubmissionCreate,
) -> tuple[Submission, bool]:
    adapter = get_adapter(payload.platform)
    external_id = adapter.validate_external_id(payload.external_id)
    problem_url = adapter.validate_problem_url(payload.problem_url) if payload.problem_url else None
    verdict = payload.verdict or adapter.normalize_verdict(payload.verdict_raw)

    existing = await _existing_submission(session, user_id, payload.platform, external_id)
    if existing is not None:
        return existing, True

    if payload.oj_account_id is not None:
        account = await session.scalar(
            select(OJAccount).where(
                OJAccount.id == payload.oj_account_id,
                OJAccount.user_id == user_id,
            )
        )
        if account is None:
            raise DomainError(
                code="OJ_ACCOUNT_NOT_FOUND",
                message="OJ 账号不存在。",
                status_code=404,
            )

    row = Submission(
        user_id=user_id,
        oj_account_id=payload.oj_account_id,
        platform=payload.platform,
        external_id=external_id,
        problem_ref=payload.problem_ref,
        problem_url=problem_url,
        verdict=verdict,
        verdict_raw=payload.verdict_raw,
        language=payload.language,
        time_ms=payload.time_ms,
        memory_kb=payload.memory_kb,
        submitted_at=_as_utc(payload.submitted_at),
        source="manual",
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await _existing_submission(session, user_id, payload.platform, external_id)
        if existing is None:
            raise
        return existing, True
    await session.refresh(row)
    return row, False


async def list_submissions(
    session: AsyncSession,
    user_id: UUID,
    *,
    platform: str | None = None,
    session_id: UUID | None = None,
) -> list[Submission]:
    statement = select(Submission).where(Submission.user_id == user_id)
    if platform is not None:
        statement = statement.where(Submission.platform == platform)
    if session_id is not None:
        statement = statement.where(Submission.session_id == session_id)
    statement = statement.order_by(
        Submission.submitted_at.desc().nulls_last(),
        Submission.created_at.desc(),
    )
    rows = await session.scalars(statement)
    return list(rows)


async def _owned_session(
    session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> PracticeSession:
    row = await session.scalar(
        select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user_id,
        )
    )
    if row is None:
        raise DomainError(
            code="SESSION_NOT_FOUND",
            message="训练会话不存在。",
            status_code=404,
        )
    return row


async def session_submissions(
    session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
) -> list[Submission]:
    await _owned_session(session, user_id, session_id)
    return await list_submissions(session, user_id, session_id=session_id)


async def link_submission(
    session: AsyncSession,
    user_id: UUID,
    session_id: UUID,
    submission_id: UUID,
) -> Submission:
    await _owned_session(session, user_id, session_id)
    row = await session.scalar(
        select(Submission).where(
            Submission.id == submission_id,
            Submission.user_id == user_id,
        )
    )
    if row is None:
        raise DomainError(
            code="OJ_SUBMISSION_NOT_FOUND",
            message="提交记录不存在。",
            status_code=404,
        )
    if row.session_id == session_id:
        return row
    if row.session_id is not None:
        raise DomainError(
            code="OJ_SUBMISSION_ALREADY_LINKED",
            message="该提交已关联到其他训练会话。",
            status_code=409,
        )
    row.session_id = session_id
    await session.commit()
    await session.refresh(row)
    return row


async def sync_account(
    session: AsyncSession,
    user_id: UUID,
    account_id: UUID,
) -> SyncResult:
    account = await session.scalar(
        select(OJAccount).where(
            OJAccount.id == account_id,
            OJAccount.user_id == user_id,
            OJAccount.is_active.is_(True),
        )
    )
    if account is None:
        raise DomainError(
            code="OJ_ACCOUNT_NOT_FOUND",
            message="OJ 账号不存在。",
            status_code=404,
        )
    if account.platform != "codeforces":
        raise DomainError(
            code="OJ_SYNC_UNSUPPORTED",
            message="当前仅支持 Codeforces 同步。",
            status_code=422,
        )

    submissions = await CodeforcesAdapter().fetch_submissions(account.handle, count=100)
    external_ids = [str(item["external_id"]) for item in submissions]
    existing: set[str] = set()
    if external_ids:
        existing = {
            str(value)
            for value in await session.scalars(
                select(Submission.external_id).where(
                    Submission.user_id == user_id,
                    Submission.platform == "codeforces",
                    Submission.external_id.in_(external_ids),
                )
            )
            if value is not None
        }

    created = 0
    for item in submissions:
        external_id = str(item["external_id"])
        if external_id in existing:
            continue
        session.add(
            Submission(
                user_id=user_id,
                oj_account_id=account.id,
                platform="codeforces",
                external_id=external_id,
                problem_ref=item.get("problem_ref"),
                problem_url=item.get("problem_url"),
                verdict=item.get("verdict"),
                verdict_raw=item.get("verdict_raw"),
                language=item.get("language"),
                time_ms=item.get("time_ms"),
                memory_kb=item.get("memory_kb"),
                submitted_at=item.get("submitted_at"),
                source="oj_sync",
                raw_payload=item.get("raw_payload"),
            )
        )
        existing.add(external_id)
        created += 1

    synced_at = datetime.now(UTC)
    account.last_synced_at = synced_at
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DomainError(
            code="OJ_SYNC_CONFLICT",
            message="同步过程中出现重复提交，请重试。",
            status_code=409,
        ) from exc

    return SyncResult(
        fetched=len(submissions),
        created=created,
        skipped=len(submissions) - created,
        last_synced_at=synced_at,
    )
