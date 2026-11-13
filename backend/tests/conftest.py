import os
from pathlib import Path

os.environ["RATE_LIMIT_ENABLED"] = "false"

from collections.abc import AsyncIterator  # noqa: E402

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.modules.analytics import models as analytics_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.oj import models as oj_models  # noqa: F401
from app.modules.practice import models as practice_models  # noqa: F401
from app.modules.review import models as review_models  # noqa: F401
from app.modules.task_engine import models as task_engine_models  # noqa: F401
from scripts.seed_content import (
    load_bundle,
    upsert_algorithm,
    upsert_category,
    upsert_skill,
    upsert_task,
)

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content" / "seed"
LEGACY_CONTENT_DIR = CONTENT_ROOT / "v1"
V2_CONTENT_DIR = CONTENT_ROOT / "v2"


@pytest.fixture(autouse=True)
def stub_code_judge(monkeypatch):
    async def fake_judge(code: str, cases: list[object]) -> dict[str, object]:
        if "WRONG" in code:
            result = "incorrect"
            passed = 0
        elif "PARTIAL" in code:
            result = "partial"
            passed = 1
        else:
            result = "correct"
            passed = len(cases)
        return {
            "result": result,
            "passed": passed,
            "total": len(cases),
            "score": passed / len(cases) if cases else 0.0,
            "cases": [],
        }

    monkeypatch.setattr(
        "app.modules.practice.service.judge_cpp",
        fake_judge,
    )


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


async def _seed_bundle(session: AsyncSession, content_dir: Path) -> AsyncSession:
    bundle = load_bundle(content_dir)

    category_ids = {}
    for category in bundle.categories:
        row = await upsert_category(session, category)
        category_ids[category.slug] = row.id

    algorithm_ids = {}
    for algorithm in bundle.algorithms:
        row = await upsert_algorithm(session, algorithm, category_ids)
        algorithm_ids[algorithm.slug] = row.id

    skill_ids = {}
    for skill in bundle.skills:
        row = await upsert_skill(session, skill, algorithm_ids)
        skill_ids[skill.slug] = row.id

    for task in bundle.tasks:
        await upsert_task(session, task, skill_ids)

    await session.commit()
    return session


@pytest.fixture
async def seeded_db_session(db_session: AsyncSession) -> AsyncSession:
    return await _seed_bundle(db_session, LEGACY_CONTENT_DIR)


@pytest.fixture
async def seeded_v2_db_session(db_session: AsyncSession) -> AsyncSession:
    return await _seed_bundle(db_session, V2_CONTENT_DIR)


def _override_db(session: AsyncSession) -> None:
    async def override_get_db_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db_session] = override_get_db_session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    _override_db(db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_client(seeded_db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    _override_db(seeded_db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_v2_client(seeded_v2_db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    _override_db(seeded_v2_db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
