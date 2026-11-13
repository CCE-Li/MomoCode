from httpx import AsyncClient

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics@example.com",
            "password": PASSWORD,
            "display_name": "Analytics",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _complete_session(
    client: AsyncClient,
    *,
    task_slug: str = "binary-search-template-001",
    self_assessment: str = "correct",
    hints: list[int] | None = None,
    error_types: list[str] | None = None,
) -> str:
    task = await client.get(f"/api/v1/catalog/tasks/{task_slug}")
    assert task.status_code == 200
    created = await client.post(
        "/api/v1/sessions",
        json={"task_id": task.json()["id"], "mode": "free"},
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
            "answer_payload": {
                "code": (
                    "int lower_bound_index(...) { WRONG }"
                    if self_assessment == "incorrect"
                    else "int lower_bound_index(...) { }"
                )
            },
            "error_types": error_types or [],
        },
    )
    assert answer.status_code == 200

    completed = await client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.status_code == 200
    return session_id


async def test_forgetting_curve_shape(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    response = await seeded_client.get("/api/v1/analytics/forgetting-curve")
    assert response.status_code == 200
    body = response.json()
    assert body["horizon_days"] == 30
    assert len(body["points"]) == 31
    assert body["fibonacci_review_days"] == [1, 2, 4, 7, 12, 20]
    assert body["sample_size"] == 0
    assert body["points"][0]["fibonacci_retention"] == 1.0
    assert body["points"][0]["my_retention"] is None


async def test_analytics_overview_trends_and_skills(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    await _complete_session(seeded_client)
    await _complete_session(seeded_client)
    await _complete_session(seeded_client)
    await _complete_session(seeded_client, self_assessment="incorrect")
    await _complete_session(
        seeded_client,
        task_slug="binary-search-errors-001",
        self_assessment="incorrect",
        error_types=["logic", "boundary"],
    )

    overview = await seeded_client.get("/api/v1/analytics/overview?days=30")
    assert overview.status_code == 200
    data = overview.json()
    assert data["sessions_completed"] == 5
    assert data["sample_size"] == 5
    assert data["insufficient_data"] is False
    assert data["correctness_rate"] == 0.6
    assert data["independent_rate"] == 1.0
    assert data["hint_dependency"] == 0.0
    assert 0.5 <= data["avg_normalized_time"] <= 1.5
    assert data["reviewed_count"] == 0
    assert data["due_count"] == 0
    template = next(item for item in data["training_types"] if item["training_type"] == "template")
    assert template["sessions"] == 4

    trends = await seeded_client.get("/api/v1/analytics/trends?days=30")
    assert trends.status_code == 200
    points = trends.json()["points"]
    assert len(points) == 30
    assert sum(point["sessions"] for point in points) == 5

    errors = await seeded_client.get("/api/v1/analytics/errors?days=30")
    assert errors.status_code == 200
    error_map = {item["error_type"]: item["count"] for item in errors.json()}
    assert error_map["logic"] == 1
    assert error_map["boundary"] == 1

    skills = await seeded_client.get("/api/v1/analytics/skills?days=30")
    assert skills.status_code == 200
    skill_rows = skills.json()
    template_skill = next(
        item for item in skill_rows if item["skill_slug"] == "binary-search-template"
    )
    assert template_skill["sample_size"] == 4
    assert template_skill["insufficient_data"] is False
    assert template_skill["skill_score"] is not None
    assert 0 <= template_skill["skill_score"] <= 100
    assert template_skill["score_version"] == "skill-score-v0"

    definitions = await seeded_client.get("/api/v1/analytics/definitions")
    assert definitions.status_code == 200
    keys = {item["key"] for item in definitions.json()}
    assert {
        "correctness_rate",
        "independent_rate",
        "hint_dependency",
        "normalized_time",
        "skill_score",
        "due_count",
        "reviewed_count",
    } <= keys


async def test_analytics_insufficient_data(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    await _complete_session(seeded_client)

    overview = await seeded_client.get("/api/v1/analytics/overview?days=30")
    assert overview.status_code == 200
    assert overview.json()["insufficient_data"] is True

    skills = await seeded_client.get("/api/v1/analytics/skills?days=30")
    assert skills.status_code == 200
    assert skills.json()[0]["insufficient_data"] is True
    assert skills.json()[0]["skill_score"] is None
