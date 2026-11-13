from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.review.models import ReviewLog, SkillMemory

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "review@example.com",
            "password": PASSWORD,
            "display_name": "Reviewer",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _task(client: AsyncClient, slug: str) -> dict[str, object]:
    response = await client.get(f"/api/v1/catalog/tasks/{slug}")
    assert response.status_code == 200
    return response.json()


async def _complete_coding_session(
    client: AsyncClient,
    *,
    mark_as_review: bool,
    hints: list[int] | None = None,
) -> dict[str, object]:
    task = await _task(client, "binary-search-template-001")
    created = await client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    assert created.status_code == 201
    session_id = created.json()["id"]

    for level in hints or []:
        hint = await client.post(
            f"/api/v1/sessions/{session_id}/hints",
            json={"level": level},
        )
        assert hint.status_code == 200

    answer = await client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { /* ... */ }"},
            "self_assessment": "correct",
            "error_types": [],
        },
    )
    assert answer.status_code == 200

    completed = await client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": mark_as_review},
    )
    assert completed.status_code == 200
    return completed.json()


async def test_formal_review_updates_fsrs(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client)
    result = await _complete_coding_session(seeded_client, mark_as_review=True)

    assert result["next_review_at"] is not None

    history = await seeded_client.get("/api/v1/reviews/history")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["rating"] in (1, 2, 3, 4)

    today = await seeded_client.get("/api/v1/reviews/today")
    assert today.status_code == 200
    assert today.json()["reviewed_today"] == 1

    memory = await seeded_db_session.scalar(select(SkillMemory))
    assert memory is not None
    assert memory.due_at is not None


async def test_free_practice_does_not_update_fsrs(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client)
    result = await _complete_coding_session(seeded_client, mark_as_review=False)

    assert result["next_review_at"] is None
    assert result["mark_as_review"] is False

    history = await seeded_client.get("/api/v1/reviews/history")
    assert history.json() == []
    log_count = await seeded_db_session.scalar(select(ReviewLog))
    assert log_count is None


async def test_due_queue_includes_overdue_memory(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client)
    await _complete_coding_session(seeded_client, mark_as_review=True)

    memory = await seeded_db_session.scalar(select(SkillMemory))
    assert memory is not None
    memory.due_at = datetime.now(UTC) - timedelta(days=1)
    await seeded_db_session.commit()

    due = await seeded_client.get("/api/v1/reviews/due")
    assert due.status_code == 200
    body = due.json()
    assert body["due_count"] >= 1
    assert body["items"][0]["task_slug"] == "binary-search-template-001"
    assert body["items"][0]["overdue"] is True


async def test_review_completion_is_idempotent(
    seeded_client: AsyncClient,
) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-template-001")
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { }"},
            "self_assessment": "correct",
        },
    )
    first = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )
    assert first.status_code == 200

    second = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )
    assert second.status_code == 200
    assert second.json()["next_review_at"] == first.json()["next_review_at"]

    history = await seeded_client.get("/api/v1/reviews/history")
    assert len(history.json()) == 1
