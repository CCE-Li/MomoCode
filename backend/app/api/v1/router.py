from fastapi import APIRouter

from app.api.v1 import health
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.oj.router import router as oj_router
from app.modules.practice.router import router as practice_router
from app.modules.review.router import router as review_router
from app.modules.settings.router import router as settings_router
from app.modules.user_tasks.router import router as user_tasks_router

router = APIRouter()
router.include_router(health.router)
router.include_router(auth_router)
router.include_router(catalog_router)
router.include_router(practice_router)
router.include_router(review_router)
router.include_router(oj_router)
router.include_router(analytics_router)
router.include_router(settings_router)
router.include_router(user_tasks_router)
