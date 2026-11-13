import hashlib
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.errors import DomainError

logger = logging.getLogger(__name__)


async def enforce_rate_limit(
    scope: str,
    identity: str,
    *,
    limit: int,
    window_seconds: int,
) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return
    redis = Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=0.2,
        socket_timeout=0.2,
    )
    key = f"ratelimit:{scope}:{hashlib.sha256(identity.encode('utf-8')).hexdigest()}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        if count > limit:
            raise DomainError(
                code="RATE_LIMITED",
                message="尝试次数过多，请稍后再试。",
                status_code=429,
            )
    except RedisError:
        logger.warning("Rate limit backend unavailable; allowing request")
    finally:
        await redis.aclose()
