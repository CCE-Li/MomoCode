import logging

from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])
_settings = get_settings()


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(response: Response) -> dict[str, object]:
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        logger.exception("Database readiness check failed")
        checks["database"] = "error"

    redis = Redis.from_url(_settings.redis_url)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        logger.exception("Redis readiness check failed")
        checks["redis"] = "error"
    finally:
        await redis.aclose()

    if any(value != "ok" for value in checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "checks": checks}

    return {"status": "ok", "checks": checks}
