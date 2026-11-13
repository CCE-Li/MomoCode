from uuid import UUID

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.task_engine.models import PracticeTask

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "display_name": "Task Author",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


def _payload(title: str = "我的二分模板题") -> dict[str, object]:
    return {
        "title": title,
        "training_type": "variant",
        "evaluation_mode": "self_assessment",
        "difficulty": 2,
        "oj_platform": "codeforces",
        "oj_problem_ref": "CF 706B",
        "oj_problem_url": "https://codeforces.com/problemset/problem/706/B",
        "statement_md": "完成这道二分查找经典题，并写下边界检查结论。",
        "constraints_md": "以 OJ 原题为准。",
        "target_skills": ["binary-search-template"],
        "related_skills": ["binary-search-recognition"],
        "hints": {"1": "先排序，再二分。"},
        "max_hint_level": 1,
        "tags": ["#二分", "#BFS", " 双指针 ", "#二分"],
    }


async def test_create_list_and_practice_user_task(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "author@example.com")
    created = await seeded_client.post("/api/v1/user-tasks", json=_payload())
    assert created.status_code == 201
    task = created.json()
    assert task["source_type"] == "user"
    assert task["slug"].startswith("user-")
    assert task["oj_problem_url"] == "https://codeforces.com/problemset/problem/706/B"
    assert set(task["tags"]) == {"二分", "BFS", "双指针"}

    by_tag = await seeded_client.get("/api/v1/user-tasks?tag=%23二分")
    assert by_tag.status_code == 200
    assert [item["id"] for item in by_tag.json()] == [task["id"]]

    listing = await seeded_client.get("/api/v1/user-tasks")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [task["id"]]

    catalog = await seeded_client.get("/api/v1/catalog/tasks")
    assert task["slug"] not in {item["slug"] for item in catalog.json()}
    hidden = await seeded_client.get(f"/api/v1/catalog/tasks/{task['slug']}")
    assert hidden.status_code == 404

    session = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    assert session.status_code == 201
    assert session.json()["task"]["id"] == task["id"]


async def test_user_task_is_private(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "author-private@example.com")
    task = (await seeded_client.post("/api/v1/user-tasks", json=_payload())).json()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other:
        await _register(other, "other-private@example.com")
        assert (await other.get("/api/v1/user-tasks")).json() == []
        assert (await other.get(f"/api/v1/user-tasks/{task['id']}")).status_code == 404
        assert (
            await other.post("/api/v1/sessions", json={"task_id": task["id"], "mode": "free"})
        ).status_code == 404
        assert (
            await other.patch(f"/api/v1/user-tasks/{task['id']}", json={"title": "越权"})
        ).status_code == 404
        assert (await other.delete(f"/api/v1/user-tasks/{task['id']}")).status_code == 404


async def test_update_and_soft_delete_user_task(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "author-update@example.com")
    task = (await seeded_client.post("/api/v1/user-tasks", json=_payload())).json()

    updated = await seeded_client.patch(
        f"/api/v1/user-tasks/{task['id']}",
        json={
            "title": "更新后的二分题",
            "difficulty": 3,
            "target_skills": ["binary-search-recognition"],
            "related_skills": [],
            "tags": ["#二分查找", "#贪心"],
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "更新后的二分题"
    assert body["difficulty"] == 3
    assert set(body["tags"]) == {"二分查找", "贪心"}
    assert [skill["slug"] for skill in body["target_skills"]] == ["binary-search-recognition"]

    deleted = await seeded_client.delete(f"/api/v1/user-tasks/{task['id']}")
    assert deleted.status_code == 204
    assert (await seeded_client.get("/api/v1/user-tasks")).json() == []
    assert (await seeded_client.get(f"/api/v1/user-tasks/{task['id']}")).status_code == 404


async def test_orphaned_user_task_is_not_public(
    seeded_client: AsyncClient,
    seeded_db_session: AsyncSession,
) -> None:
    await _register(seeded_client, "author-orphan@example.com")
    task = (await seeded_client.post("/api/v1/user-tasks", json=_payload())).json()

    row = await seeded_db_session.get(PracticeTask, UUID(task["id"]))
    assert row is not None
    row.created_by_user_id = None
    await seeded_db_session.commit()

    catalog = await seeded_client.get("/api/v1/catalog/tasks")
    assert task["slug"] not in {item["slug"] for item in catalog.json()}
    assert (await seeded_client.get(f"/api/v1/catalog/tasks/{task['slug']}")).status_code == 404
    assert (await seeded_client.get("/api/v1/user-tasks")).json() == []
    assert (
        await seeded_client.post(
            "/api/v1/sessions",
            json={"task_id": task["id"], "mode": "free"},
        )
    ).status_code == 404


async def test_bulk_import_and_atomic_unknown_skill(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "author-import@example.com")
    imported = await seeded_client.post(
        "/api/v1/user-tasks/import",
        json={"tasks": [_payload("批量题 A"), _payload("批量题 B")]},
    )
    assert imported.status_code == 201
    assert imported.json()["total"] == 2
    assert len((await seeded_client.get("/api/v1/user-tasks")).json()) == 2

    invalid = _payload("无效题")
    invalid["target_skills"] = ["does-not-exist"]
    rejected = await seeded_client.post(
        "/api/v1/user-tasks/import",
        json={"tasks": [_payload("有效题"), invalid]},
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["code"] == "UNKNOWN_SKILL"
    assert len((await seeded_client.get("/api/v1/user-tasks")).json()) == 2
