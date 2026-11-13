from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.tags import normalize_tags
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.catalog.models import Algorithm, AlgorithmCategory, ContentVersion, Skill
from app.modules.task_engine.models import PracticeTask, TaskSkill, TaskTag

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTENT_DIR = REPO_ROOT / "content" / "seed" / "v2"

SkillType = Literal["recognition", "base_implementation", "variant", "common_error"]
TrainingType = Literal["recognition", "template", "variant", "correction"]
EvaluationMode = Literal["auto_recognition", "self_assessment", "auto_tests"]
SourceType = Literal["original", "oj_reference", "user"]
OJPlatform = Literal["codeforces", "luogu", "atcoder", "other"]


class Manifest(BaseModel):
    version: str = Field(min_length=1)
    description: str
    files: list[str] = Field(min_length=1)


class CategorySeed(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    sort_order: int = 0


class AlgorithmSeed(BaseModel):
    slug: str = Field(min_length=1)
    category_slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    summary: str | None = None
    description_md: str | None = None
    difficulty: int = Field(ge=1, le=5)
    prerequisites: list[str] = Field(default_factory=list)


class SkillSeed(BaseModel):
    slug: str = Field(min_length=1)
    algorithm_slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    skill_type: SkillType
    description_md: str | None = None
    learning_objective: str | None = None
    mastery_evidence_md: str | None = None
    common_mistakes_md: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    sort_order: int = 0


class TaskSeed(BaseModel):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    training_type: TrainingType
    evaluation_mode: EvaluationMode
    difficulty: int = Field(ge=1, le=5)
    source_type: SourceType = "original"
    source_ref: str | None = None
    oj_platform: OJPlatform | None = None
    oj_problem_ref: str | None = None
    oj_problem_url: str | None = None
    statement_md: str = Field(min_length=1)
    constraints_md: str | None = None
    input_spec: dict[str, object] | None = None
    expected_output_spec: dict[str, object] | None = None
    code_scaffold: str | None = None
    reference_solution_md: str | None = None
    language: str = "cpp17"
    hints: dict[str, str] = Field(default_factory=dict)
    max_hint_level: int = Field(ge=0, le=5)
    error_types: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(min_length=1)
    related_skills: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_task(self) -> TaskSeed:
        allowed_hint_keys = {str(level) for level in range(1, self.max_hint_level + 1)}
        invalid_hints = set(self.hints) - allowed_hint_keys
        if invalid_hints:
            raise ValueError(f"{self.slug}: hints contain levels outside 1..{self.max_hint_level}")

        if self.training_type == "recognition":
            if self.evaluation_mode != "auto_recognition":
                raise ValueError(f"{self.slug}: recognition tasks must use auto_recognition")
            if self.max_hint_level > 3:
                raise ValueError(f"{self.slug}: recognition tasks may only use hints 0..3")
        else:
            if self.evaluation_mode not in {"self_assessment", "auto_tests"}:
                raise ValueError(
                    f"{self.slug}: coding tasks must use self_assessment or auto_tests"
                )
            if self.evaluation_mode == "auto_tests":
                judge = (self.expected_output_spec or {}).get("judge")
                if not isinstance(judge, dict) or not judge.get("test_cases"):
                    raise ValueError(f"{self.slug}: auto_tests requires judge test_cases")

        if (self.oj_platform is None) != (self.oj_problem_ref is None):
            raise ValueError(
                f"{self.slug}: oj_platform and oj_problem_ref must both be set or null"
            )
        if self.oj_problem_url is not None and self.oj_platform is None:
            raise ValueError(f"{self.slug}: oj_problem_url requires oj_platform")

        if len(set(self.target_skills)) != len(self.target_skills):
            raise ValueError(f"{self.slug}: target_skills must be unique")
        overlap = set(self.target_skills) & set(self.related_skills)
        if overlap:
            raise ValueError(f"{self.slug}: target_skills and related_skills overlap: {overlap}")

        return self


class SeedBundle(BaseModel):
    manifest: Manifest
    categories: list[CategorySeed]
    algorithms: list[AlgorithmSeed]
    skills: list[SkillSeed]
    tasks: list[TaskSeed]

    @model_validator(mode="after")
    def validate_bundle(self) -> SeedBundle:
        category_slugs = {item.slug for item in self.categories}
        if len(category_slugs) != len(self.categories):
            raise ValueError("duplicate category slug")

        algorithm_slugs = {item.slug for item in self.algorithms}
        if len(algorithm_slugs) != len(self.algorithms):
            raise ValueError("duplicate algorithm slug")
        for algorithm in self.algorithms:
            if algorithm.category_slug not in category_slugs:
                raise ValueError(f"{algorithm.slug}: unknown category {algorithm.category_slug}")

        skill_slugs = {item.slug for item in self.skills}
        if len(skill_slugs) != len(self.skills):
            raise ValueError("duplicate skill slug")
        for skill in self.skills:
            if skill.algorithm_slug not in algorithm_slugs:
                raise ValueError(f"{skill.slug}: unknown algorithm {skill.algorithm_slug}")

        task_slugs = {item.slug for item in self.tasks}
        if len(task_slugs) != len(self.tasks):
            raise ValueError("duplicate task slug")
        for task in self.tasks:
            references = set(task.target_skills) | set(task.related_skills)
            unknown = references - skill_slugs
            if unknown:
                raise ValueError(f"{task.slug}: unknown skills {sorted(unknown)}")

        return self


def load_json_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def load_json_list(path: Path) -> list[object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array")
    return data


def load_bundle(content_dir: Path) -> SeedBundle:
    manifest = Manifest.model_validate(load_json_object(content_dir / "manifest.json"))
    categories = [
        CategorySeed.model_validate(item)
        for item in load_json_list(content_dir / "categories.json")
    ]
    algorithms = [
        AlgorithmSeed.model_validate(item)
        for item in load_json_list(content_dir / "algorithms.json")
    ]
    skills = [
        SkillSeed.model_validate(item) for item in load_json_list(content_dir / "skills.json")
    ]
    tasks = [TaskSeed.model_validate(item) for item in load_json_list(content_dir / "tasks.json")]
    return SeedBundle(
        manifest=manifest,
        categories=categories,
        algorithms=algorithms,
        skills=skills,
        tasks=tasks,
    )


def compute_checksum(content_dir: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update((content_dir / name).read_bytes())
    return digest.hexdigest()


async def upsert_category(
    session: AsyncSession,
    seed: CategorySeed,
) -> AlgorithmCategory:
    row = await session.scalar(select(AlgorithmCategory).where(AlgorithmCategory.slug == seed.slug))
    if row is None:
        row = AlgorithmCategory(slug=seed.slug)
        session.add(row)
    row.name = seed.name
    row.description = seed.description
    row.sort_order = seed.sort_order
    row.is_active = True
    await session.flush()
    return row


async def upsert_algorithm(
    session: AsyncSession,
    seed: AlgorithmSeed,
    category_ids: dict[str, UUID],
) -> Algorithm:
    row = await session.scalar(select(Algorithm).where(Algorithm.slug == seed.slug))
    if row is None:
        row = Algorithm(slug=seed.slug)
        session.add(row)
    row.category_id = category_ids[seed.category_slug]
    row.name = seed.name
    row.summary = seed.summary
    row.description_md = seed.description_md
    row.difficulty = seed.difficulty
    row.prerequisites = seed.prerequisites
    row.is_active = True
    await session.flush()
    return row


async def upsert_skill(
    session: AsyncSession,
    seed: SkillSeed,
    algorithm_ids: dict[str, UUID],
) -> Skill:
    row = await session.scalar(select(Skill).where(Skill.slug == seed.slug))
    if row is None:
        row = Skill(slug=seed.slug)
        session.add(row)
    row.algorithm_id = algorithm_ids[seed.algorithm_slug]
    row.name = seed.name
    row.skill_type = seed.skill_type
    row.description_md = seed.description_md
    row.learning_objective = seed.learning_objective
    row.mastery_evidence_md = seed.mastery_evidence_md
    row.common_mistakes_md = seed.common_mistakes_md
    row.prerequisites = seed.prerequisites
    row.sort_order = seed.sort_order
    row.is_active = True
    await session.flush()
    return row


async def upsert_task(
    session: AsyncSession,
    seed: TaskSeed,
    skill_ids: dict[str, UUID],
) -> PracticeTask:
    row = await session.scalar(select(PracticeTask).where(PracticeTask.slug == seed.slug))
    if row is None:
        row = PracticeTask(slug=seed.slug)
        session.add(row)
    row.title = seed.title
    row.training_type = seed.training_type
    row.evaluation_mode = seed.evaluation_mode
    row.difficulty = seed.difficulty
    row.source_type = seed.source_type
    row.source_ref = seed.source_ref
    row.oj_platform = seed.oj_platform
    row.oj_problem_ref = seed.oj_problem_ref
    row.oj_problem_url = seed.oj_problem_url
    row.statement_md = seed.statement_md
    row.constraints_md = seed.constraints_md
    row.input_spec = seed.input_spec
    row.expected_output_spec = seed.expected_output_spec
    row.code_scaffold = seed.code_scaffold
    row.reference_solution_md = seed.reference_solution_md
    row.language = seed.language
    row.hints = seed.hints
    row.max_hint_level = seed.max_hint_level
    row.error_types = seed.error_types
    row.is_active = True
    await session.flush()

    await session.execute(delete(TaskSkill).where(TaskSkill.task_id == row.id))
    await session.execute(delete(TaskTag).where(TaskTag.task_id == row.id))
    for tag in normalize_tags(seed.tags):
        session.add(TaskTag(task_id=row.id, tag=tag))
    for index, skill_slug in enumerate(seed.target_skills):
        session.add(
            TaskSkill(
                task_id=row.id,
                skill_id=skill_ids[skill_slug],
                relation_type="target",
                is_primary=index == 0,
            )
        )
    for skill_slug in seed.related_skills:
        session.add(
            TaskSkill(
                task_id=row.id,
                skill_id=skill_ids[skill_slug],
                relation_type="related",
                is_primary=False,
            )
        )
    await session.flush()
    return row


async def seed(content_dir: Path, force: bool) -> None:
    bundle = load_bundle(content_dir)
    checksum = compute_checksum(content_dir, bundle.manifest.files)

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            existing = await session.scalar(
                select(ContentVersion).where(ContentVersion.version == bundle.manifest.version)
            )
            if existing is not None and existing.checksum == checksum and not force:
                print(
                    f"Content {bundle.manifest.version} is already applied "
                    f"({checksum[:12]}); use --force to reapply."
                )
                return

            category_ids: dict[str, UUID] = {}
            for category in bundle.categories:
                row = await upsert_category(session, category)
                category_ids[category.slug] = row.id

            algorithm_ids: dict[str, UUID] = {}
            for algorithm in bundle.algorithms:
                row = await upsert_algorithm(session, algorithm, category_ids)
                algorithm_ids[algorithm.slug] = row.id

            skill_ids: dict[str, UUID] = {}
            for skill in bundle.skills:
                row = await upsert_skill(session, skill, algorithm_ids)
                skill_ids[skill.slug] = row.id

            for task in bundle.tasks:
                await upsert_task(session, task, skill_ids)

            version_row = existing
            if version_row is None:
                version_row = ContentVersion(version=bundle.manifest.version)
                session.add(version_row)
            version_row.checksum = checksum
            version_row.notes = bundle.manifest.description
            version_row.applied_at = datetime.now(UTC)
            version_row.applied_by = "scripts.seed_content"

            await session.commit()

        print(
            f"Seeded {len(bundle.categories)} categories, "
            f"{len(bundle.algorithms)} algorithms, "
            f"{len(bundle.skills)} skills, "
            f"{len(bundle.tasks)} tasks "
            f"(version {bundle.manifest.version}, {checksum[:12]})."
        )
    finally:
        await engine.dispose()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import MomoCode algorithm seed content.")
    parser.add_argument(
        "--content-dir",
        type=Path,
        default=DEFAULT_CONTENT_DIR,
        help=f"Seed content directory (default: {DEFAULT_CONTENT_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reapply content even if the same version/checksum is already recorded.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(seed(args.content_dir, args.force))


if __name__ == "__main__":
    main()
