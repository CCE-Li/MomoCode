from httpx import ASGITransport, AsyncClient

from app.main import app

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "display_name": "Reviewer",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _create_item(client: AsyncClient, title: str = "复盘：树状数组区间和") -> dict:
    response = await client.post(
        "/api/v1/reviews/custom-items",
        json={
            "title": title,
            "content_md": "记住 lowbit(i)=i&-i，更新时 i+=lowbit(i)，查询时 i-=lowbit(i)。",
            "tags": ["#数据结构", "模板", "#数据结构"],
            "source_url": "https://www.luogu.com.cn/problem/P3374",
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_custom_review_item_participates_in_fsrs(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "custom@example.com")
    item = await _create_item(seeded_client)

    assert item["due_at"] is not None
    assert item["tags"] == ["数据结构", "模板"]

    due = await seeded_client.get("/api/v1/reviews/due")
    assert due.status_code == 200
    custom_items = [row for row in due.json()["items"] if row["kind"] == "custom"]
    assert len(custom_items) == 1
    assert custom_items[0]["custom_item_id"] == item["id"]
    assert custom_items[0]["title"] == item["title"]
    assert due.json()["due_count"] >= 1

    reviewed = await seeded_client.post(
        f"/api/v1/reviews/custom-items/{item['id']}/review",
        json={"rating": 3, "review_duration_ms": 1200},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["next_due_at"] is not None

    today = await seeded_client.get("/api/v1/reviews/today")
    assert today.status_code == 200
    assert today.json()["reviewed_today"] == 1

    history = await seeded_client.get("/api/v1/reviews/history")
    assert history.status_code == 200
    assert history.json()[0]["kind"] == "custom"
    assert history.json()[0]["title"] == item["title"]
    assert history.json()[0]["rating"] == 3


async def test_update_and_deactivate_custom_item(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "custom-update@example.com")
    item = await _create_item(seeded_client)

    updated = await seeded_client.patch(
        f"/api/v1/reviews/custom-items/{item['id']}",
        json={"title": "更新后的复盘", "tags": ["图论"], "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "更新后的复盘"
    assert updated.json()["tags"] == ["图论"]
    assert updated.json()["is_active"] is False

    listed = await seeded_client.get("/api/v1/reviews/custom-items")
    assert listed.status_code == 200
    assert listed.json() == []

    inactive = await seeded_client.get(
        "/api/v1/reviews/custom-items?include_inactive=true",
    )
    assert len(inactive.json()) == 1

    deleted = await seeded_client.delete(f"/api/v1/reviews/custom-items/{item['id']}")
    assert deleted.status_code == 204
    missing = await seeded_client.post(
        f"/api/v1/reviews/custom-items/{item['id']}/review",
        json={"rating": 3},
    )
    assert missing.status_code == 404


async def test_custom_review_is_user_scoped(seeded_client: AsyncClient) -> None:
    await _register(seeded_client, "owner@example.com")
    item = await _create_item(seeded_client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other:
        await _register(other, "other@example.com")
        assert (await other.get("/api/v1/reviews/custom-items")).json() == []
        assert (
            await other.patch(
                f"/api/v1/reviews/custom-items/{item['id']}",
                json={"title": "越权修改"},
            )
        ).status_code == 404
        assert (
            await other.post(
                f"/api/v1/reviews/custom-items/{item['id']}/review",
                json={"rating": 3},
            )
        ).status_code == 404
        assert (await other.delete(f"/api/v1/reviews/custom-items/{item['id']}")).status_code == 404


async def test_oj_task_without_judge_uses_self_assessment(
    seeded_v2_client: AsyncClient,
) -> None:
    await _register(seeded_v2_client, "oj-ungraded@example.com")
    task = await seeded_v2_client.get(
        "/api/v1/catalog/tasks/manual-fenwick-luogu-p3374-classic",
    )
    assert task.status_code == 200
    task_body = task.json()
    assert task_body["oj_problem_url"] == "https://www.luogu.com.cn/problem/P3374"

    created = await seeded_v2_client.post(
        "/api/v1/sessions",
        json={"task_id": task_body["id"], "mode": "free"},
    )
    assert created.status_code == 201
    session_id = created.json()["id"]

    rejected = await seeded_v2_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"answer_payload": {"code": "int main() { return 0; }"}},
    )
    assert rejected.status_code == 422

    answer = await seeded_v2_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int main() { return 0; }"},
            "self_assessment": "correct",
        },
    )
    assert answer.status_code == 200

    completed = await seeded_v2_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )
    assert completed.status_code == 200
    assert completed.json()["next_review_at"] is not None

    history = await seeded_v2_client.get("/api/v1/reviews/history")
    assert history.status_code == 200
    assert history.json()[0]["rating"] == 4
    assert history.json()[0]["skill_slug"] == "fenwick-template"
