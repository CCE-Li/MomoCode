from httpx import AsyncClient

from app.core.tags import normalize_tags


def test_normalize_tags_accepts_hashtags_and_separators() -> None:
    assert normalize_tags(["#二分", "#二分", " 双指针 ", "#BFS"]) == [
        "二分",
        "双指针",
        "BFS",
    ]
    assert normalize_tags(["#二分 #BFS", "图论，模板"]) == [
        "二分",
        "BFS",
        "图论",
        "模板",
    ]
    assert normalize_tags(["#", " ", ""]) == []


async def test_catalog_tag_filter_and_tag_cloud(seeded_v2_client: AsyncClient) -> None:
    filtered = await seeded_v2_client.get("/api/v1/catalog/tasks?tag=%23二分")
    assert filtered.status_code == 200
    items = filtered.json()
    assert items
    assert all("二分" in item["tags"] for item in items)

    tags = await seeded_v2_client.get("/api/v1/catalog/tags")
    assert tags.status_code == 200
    tag_map = {item["tag"]: item["task_count"] for item in tags.json()}
    assert tag_map["二分"] > 0
    assert tag_map["树状数组"] > 0
    assert tag_map["BFS"] > 0
