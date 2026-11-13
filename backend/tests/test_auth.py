from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "email": "alice@example.com",
    "password": "correct horse battery",
    "display_name": "Alice",
}


async def test_register_me_logout(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["display_name"] == "Alice"
    assert body["csrf_token"]
    assert client.cookies.get("momo_session")
    assert client.cookies.get("momo_csrf")

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": body["csrf_token"]},
    )
    assert logout.status_code == 204

    me_after_logout = await client.get("/api/v1/auth/me")
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["error"]["code"] == "AUTH_REQUIRED"


async def test_duplicate_email_rejected(client: AsyncClient) -> None:
    first = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "AUTH_EMAIL_TAKEN"


async def test_invalid_login(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


async def test_login_after_logout(client: AsyncClient) -> None:
    register = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    csrf_token = register.json()["csrf_token"]

    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 204

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "alice@example.com"


async def test_logout_requires_csrf(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 403
    assert logout.json()["error"]["code"] == "CSRF_INVALID"


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
