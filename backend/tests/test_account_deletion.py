from uuid import UUID

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import UserSkillStats
from app.modules.auth.models import EmailToken, User, UserPreference, UserSession
from app.modules.oj.models import OJAccount, Submission
from app.modules.practice.models import PracticeSession, SessionHint
from app.modules.review.models import ReviewLog, SkillMemory

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "delete@example.com",
            "password": PASSWORD,
            "display_name": "Delete Me",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _count(session: AsyncSession, model, user_id: UUID) -> int:
    value = await session.scalar(
        select(func.count()).select_from(model).where(model.user_id == user_id)
    )
    return int(value or 0)


async def test_delete_account_cascades_user_data(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client)
    me = await seeded_client.get("/api/v1/auth/me")
    user_id = UUID(me.json()["id"])

    task = await seeded_client.get("/api/v1/catalog/tasks/binary-search-template-001")
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task.json()["id"], "mode": "free"},
    )
    session_id = created.json()["id"]
    await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { }"},
            "self_assessment": "correct",
        },
    )
    await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )

    await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "delete_me"},
    )
    await seeded_client.post(
        "/api/v1/submissions/manual",
        json={"platform": "codeforces", "external_id": "delete-1"},
    )
    await seeded_client.get("/api/v1/analytics/skills")

    wrong = await seeded_client.post(
        "/api/v1/auth/account/delete",
        json={"password": "wrong-password", "confirmation": "DELETE"},
    )
    assert wrong.status_code == 401
    assert (await seeded_client.get("/api/v1/auth/me")).status_code == 200

    bad_confirmation = await seeded_client.post(
        "/api/v1/auth/account/delete",
        json={"password": PASSWORD, "confirmation": "delete"},
    )
    assert bad_confirmation.status_code == 422

    deleted = await seeded_client.post(
        "/api/v1/auth/account/delete",
        json={"password": PASSWORD, "confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    assert (await seeded_client.get("/api/v1/auth/me")).status_code == 401

    login = await seeded_client.post(
        "/api/v1/auth/login",
        json={"email": "delete@example.com", "password": PASSWORD},
    )
    assert login.status_code == 401

    hint_count = await seeded_db_session.scalar(
        select(func.count())
        .select_from(SessionHint)
        .join(PracticeSession, PracticeSession.id == SessionHint.session_id)
        .where(PracticeSession.user_id == user_id)
    )
    assert int(hint_count or 0) == 0
    for model in (
        User,
        UserSession,
        UserPreference,
        PracticeSession,
        ReviewLog,
        Submission,
        SkillMemory,
        UserSkillStats,
        OJAccount,
        EmailToken,
    ):
        if model is User:
            continue
        assert await _count(seeded_db_session, model, user_id) == 0, model.__name__

    user = await seeded_db_session.get(User, user_id)
    assert user is None
