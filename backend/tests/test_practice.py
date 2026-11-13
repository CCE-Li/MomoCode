from httpx import AsyncClient

PASSWORD = "correct horse battery"


async def _fake_judge(code: str, cases: list[object]) -> dict[str, object]:
    return {
        "result": "correct",
        "passed": len(cases),
        "total": len(cases),
        "score": 1.0,
        "cases": [],
    }


async def _register(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "practice@example.com",
            "password": PASSWORD,
            "display_name": "Practice",
        },
    )
    assert response.status_code == 201
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]


async def _task(client: AsyncClient, slug: str) -> dict[str, object]:
    response = await client.get(f"/api/v1/catalog/tasks/{slug}")
    assert response.status_code == 200
    return response.json()


async def test_recognition_training_flow(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-recognition-001")
    assert task["target_skills"] == []

    skill = await seeded_client.get("/api/v1/catalog/skills/binary-search-recognition")
    assert skill.status_code == 200
    target_id = skill.json()["id"]

    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    assert created.status_code == 201
    session = created.json()
    assert session["status"] == "in_progress"
    assert session["training_type"] == "recognition"
    assert "reference_solution_md" not in session["task"]
    assert session["task"]["target_skills"] == []

    session_id = session["id"]
    hint = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/hints",
        json={"level": 1},
    )
    assert hint.status_code == 200
    assert hint.json()["content"]
    hint_again = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/hints",
        json={"level": 1},
    )
    assert hint_again.json()["content"] == hint.json()["content"]

    answer = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"answer_payload": {"selected_skill_ids": [target_id]}},
    )
    assert answer.status_code == 200
    assert answer.json()["status"] == "submitted"
    assert answer.json()["auto_grade"]["result"] == "correct"
    assert answer.json()["auto_grade"]["overlap_score"] == 1.0

    completed = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["time_spent_ms"] is not None
    assert completed.json()["reference_solution_md"] is None

    result = await seeded_client.get(f"/api/v1/sessions/{session_id}/result")
    assert result.status_code == 200
    assert result.json()["auto_grade"]["result"] == "correct"


async def test_recognition_partial_and_incorrect(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-recognition-001")
    skill = await seeded_client.get("/api/v1/catalog/skills/binary-search-recognition")
    target_id = skill.json()["id"]
    wrong_id = "00000000-0000-0000-0000-000000000000"

    partial = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    partial_id = partial.json()["id"]
    partial_answer = await seeded_client.post(
        f"/api/v1/sessions/{partial_id}/answers",
        json={"answer_payload": {"selected_skill_ids": [target_id, wrong_id]}},
    )
    assert partial_answer.json()["auto_grade"]["result"] == "partial"

    incorrect = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    incorrect_id = incorrect.json()["id"]
    incorrect_answer = await seeded_client.post(
        f"/api/v1/sessions/{incorrect_id}/answers",
        json={"answer_payload": {"selected_skill_ids": []}},
    )
    assert incorrect_answer.json()["auto_grade"]["result"] == "incorrect"


async def test_coding_training_flow(
    seeded_client: AsyncClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.modules.practice.service.judge_cpp",
        _fake_judge,
    )
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-template-001")
    assert task["sample_cases"]
    assert "judge" not in task["expected_output_spec"]

    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    run = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/run",
        json={
            "code": "int main() { return 0; }",
            "cases": [{"input": "1 2\n", "expected_output": "3\n"}],
        },
    )
    assert run.status_code == 200
    assert run.json()["result"] == "correct"
    still_open = await seeded_client.get(f"/api/v1/sessions/{session_id}")
    assert still_open.json()["status"] == "in_progress"

    hint = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/hints",
        json={"level": 3},
    )
    assert hint.status_code == 200

    answer = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { /* ... */ }"},
            "error_types": [],
        },
    )
    assert answer.status_code == 200
    assert answer.json()["self_assessment"] is None
    assert answer.json()["auto_grade"]["result"] == "correct"

    completed = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": True},
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["status"] == "completed"
    assert body["mark_as_review"] is True
    assert body["reference_solution_md"]
    assert body["hints_used"][0]["level"] == 3


async def test_variant_training_flow(
    seeded_client: AsyncClient,
    monkeypatch,
) -> None:
    async def partial_judge(code: str, cases: list[object]) -> dict[str, object]:
        return {
            "result": "partial",
            "passed": 1,
            "total": 2,
            "score": 0.5,
            "cases": [],
        }

    monkeypatch.setattr(
        "app.modules.practice.service.judge_cpp",
        partial_judge,
    )
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-variant-001")

    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    hint = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/hints",
        json={"level": 2},
    )
    assert hint.status_code == 200

    answer = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "long long max_piece_length(...) { }"},
        },
    )
    assert answer.status_code == 200

    completed = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["training_type"] == "variant"
    assert body["status"] == "completed"
    assert body["self_assessment"] is None
    assert body["auto_grade"]["result"] == "partial"
    assert body["reference_solution_md"]


async def test_correction_training_flow(
    seeded_client: AsyncClient,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.modules.practice.service.judge_cpp",
        _fake_judge,
    )
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-errors-001")

    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    answer = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={
            "answer_payload": {"code": "int lower_bound_index(...) { fixed }"},
            "error_types": ["boundary", "overflow"],
        },
    )
    assert answer.status_code == 200

    completed = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.status_code == 200
    body = completed.json()
    assert body["training_type"] == "correction"
    assert body["error_types"] == ["boundary", "overflow"]
    assert body["status"] == "completed"


async def test_draft_code_survives_and_resets_on_new_session(
    seeded_client: AsyncClient,
) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-template-001")
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]
    assert created.json()["draft_code"] is None

    saved = await seeded_client.put(
        f"/api/v1/sessions/{session_id}/draft",
        json={"code": "int main() { /* draft */ }"},
    )
    assert saved.status_code == 200
    assert saved.json()["draft_code"] == "int main() { /* draft */ }"
    assert saved.json()["draft_saved_at"] is not None

    reloaded = await seeded_client.get(f"/api/v1/sessions/{session_id}")
    assert reloaded.json()["draft_code"] == "int main() { /* draft */ }"

    submitted = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"answer_payload": {"code": "int main() { return 0; }"}},
    )
    assert submitted.status_code == 200

    completed = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert completed.json()["submitted_code"] == "int main() { return 0; }"

    blocked = await seeded_client.put(
        f"/api/v1/sessions/{session_id}/draft",
        json={"code": "late edit"},
    )
    assert blocked.status_code == 409

    review = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "review"},
    )
    assert review.json()["draft_code"] is None


async def test_ai_review_returns_structured_verdict(
    seeded_client: AsyncClient,
    monkeypatch,
) -> None:
    async def fake_llm(**_: object) -> dict[str, object]:
        return {
            "verdict": "partial",
            "score": 70,
            "summary": "思路正确，边界处理不完整。",
            "issues": ["未处理空数组"],
            "suggestions": ["补充 n == 0 的判断"],
        }

    monkeypatch.setattr(
        "app.modules.practice.service.judge_with_llm",
        fake_llm,
    )
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-template-001")
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    response = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/ai-review",
        json={"code": "int main() { return 0; }"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "partial"
    assert body["score"] == 70
    assert body["issues"] == ["未处理空数组"]


async def test_ai_review_unavailable_without_key(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-template-001")
    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    response = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/ai-review",
        json={"code": "int main() { return 0; }"},
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "unavailable"


async def test_invalid_session_transitions(seeded_client: AsyncClient) -> None:
    await _register(seeded_client)
    task = await _task(seeded_client, "binary-search-recognition-001")

    created = await seeded_client.post(
        "/api/v1/sessions",
        json={"task_id": task["id"], "mode": "free"},
    )
    session_id = created.json()["id"]

    complete_before_submit = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"mark_as_review": False},
    )
    assert complete_before_submit.status_code == 409
    assert complete_before_submit.json()["error"]["code"] == "SESSION_STATE_CONFLICT"

    skill = await seeded_client.get("/api/v1/catalog/skills/binary-search-recognition")
    target_id = skill.json()["id"]
    first = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"answer_payload": {"selected_skill_ids": [target_id]}},
    )
    assert first.status_code == 200

    second = await seeded_client.post(
        f"/api/v1/sessions/{session_id}/answers",
        json={"answer_payload": {"selected_skill_ids": [target_id]}},
    )
    assert second.status_code == 409
