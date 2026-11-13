from httpx import AsyncClient

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "settings@example.com",
            "password": PASSWORD,
            "display_name": "Settings User",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def test_preferences_and_profile(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)

    preferences = await seeded_client.get("/api/v1/settings/preferences")
    assert preferences.status_code == 200
    defaults = preferences.json()
    assert defaults["timezone"] == "UTC"
    assert defaults["daily_review_limit"] == 50
    assert defaults["desired_retention"] == 0.9
    assert defaults["theme"] == "dark"
    assert defaults["locale"] == "zh-CN"

    updated = await seeded_client.patch(
        "/api/v1/settings/preferences",
        json={
            "timezone": "Asia/Shanghai",
            "daily_review_limit": 10,
            "desired_retention": 0.85,
            "theme": "light",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["timezone"] == "Asia/Shanghai"
    assert body["daily_review_limit"] == 10
    assert body["desired_retention"] == 0.85
    assert body["theme"] == "light"

    profile = await seeded_client.patch(
        "/api/v1/settings/profile",
        json={"display_name": "Renamed"},
    )
    assert profile.status_code == 200
    assert profile.json()["display_name"] == "Renamed"

    me = await seeded_client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["display_name"] == "Renamed"

    export = await seeded_client.get("/api/v1/settings/export")
    assert export.status_code == 200
    assert "attachment" in export.headers["content-disposition"]
    body = export.json()
    assert body["version"] == "export-v1"
    assert body["profile"]["display_name"] == "Renamed"
    assert "password_hash" not in export.text
    assert "token_hash" not in export.text
    assert "ip_hash" not in export.text
    assert isinstance(body["practice_sessions"], list)
    assert isinstance(body["sessions"], list)


async def test_invalid_timezone_and_csrf(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)

    invalid = await seeded_client.patch(
        "/api/v1/settings/preferences",
        json={"timezone": "Not/A_Timezone"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_TIMEZONE"

    csrf_failure = await seeded_client.patch(
        "/api/v1/settings/preferences",
        headers={"X-CSRF-Token": "wrong-token"},
        json={"daily_review_limit": 20},
    )
    assert csrf_failure.status_code == 403
    assert csrf_failure.json()["error"]["code"] == "CSRF_INVALID"
