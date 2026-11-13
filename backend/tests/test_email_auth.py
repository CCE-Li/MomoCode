import re
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.modules.auth.models import EmailToken

PASSWORD = "correct horse battery"
NEW_PASSWORD = "after reset horse battery"


def _token_from_email(text: str) -> str:
    match = re.search(r"token=([A-Za-z0-9_\-]+)", text)
    assert match is not None, text
    return match.group(1)


async def _register(client: AsyncClient, email: str) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Mail User"},
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []

    async def fake_send(*, to: str, subject: str, text: str) -> None:
        messages.append({"to": to, "subject": subject, "text": text})

    monkeypatch.setattr("app.modules.auth.service.send_email", fake_send)
    return messages


async def test_email_verification(
    client: AsyncClient,
    sent_emails: list[dict[str, str]],
) -> None:
    await _register(client, "verify@example.com")
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == "verify@example.com"
    token = _token_from_email(sent_emails[0]["text"])

    me = await client.get("/api/v1/auth/me")
    assert me.json()["email_verified_at"] is None

    verified = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verified.status_code == 204
    me = await client.get("/api/v1/auth/me")
    assert me.json()["email_verified_at"] is not None

    reused = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "EMAIL_TOKEN_INVALID"

    count_before = len(sent_emails)
    resend = await client.post("/api/v1/auth/verify-email/resend")
    assert resend.status_code == 204
    assert len(sent_emails) == count_before


async def test_password_reset_revokes_sessions(
    client: AsyncClient,
    sent_emails: list[dict[str, str]],
) -> None:
    transport = ASGITransport(app=app)
    await _register(client, "reset@example.com")

    async with AsyncClient(transport=transport, base_url="http://test") as second:
        login = await second.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": PASSWORD},
        )
        assert login.status_code == 200
        second.headers["X-CSRF-Token"] = login.json()["csrf_token"]

        request = await client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "reset@example.com"},
        )
        assert request.status_code == 202
        assert "重置链接" in request.json()["message"]
        assert len(sent_emails) == 2
        token = _token_from_email(sent_emails[-1]["text"])

        confirm = await client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": token, "new_password": NEW_PASSWORD},
        )
        assert confirm.status_code == 204

        assert (await second.get("/api/v1/auth/me")).status_code == 401
        old_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": PASSWORD},
        )
        assert old_login.status_code == 401
        new_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": NEW_PASSWORD},
        )
        assert new_login.status_code == 200


async def test_password_reset_unknown_email_does_not_enumerate(
    client: AsyncClient,
    sent_emails: list[dict[str, str]],
) -> None:
    await _register(client, "known@example.com")
    count_before = len(sent_emails)
    response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@example.com"},
    )
    assert response.status_code == 202
    assert len(sent_emails) == count_before


async def test_expired_email_token_is_rejected(
    client: AsyncClient,
    sent_emails: list[dict[str, str]],
    db_session: AsyncSession,
) -> None:
    await _register(client, "expired@example.com")
    token = _token_from_email(sent_emails[0]["text"])
    row = await db_session.scalar(select(EmailToken).where(EmailToken.purpose == "verify_email"))
    assert row is not None
    row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    await db_session.commit()

    response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMAIL_TOKEN_INVALID"
