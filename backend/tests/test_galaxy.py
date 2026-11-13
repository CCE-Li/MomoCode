from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.galaxy import (
    confidence_for,
    next_star_state,
    star_brightness,
)
from app.modules.review.models import SkillMemory

PASSWORD = "correct horse battery"


def test_star_state_hysteresis() -> None:
    assert next_star_state("dark", 0.80) == "lit"
    assert next_star_state("lit", 0.80) == "lit"
    assert next_star_state("lit", 0.50) == "lit"
    assert next_star_state("dark", 0.50) == "dark"
    assert next_star_state("lit", 0.20) == "dark"
    assert next_star_state("dark", 0.20) == "dark"


def test_brightness_confidence() -> None:
    assert confidence_for(0) == 0.0
    assert confidence_for(1) == 0.45
    assert confidence_for(2) == 0.7
    assert confidence_for(3) == 1.0
    assert star_brightness("dark", 0.9, 3) < 0.30
    assert star_brightness("lit", 0.95, 1) < star_brightness("lit", 0.95, 3)


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "galaxy@example.com",
            "password": PASSWORD,
            "display_name": "Stargazer",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _complete_formal_review(client: AsyncClient) -> None:
    task = await client.get("/api/v1/catalog/tasks/binary-search-template-001")
    assert task.status_code == 200
    created = await client.post(
        "/api/v1/sessions",
        json={"task_id": task.json()["id"], "mode": "free"},
    )
    assert created.status_code == 201
    session_id = created.json()["id"]

    answer = await client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { }"},
            "self_assessment": "correct",
        },
    )
    assert answer.status_code == 200

    completed = await client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )
    assert completed.status_code == 200


async def test_galaxy_starts_dark_and_lights_on_formal_review(
    seeded_client: AsyncClient,
) -> None:
    await _register(seeded_client)

    before = await seeded_client.get("/api/v1/analytics/galaxy")
    assert before.status_code == 200
    body = before.json()
    assert body["total_skills"] >= 40
    assert body["lit_count"] == 0
    assert all(item["star_state"] == "dark" for item in body["skills"])

    await _complete_formal_review(seeded_client)

    after = await seeded_client.get("/api/v1/analytics/galaxy")
    assert after.status_code == 200
    data = after.json()
    assert data["lit_count"] == 1
    lit = [item for item in data["skills"] if item["star_state"] == "lit"]
    assert len(lit) == 1
    assert lit[0]["mastery"] >= 75
    assert lit[0]["review_count"] == 1
    assert lit[0]["brightness"] > 0


async def test_galaxy_extinguishes_after_memory_decays(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client)
    await _complete_formal_review(seeded_client)

    lit = await seeded_client.get("/api/v1/analytics/galaxy")
    assert lit.json()["lit_count"] == 1

    memory = await seeded_db_session.scalar(select(SkillMemory))
    assert memory is not None
    memory.stability = 1.0
    memory.last_review_at = datetime.now(UTC) - timedelta(days=3650)
    await seeded_db_session.commit()

    dark = await seeded_client.get("/api/v1/analytics/galaxy")
    assert dark.status_code == 200
    data = dark.json()
    assert data["lit_count"] == 0
    assert all(item["star_state"] == "dark" for item in data["skills"])
