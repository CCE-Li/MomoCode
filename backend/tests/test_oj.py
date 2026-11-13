from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.errors import DomainError
from app.main import app
from app.modules.oj.adapter import ManualOJAdapter

PASSWORD = "correct horse battery"


async def _register(client: AsyncClient, email: str = "oj@example.com") -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "display_name": "OJ User",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _completed_session(client: AsyncClient) -> str:
    task = await client.get("/api/v1/catalog/tasks/binary-search-template-001")
    created = await client.post(
        "/api/v1/sessions",
        json={"task_id": task.json()["id"], "mode": "free"},
    )
    session_id = created.json()["id"]
    await client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { }"},
            "self_assessment": "correct",
        },
    )
    completed = await client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.status_code == 200
    return session_id


def test_manual_adapter_normalizes_verdicts() -> None:
    adapter = ManualOJAdapter()
    assert adapter.normalize_verdict("AC") == "accepted"
    assert adapter.normalize_verdict("wrong answer") == "wrong_answer"
    assert adapter.normalize_verdict("tle") == "time_limit_exceeded"
    assert adapter.normalize_verdict("unknown-verdict") is None
    assert adapter.validate_external_id(" 123456 ") == "123456"


async def test_oj_account_and_manual_submission(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)

    account = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "tourist"},
    )
    assert account.status_code == 201
    assert account.json()["handle"] == "tourist"

    duplicate_account = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "tourist"},
    )
    assert duplicate_account.status_code == 409

    submission = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={
            "platform": "codeforces",
            "external_id": "123456",
            "problem_ref": "1A",
            "problem_url": "https://codeforces.com/problemset/problem/1/A",
            "verdict": "accepted",
            "verdict_raw": "Accepted",
            "language": "C++17",
            "time_ms": 15,
            "memory_kb": 1024,
            "submitted_at": "2026-11-10T12:00:00Z",
        },
    )
    assert submission.status_code == 201
    body = submission.json()
    assert body["duplicate"] is False
    submission_id = body["submission"]["id"]
    assert body["submission"]["verdict"] == "accepted"

    duplicate = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={
            "platform": "codeforces",
            "external_id": "123456",
            "verdict": "accepted",
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["submission"]["id"] == submission_id

    session_id = await _completed_session(seeded_client)
    linked = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/submissions",
        json={"submission_id": submission_id},
    )
    assert linked.status_code == 200
    assert linked.json()["session_id"] == session_id

    session_submissions = await seeded_client.get(f"/api/v1/sessions/{session_id}/submissions")
    assert session_submissions.status_code == 200
    assert len(session_submissions.json()) == 1

    accounts = await seeded_client.get("/api/v1/oj/accounts")
    assert accounts.status_code == 200
    account_id = accounts.json()[0]["id"]
    deleted = await seeded_client.delete(f"/api/v1/oj/accounts/{account_id}")
    assert deleted.status_code == 204
    assert (await seeded_client.get("/api/v1/oj/accounts")).json() == []


async def test_manual_submission_missing_fields_and_url_validation(
    seeded_client: AsyncClient,
) -> None:
    await _register(seeded_client)

    minimal = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={"platform": "atcoder", "external_id": "abc-1"},
    )
    assert minimal.status_code == 201
    body = minimal.json()["submission"]
    assert body["verdict"] is None
    assert body["language"] is None
    assert body["time_ms"] is None
    assert body["memory_kb"] is None
    assert body["submitted_at"] is None

    invalid_url = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={
            "platform": "codeforces",
            "external_id": "abc-2",
            "problem_url": "https://evil.example.com/problem",
        },
    )
    assert invalid_url.status_code == 422
    assert invalid_url.json()["error"]["code"] == "OJ_URL_INVALID"

    invalid_id = await seeded_client.post(
        "/api/v1/submissions/manual",
        json={"platform": "codeforces", "external_id": "bad id!"},
    )
    assert invalid_id.status_code == 422
    assert invalid_id.json()["error"]["code"] == "OJ_EXTERNAL_ID_INVALID"


async def test_codeforces_sync_is_idempotent(
    seeded_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _register(seeded_client)
    account = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "sync_user"},
    )
    account_id = account.json()["id"]

    async def fake_fetch(self, handle: str, *, count: int = 100) -> list[dict]:
        assert handle == "sync_user"
        assert count == 100
        return [
            {
                "external_id": "1001",
                "problem_ref": "1A",
                "problem_url": "https://codeforces.com/contest/1/problem/A",
                "verdict": "accepted",
                "verdict_raw": "OK",
                "language": "C++17",
                "time_ms": 15,
                "memory_kb": 1024,
                "submitted_at": datetime(2026, 1, 1, tzinfo=UTC),
                "raw_payload": {"testset": "TESTS"},
            },
            {
                "external_id": "1002",
                "problem_ref": "1B",
                "problem_url": "https://codeforces.com/contest/1/problem/B",
                "verdict": "wrong_answer",
                "verdict_raw": "WRONG_ANSWER",
                "language": "C++17",
                "time_ms": 20,
                "memory_kb": 2048,
                "submitted_at": datetime(2026, 1, 2, tzinfo=UTC),
                "raw_payload": {"testset": "TESTS"},
            },
        ]

    monkeypatch.setattr(
        "app.modules.oj.service.CodeforcesAdapter.fetch_submissions",
        fake_fetch,
    )

    first = await seeded_client.post(f"/api/v1/oj/accounts/{account_id}/sync")
    assert first.status_code == 200
    assert first.json()["fetched"] == 2
    assert first.json()["created"] == 2
    assert first.json()["skipped"] == 0

    second = await seeded_client.post(f"/api/v1/oj/accounts/{account_id}/sync")
    assert second.status_code == 200
    assert second.json()["created"] == 0
    assert second.json()["skipped"] == 2

    submissions = await seeded_client.get("/api/v1/submissions?platform=codeforces")
    assert len(submissions.json()) == 2
    assert all(item["source"] == "oj_sync" for item in submissions.json())
    accounts = await seeded_client.get("/api/v1/oj/accounts")
    assert accounts.json()[0]["last_synced_at"] is not None


async def test_codeforces_sync_failure_and_unsupported_platform(
    seeded_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _register(seeded_client)
    atcoder = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "atcoder", "handle": "atcoder_user"},
    )
    unsupported = await seeded_client.post(f"/api/v1/oj/accounts/{atcoder.json()['id']}/sync")
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "OJ_SYNC_UNSUPPORTED"

    codeforces = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "failure_user"},
    )

    async def failing_fetch(self, handle: str, *, count: int = 100) -> list[dict]:
        raise DomainError(
            code="OJ_SYNC_FAILED",
            message="Codeforces 同步失败，请稍后重试。",
            status_code=502,
        )

    monkeypatch.setattr(
        "app.modules.oj.service.CodeforcesAdapter.fetch_submissions",
        failing_fetch,
    )
    failed = await seeded_client.post(f"/api/v1/oj/accounts/{codeforces.json()['id']}/sync")
    assert failed.status_code == 502
    assert failed.json()["error"]["code"] == "OJ_SYNC_FAILED"
    assert (await seeded_client.get("/api/v1/submissions")).json() == []


async def test_codeforces_sync_requires_ownership(
    seeded_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _register(seeded_client)
    account = await seeded_client.post(
        "/api/v1/oj/accounts",
        json={"platform": "codeforces", "handle": "owner_only"},
    )

    async def fake_fetch(self, handle: str, *, count: int = 100) -> list[dict]:
        return []

    monkeypatch.setattr(
        "app.modules.oj.service.CodeforcesAdapter.fetch_submissions",
        fake_fetch,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as other:
        await _register(other, "other-oj@example.com")
        response = await other.post(f"/api/v1/oj/accounts/{account.json()['id']}/sync")
        assert response.status_code == 404
