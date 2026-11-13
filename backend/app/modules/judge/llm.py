from __future__ import annotations

import json
import logging
from typing import Literal

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()

Verdict = Literal["correct", "partial", "incorrect", "unavailable"]

SYSTEM_PROMPT = """你是一名严格的算法竞赛教练，负责判题。
只能依据给出的题面、约束和参考实现判断；不要臆造未给出的信息。
必须只输出 JSON，字段：
{
  "verdict": "correct" | "partial" | "incorrect",
  "score": 0-100 的整数,
  "summary": "一句话结论（中文）",
  "issues": ["最多 3 条具体问题（中文），没有则为空数组"],
  "suggestions": ["最多 3 条改进建议（中文），没有则为空数组"]
}
判分标准：
- correct：逻辑等价于参考实现，边界、复杂度可接受。
- partial：思路正确但有边界/复杂度/实现缺陷。
- incorrect：逻辑错误或未实现目标。
如果代码只有 TODO 或明显未完成，判 incorrect。"""


def _build_user_prompt(
    *,
    title: str,
    statement_md: str,
    constraints_md: str | None,
    reference_solution: str | None,
    language: str,
    code: str,
) -> str:
    parts = [
        f"任务标题：{title}",
        f"题面：\n{statement_md}",
    ]
    if constraints_md:
        parts.append(f"约束：\n{constraints_md}")
    if reference_solution:
        parts.append(f"参考实现（不要直接抄给用户）：\n```\n{reference_solution}\n```")
    parts.append(f"语言：{language}")
    parts.append(f"用户代码：\n```\n{code}\n```")
    return "\n\n".join(parts)


def _fallback(reason: str) -> dict[str, object]:
    return {
        "verdict": "unavailable",
        "score": None,
        "summary": reason,
        "issues": [],
        "suggestions": [],
    }


async def judge_with_llm(
    *,
    title: str,
    statement_md: str,
    constraints_md: str | None,
    reference_solution: str | None,
    language: str,
    code: str,
) -> dict[str, object]:
    if not _settings.llm_api_key:
        return _fallback("未配置 LLM_API_KEY，AI 判题不可用。")

    payload = {
        "model": _settings.llm_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    title=title,
                    statement_md=statement_md,
                    constraints_md=constraints_md,
                    reference_solution=reference_solution,
                    language=language,
                    code=code,
                ),
            },
        ],
    }

    url = f"{_settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {_settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_settings.llm_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("LLM judge failed: %s", exc)
        return _fallback(f"AI 判题请求失败（HTTP {exc.response.status_code}）。")
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("LLM judge error: %s", exc)
        return _fallback("AI 判题请求失败，请稍后重试。")

    try:
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        logger.warning("LLM judge returned unexpected payload")
        return _fallback("AI 判题返回格式异常。")

    verdict = parsed.get("verdict")
    if verdict not in {"correct", "partial", "incorrect"}:
        return _fallback("AI 判题未返回有效结论。")

    score = parsed.get("score")
    if not isinstance(score, int):
        score = None

    def _string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str)][:3]

    summary = parsed.get("summary")
    return {
        "verdict": verdict,
        "score": max(0, min(100, score)) if score is not None else None,
        "summary": summary if isinstance(summary, str) else "",
        "issues": _string_list(parsed.get("issues")),
        "suggestions": _string_list(parsed.get("suggestions")),
    }
