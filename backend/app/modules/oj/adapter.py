import re
from typing import Protocol
from urllib.parse import urlparse

from app.core.errors import DomainError

ALLOWED_DOMAINS = {
    "codeforces.com": "codeforces",
    "luogu.com.cn": "luogu",
    "atcoder.jp": "atcoder",
}

VERDICT_MAP = {
    "accepted": "accepted",
    "ac": "accepted",
    "ok": "accepted",
    "wrong answer": "wrong_answer",
    "wrong_answer": "wrong_answer",
    "wa": "wrong_answer",
    "time limit exceeded": "time_limit_exceeded",
    "time_limit_exceeded": "time_limit_exceeded",
    "tle": "time_limit_exceeded",
    "memory limit exceeded": "memory_limit_exceeded",
    "memory_limit_exceeded": "memory_limit_exceeded",
    "mle": "memory_limit_exceeded",
    "runtime error": "runtime_error",
    "runtime_error": "runtime_error",
    "re": "runtime_error",
    "compilation error": "compilation_error",
    "compilation_error": "compilation_error",
    "ce": "compilation_error",
    "partially accepted": "partially_accepted",
    "partially_accepted": "partially_accepted",
    "pa": "partially_accepted",
    "other": "other",
}

_EXTERNAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:\-]{1,200}$")


class OJAdapter(Protocol):
    platform: str

    def normalize_verdict(self, raw_verdict: str | None) -> str | None:
        """Map a platform verdict to a canonical value; unknown returns None."""

    def validate_external_id(self, external_id: str) -> str:
        """Validate and return a normalized external submission id."""

    def validate_problem_url(self, problem_url: str) -> str:
        """Validate a problem URL against the platform allowlist."""


class ManualOJAdapter:
    platform = "manual"

    def normalize_verdict(self, raw_verdict: str | None) -> str | None:
        if raw_verdict is None:
            return None
        normalized = raw_verdict.strip().lower()
        if not normalized:
            return None
        return VERDICT_MAP.get(normalized)

    def validate_external_id(self, external_id: str) -> str:
        candidate = external_id.strip()
        if not _EXTERNAL_ID_PATTERN.fullmatch(candidate):
            raise DomainError(
                code="OJ_EXTERNAL_ID_INVALID",
                message="提交 ID 格式不合法。",
                status_code=422,
            )
        return candidate

    def validate_problem_url(self, problem_url: str) -> str:
        parsed = urlparse(problem_url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise DomainError(
                code="OJ_URL_INVALID",
                message="题目链接必须是合法的 http(s) URL。",
                status_code=422,
            )
        host = parsed.hostname.lower()
        if not any(host == domain or host.endswith(f".{domain}") for domain in ALLOWED_DOMAINS):
            raise DomainError(
                code="OJ_URL_INVALID",
                message="题目链接域名不在允许列表中。",
                status_code=422,
            )
        return problem_url.strip()


def get_adapter(platform: str) -> ManualOJAdapter:
    if platform not in {"codeforces", "luogu", "atcoder", "other"}:
        raise DomainError(
            code="OJ_PLATFORM_INVALID",
            message="不支持的 OJ 平台。",
            status_code=422,
        )
    return ManualOJAdapter()
