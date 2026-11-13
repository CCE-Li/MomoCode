from httpx import ASGITransport, AsyncClient

from app.main import app

PASSWORD = "correct horse battery"
NEW_PASSWORD = "new correct horse battery"


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Security"},
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _login(client: AsyncClient, email: str, password: str = PASSWORD) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def test_session_listing_and_change_password(client: AsyncClient) -> None:
    transport = ASGITransport(app=app)
    await _register(client, "security@example.com")

    sessions = await client.get("/api/v1/auth/sessions")
    assert sessions.status_code == 200
    first_list = sessions.json()
    assert len(first_list) == 1
    assert first_list[0]["is_current"] is True
    assert "token_hash" not in first_list[0]
    assert "ip_hash" not in first_list[0]

    async with AsyncClient(transport=transport, base_url="http://test") as second:
        await _login(second, "security@example.com")
        both = await client.get("/api/v1/auth/sessions")
        assert len(both.json()) == 2

        wrong = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrong-password",
                "new_password": NEW_PASSWORD,
            },
        )
        assert wrong.status_code == 401

        unchanged = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": PASSWORD,
                "new_password": PASSWORD,
            },
        )
        assert unchanged.status_code == 422

        changed = await client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": PASSWORD,
                "new_password": NEW_PASSWORD,
            },
        )
        assert changed.status_code == 204
        assert (await client.get("/api/v1/auth/me")).status_code == 200
        assert (await second.get("/api/v1/auth/me")).status_code == 401

        old_login = await second.post(
            "/api/v1/auth/login",
            json={"email": "security@example.com", "password": PASSWORD},
        )
        assert old_login.status_code == 401
        await _login(second, "security@example.com", NEW_PASSWORD)


async def test_revoke_session_and_logout_all(client: AsyncClient) -> None:
    transport = ASGITransport(app=app)
    await _register(client, "revoke@example.com")

    async with AsyncClient(transport=transport, base_url="http://test") as second:
        await _login(second, "revoke@example.com")
        sessions = (await client.get("/api/v1/auth/sessions")).json()
        other = next(item for item in sessions if not item["is_current"])

        revoked = await client.delete(f"/api/v1/auth/sessions/{other['id']}")
        assert revoked.status_code == 204
        assert (await second.get("/api/v1/auth/me")).status_code == 401

        current = next(item for item in (await client.get("/api/v1/auth/sessions")).json())
        revoked_current = await client.delete(f"/api/v1/auth/sessions/{current['id']}")
        assert revoked_current.status_code == 204
        assert (await client.get("/api/v1/auth/me")).status_code == 401

    await _login(client, "revoke@example.com", PASSWORD)
    async with AsyncClient(transport=transport, base_url="http://test") as third:
        await _login(third, "revoke@example.com")
        logout_all = await client.post("/api/v1/auth/logout-all")
        assert logout_all.status_code == 204
        assert (await client.get("/api/v1/auth/me")).status_code == 401
        assert (await third.get("/api/v1/auth/me")).status_code == 401


async def test_security_mutations_require_csrf(client: AsyncClient) -> None:
    await _register(client, "csrf-security@example.com")

    change = await client.post(
        "/api/v1/auth/change-password",
        headers={"X-CSRF-Token": "wrong"},
        json={
            "current_password": PASSWORD,
            "new_password": NEW_PASSWORD,
        },
    )
    assert change.status_code == 403
    assert change.json()["error"]["code"] == "CSRF_INVALID"

    logout_all = await client.post(
        "/api/v1/auth/logout-all",
        headers={"X-CSRF-Token": "wrong"},
    )
    assert logout_all.status_code == 403
