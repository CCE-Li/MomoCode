import asyncio
from datetime import UTC, datetime

import httpx

from app.core.errors import DomainError

CODEFORCES_API = "https://codeforces.com/api/user.status"

VERDICT_MAP = {
    "OK": "accepted",
    "WRONG_ANSWER": "wrong_answer",
    "TIME_LIMIT_EXCEEDED": "time_limit_exceeded",
    "MEMORY_LIMIT_EXCEEDED": "memory_limit_exceeded",
    "RUNTIME_ERROR": "runtime_error",
    "COMPILATION_ERROR": "compilation_error",
    "PARTIAL": "partially_accepted",
}


class CodeforcesAdapter:
    platform = "codeforces"

    async def fetch_submissions(
        self,
        handle: str,
        *,
        count: int = 100,
    ) -> list[dict[str, object]]:
        normalized_handle = handle.strip()
        if not normalized_handle:
            raise DomainError(
                code="OJ_HANDLE_INVALID",
                message="Codeforces 账号标识不能为空。",
                status_code=422,
            )

        params: dict[str, str | int] = {
            "handle": normalized_handle,
            "from": 1,
            "count": min(max(count, 1), 1000),
        }
        last_error: Exception | None = None
        async with httpx.AsyncClient(
            timeout=15,
            follow_redirects=True,
            headers={"User-Agent": "MomoCode/0.1 (manual OJ sync)"},
        ) as client:
            for attempt in range(3):
                try:
                    response = await client.get(CODEFORCES_API, params=params)
                    response.raise_for_status()
                    payload = response.json()
                    if payload.get("status") != "OK":
                        raise DomainError(
                            code="OJ_SYNC_FAILED",
                            message="Codeforces 返回同步失败。",
                            status_code=502,
                        )
                    result = payload.get("result")
                    if not isinstance(result, list):
                        raise ValueError("result is not a list")
                    return [
                        normalized
                        for item in result
                        if (normalized := self._normalize_submission(item)) is not None
                    ]
                except DomainError:
                    raise
                except (httpx.HTTPError, ValueError) as exc:
                    last_error = exc
                    if attempt < 2:
                        await asyncio.sleep(0.5 * (attempt + 1))

        raise DomainError(
            code="OJ_SYNC_FAILED",
            message="Codeforces 同步失败，请稍后重试。",
            status_code=502,
        ) from last_error

    def _normalize_submission(self, item: object) -> dict[str, object] | None:
        if not isinstance(item, dict):
            return None
        external_id = item.get("id")
        creation_time = item.get("creationTimeSeconds")
        if external_id is None or creation_time is None:
            return None

        problem = item.get("problem")
        problem_data = problem if isinstance(problem, dict) else {}
        contest_id = problem_data.get("contestId")
        index = problem_data.get("index")
        problem_ref = (
            f"{contest_id}{index}"
            if contest_id is not None and index is not None
            else (str(index) if index is not None else None)
        )
        problem_url = (
            f"https://codeforces.com/contest/{contest_id}/problem/{index}"
            if contest_id is not None and index is not None
            else None
        )

        verdict_raw = item.get("verdict")
        verdict = VERDICT_MAP.get(str(verdict_raw), "other") if verdict_raw is not None else None
        memory_bytes = item.get("memoryConsumedBytes")
        time_ms = item.get("timeConsumedMillis")

        return {
            "external_id": str(external_id),
            "problem_ref": problem_ref,
            "problem_url": problem_url,
            "verdict": verdict,
            "verdict_raw": str(verdict_raw) if verdict_raw is not None else None,
            "language": item.get("programmingLanguage"),
            "time_ms": int(time_ms) if isinstance(time_ms, (int, float)) else None,
            "memory_kb": (
                int(memory_bytes) // 1024 if isinstance(memory_bytes, (int, float)) else None
            ),
            "submitted_at": datetime.fromtimestamp(int(creation_time), UTC),
            "raw_payload": {
                "testset": item.get("testset"),
                "passedTestCount": item.get("passedTestCount"),
            },
        }
