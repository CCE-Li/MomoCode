from httpx import ASGITransport, AsyncClient

from app.main import app

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": email},
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def test_user_data_isolation(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "owner@example.com")

    task = await seeded_client.get("/api/v1/catalog/tasks/binary-search-template-001")
    task_id = task.json()["id"]
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task_id, "mode": "free"},
    )
    assert created.status_code == 201
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

    submission = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={
            "platform": "codeforces",
            "external_id": "isolation-1",
            "verdict": "accepted",
        },
    )
    assert submission.status_code == 201
    submission_id = submission.json()["submission"]["id"]

    await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "owner"},
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other:
        await _register(other, "intruder@example.com")

        assert (await other.get(f"/api/v1/sessions/{session_id}")).status_code == 404
        assert (await other.get(f"/api/v1/sessions/{session_id}/result")).status_code == 404
        assert (await other.get(f"/api/v1/sessions/{session_id}/submissions")).status_code == 404
        assert (
            await other.post(
                f"/api/v1/sessions/{session_id}/submissions",
                json={"submission_id": submission_id},
            )
        ).status_code == 404

        assert (await other.get("/api/v1/oj/accounts")).json() == []
        assert (await other.get("/api/v1/submissions")).json() == []
        assert (await other.get("/api/v1/reviews/due")).json()["due_count"] == 0

        overview = await other.get("/api/v1/analytics/overview?days=30")
        assert overview.status_code == 200
        assert overview.json()["sessions_completed"] == 0
