from httpx import AsyncClient


async def test_catalog_lists_seeded_content(seeded_client: AsyncClient) -> None:
    categories = await seeded_client.get("/api/v1/catalog/categories")
    assert categories.status_code == 200
    assert len(categories.json()) == 3

    algorithms = await seeded_client.get("/api/v1/catalog/algorithms")
    assert algorithms.status_code == 200
    assert len(algorithms.json()) == 10
    assert all(item["skill_count"] == 4 for item in algorithms.json())

    tasks = await seeded_client.get("/api/v1/catalog/tasks")
    assert tasks.status_code == 200
    assert len(tasks.json()) == 40


async def test_catalog_filters_and_detail(seeded_client: AsyncClient) -> None:
    recognition = await seeded_client.get(
        "/api/v1/catalog/tasks",
        params={"training_type": "recognition"},
    )
    assert recognition.status_code == 200
    assert len(recognition.json()) == 10
    assert all(item["training_type"] == "recognition" for item in recognition.json())

    binary_tasks = await seeded_client.get(
        "/api/v1/catalog/tasks",
        params={"algorithm": "binary-search"},
    )
    assert binary_tasks.status_code == 200
    assert len(binary_tasks.json()) == 4

    detail = await seeded_client.get("/api/v1/catalog/tasks/binary-search-template-001")
    assert detail.status_code == 200
    body = detail.json()
    assert body["target_skills"][0]["slug"] == "binary-search-template"
    assert "reference_solution_md" not in body
    assert "hints" not in body

    recognition_detail = await seeded_client.get(
        "/api/v1/catalog/tasks/binary-search-recognition-001"
    )
    assert recognition_detail.status_code == 200
    assert recognition_detail.json()["target_skills"] == []
    assert recognition_detail.json()["related_skills"] == []

    skills = await seeded_client.get(
        "/api/v1/catalog/skills",
        params={"skill_type": "recognition"},
    )
    assert skills.status_code == 200
    assert len(skills.json()) == 10

    skill = await seeded_client.get("/api/v1/catalog/skills/binary-search-template")
    assert skill.status_code == 200
    assert skill.json()["mastery_evidence_md"]
