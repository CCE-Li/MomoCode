# ruff: noqa: S311
"""Seed a demo user with a year of training, review, and OJ evidence.

Usage:
    uv run python -m scripts.seed_demo_user --email 2766503189@qq.com

This is a development helper. It appends fabricated data; run it once on a
test account. It does not delete existing rows or change the password.
"""

from __future__ import annotations

import argparse
import asyncio
import random
from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionFactory
from app.modules.auth.models import User, UserPreference
from app.modules.catalog.models import Algorithm, Skill
from app.modules.oj.models import OJAccount, Submission
from app.modules.practice.models import PracticeSession
from app.modules.review.models import ReviewLog, SkillMemory
from app.modules.task_engine.models import PracticeTask, TaskSkill

DEFAULT_EMAIL = "2766503189@qq.com"
INITIAL_ALGORITHMS = (
    "binary-search",
    "two-pointers",
    "prefix-sum",
    "difference-array",
    "bfs",
    "dfs",
    "dijkstra",
    "union-find",
    "knapsack-01",
    "lis",
)
DEFAULT_ERROR_TYPES = ["边界错误", "初始化错误", "溢出", "越界", "逻辑错误"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed demo training data")
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--seed", type=int, default=20261114)
    return parser.parse_args()


def skill_ref(skill: Skill, algorithm: Algorithm) -> dict[str, str]:
    return {
        "id": str(skill.id),
        "slug": skill.slug,
        "name": skill.name,
        "skill_type": skill.skill_type,
        "algorithm_slug": algorithm.slug,
        "algorithm_name": algorithm.name,
    }


def task_snapshot(entry: dict[str, Any]) -> dict[str, Any]:
    task: PracticeTask = entry["task"]
    return {
        "id": str(task.id),
        "slug": task.slug,
        "title": task.title,
        "training_type": task.training_type,
        "evaluation_mode": task.evaluation_mode,
        "difficulty": task.difficulty,
        "language": task.language,
        "max_hint_level": task.max_hint_level,
        "error_types": task.error_types,
        "statement_md": task.statement_md,
        "constraints_md": task.constraints_md,
        "oj_platform": task.oj_platform,
        "oj_problem_url": task.oj_problem_url,
        "target_skills": [skill_ref(skill, algorithm) for skill, algorithm in entry["skills"]],
        "related_skills": [],
    }


async def load_tasks(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(PracticeTask, Skill, Algorithm)
            .join(TaskSkill, TaskSkill.task_id == PracticeTask.id)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(
                TaskSkill.relation_type == "target",
                PracticeTask.is_active.is_(True),
                Algorithm.slug.in_(INITIAL_ALGORITHMS),
            )
            .order_by(PracticeTask.id, TaskSkill.is_primary.desc())
        )
    ).all()

    grouped: dict[UUID, dict[str, Any]] = {}
    for task, skill, algorithm in rows:
        entry = grouped.setdefault(task.id, {"task": task, "skills": []})
        entry["skills"].append((skill, algorithm))

    by_algorithm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in grouped.values():
        first_skill = entry["skills"][0]
        by_algorithm[first_skill[1].slug].append(entry)

    selected: list[dict[str, Any]] = []
    for slug in INITIAL_ALGORITHMS:
        entries = by_algorithm.get(slug, [])
        entries.sort(key=lambda item: (item["task"].difficulty, item["task"].title))
        by_type: dict[str, dict[str, Any]] = {}
        for entry in entries:
            by_type.setdefault(entry["task"].training_type, entry)
        picked = list(by_type.values())[:2] or entries[:2]
        selected.extend(picked)
    return selected


def build_schedule(days: int, today) -> list[tuple[Any, int]]:
    schedule: list[tuple[Any, int]] = []
    for offset in range(days):
        day = today - timedelta(days=offset)
        weekday = day.weekday()
        chance = 0.5 if weekday < 5 else 0.34
        if offset < 12:
            chance = 0.9
        if random.random() > chance:
            continue
        count = random.choices(
            [1, 2, 3, 4, 5, 6, 8],
            weights=[30, 27, 18, 11, 7, 5, 2],
        )[0]
        schedule.append((day, count))
    if not any(day == today for day, _ in schedule):
        schedule.append((today, 3))
    return schedule


def duration_for(training_type: str) -> int:
    if training_type == "recognition":
        return random.randint(60_000, 240_000)
    if training_type == "template":
        return random.randint(300_000, 1_500_000)
    if training_type == "variant":
        return random.randint(480_000, 1_800_000)
    return random.randint(180_000, 900_000)


def assessment_for(training_type: str) -> str:
    if training_type == "recognition":
        return random.choices(["correct", "incorrect"], weights=[75, 25])[0]
    return random.choices(["correct", "partial", "incorrect"], weights=[66, 22, 12])[0]


def auto_grade_for(
    task: PracticeTask,
    self_assessment: str,
    entry: dict[str, Any],
) -> dict[str, Any] | None:
    if task.evaluation_mode == "auto_recognition":
        result = "correct" if self_assessment == "correct" else "incorrect"
        target_ids = [str(skill.id) for skill, _ in entry["skills"]]
        selected_ids = target_ids if result == "correct" else []
        return {
            "result": result,
            "overlap_score": 1.0 if result == "correct" else 0.0,
            "target_skill_ids": target_ids,
            "selected_skill_ids": selected_ids,
        }
    if task.evaluation_mode == "auto_tests":
        total = 3
        passed = total if self_assessment == "correct" else 1 if self_assessment == "partial" else 0
        return {
            "result": self_assessment,
            "passed": passed,
            "total": total,
            "score": passed / total,
            "cases": [],
        }
    return None


async def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    now = datetime.now(UTC)
    timezone = ZoneInfo("Asia/Shanghai")
    now_local = now.astimezone(timezone)
    today = now_local.date()

    async with SessionFactory() as session:
        user = await session.scalar(select(User).where(User.email == args.email))
        if user is None:
            print(f"user not found: {args.email}")
            return 1

        preference = await session.get(UserPreference, user.id)
        if preference is None:
            preference = UserPreference(user_id=user.id)
            session.add(preference)
        preference.timezone = "Asia/Shanghai"
        preference.daily_review_limit = 50
        preference.desired_retention = Decimal("0.90")
        preference.locale = "zh-CN"
        preference.theme = "dark"

        oj_account = await session.scalar(
            select(OJAccount).where(
                OJAccount.user_id == user.id,
                OJAccount.platform == "codeforces",
            )
        )
        if oj_account is None:
            oj_account = OJAccount(
                user_id=user.id,
                platform="codeforces",
                handle="cceli",
                display_name="cceli",
                last_synced_at=now,
            )
            session.add(oj_account)
            await session.flush()

        selected = await load_tasks(session)
        if not selected:
            print("no seedable tasks found")
            return 1
        snapshot_cache = {entry["task"].id: task_snapshot(entry) for entry in selected}

        schedule = build_schedule(args.days, today)
        created = 0
        formal = 0
        submissions = 0
        submission_index = 0
        today_seen = False

        for day, count in schedule:
            for index in range(count):
                entry = random.choice(selected)
                task: PracticeTask = entry["task"]
                primary_skill, primary_algorithm = entry["skills"][0]
                training_type = task.training_type
                is_today = day == today
                if is_today:
                    today_seen = True

                is_formal = (is_today and index == 0) or random.random() < 0.15
                mode = "review" if is_formal else "free"
                duration = duration_for(training_type)
                self_assessment = assessment_for(training_type)
                max_hint = min(
                    task.max_hint_level,
                    random.choices([0, 1, 2, 3], weights=[50, 24, 16, 10])[0],
                )

                if is_today:
                    created_local = (
                        now_local
                        - timedelta(milliseconds=duration)
                        - timedelta(minutes=random.randint(30, 300))
                    )
                    if created_local.date() != day:
                        created_local = datetime.combine(day, time(0, 5), timezone)
                else:
                    created_local = datetime.combine(
                        day,
                        time(
                            random.randint(8, 21),
                            random.randint(0, 59),
                            random.randint(0, 59),
                        ),
                        timezone,
                    )
                completed_local = created_local + timedelta(milliseconds=duration)
                created_at = created_local.astimezone(UTC)
                completed_at = completed_local.astimezone(UTC)

                auto_grade = auto_grade_for(task, self_assessment, entry)
                error_types = []
                if self_assessment != "correct":
                    pool = task.error_types or DEFAULT_ERROR_TYPES
                    error_types = random.sample(
                        pool,
                        k=min(len(pool), random.randint(1, 2)),
                    )

                answer_payload: dict[str, Any]
                if training_type == "recognition":
                    answer_payload = {
                        "selected_skill_ids": [str(primary_skill.id)]
                        if self_assessment == "correct"
                        else []
                    }
                else:
                    answer_payload = {"code": "// demo solution\n"}

                row = PracticeSession(
                    user_id=user.id,
                    task_id=task.id,
                    task_snapshot=snapshot_cache[task.id],
                    training_type=training_type,
                    mode=mode,
                    status="completed",
                    started_at=created_at,
                    submitted_at=completed_at - timedelta(seconds=15),
                    completed_at=completed_at,
                    time_spent_ms=duration,
                    answer_payload=answer_payload,
                    auto_grade=auto_grade,
                    self_assessment=self_assessment,
                    self_assessment_note=None,
                    max_hint_level=max_hint,
                    error_types=error_types,
                    mark_as_review=is_formal,
                    created_at=created_at,
                    updated_at=completed_at,
                )
                session.add(row)
                await session.flush()
                created += 1

                if is_formal:
                    if self_assessment == "correct":
                        rating = 4 if max_hint <= 1 else 3
                    elif self_assessment == "partial":
                        rating = 2
                    else:
                        rating = 1
                    session.add(
                        ReviewLog(
                            user_id=user.id,
                            skill_id=primary_skill.id,
                            session_id=row.id,
                            rating=rating,
                            reviewed_at=completed_at,
                            review_duration_ms=duration,
                            scheduler_version="demo",
                            mapping_version="demo",
                            evidence_snapshot={
                                "session_id": str(row.id),
                                "task_slug": task.slug,
                                "training_type": training_type,
                                "mode": mode,
                                "max_hint_level": max_hint,
                                "self_assessment": self_assessment,
                                "auto_grade": auto_grade,
                                "error_types": error_types,
                                "time_spent_ms": duration,
                            },
                        )
                    )
                    formal += 1

                if training_type != "recognition" and random.random() < 0.4:
                    submission_index += 1
                    platform = task.oj_platform or "codeforces"
                    if platform not in {"codeforces", "luogu", "atcoder", "other"}:
                        platform = "other"
                    verdict = "accepted" if self_assessment == "correct" else "wrong_answer"
                    session.add(
                        Submission(
                            user_id=user.id,
                            session_id=row.id,
                            oj_account_id=(oj_account.id if platform == "codeforces" else None),
                            platform=platform,
                            external_id=f"demo-{submission_index:05d}",
                            problem_ref=task.oj_problem_ref,
                            problem_url=task.oj_problem_url,
                            verdict=verdict,
                            verdict_raw=verdict.upper(),
                            language="C++17",
                            time_ms=random.randint(20, 800),
                            memory_kb=random.randint(4_000, 60_000),
                            submitted_at=completed_at,
                            source="manual",
                            raw_payload={"seed": "demo"},
                        )
                    )
                    submissions += 1

        if not today_seen:
            print("warning: no sessions scheduled for today")

        unique_skills: dict[UUID, tuple[Skill, Algorithm]] = {}
        for entry in selected:
            skill, algorithm = entry["skills"][0]
            unique_skills[skill.id] = (skill, algorithm)
        ordered_skills = sorted(unique_skills.values(), key=lambda pair: pair[0].slug)

        due_soon = 0
        for index, (skill, _algorithm) in enumerate(ordered_skills):
            if index < 4:
                due_at = now - timedelta(days=random.randint(1, 6))
                last_review = now - timedelta(days=random.randint(6, 18))
                stability = random.uniform(3.0, 7.0)
                due_soon += 1
            elif index < 8:
                due_at = now + timedelta(days=random.randint(1, 6))
                last_review = now - timedelta(days=random.randint(1, 4))
                stability = random.uniform(30.0, 60.0)
            else:
                due_at = now + timedelta(days=random.randint(10, 40))
                last_review = now - timedelta(days=random.randint(2, 12))
                stability = random.uniform(12.0, 35.0)
            session.add(
                SkillMemory(
                    user_id=user.id,
                    skill_id=skill.id,
                    state=2,
                    step=None,
                    stability=stability,
                    difficulty=random.uniform(3.0, 8.0),
                    due_at=due_at,
                    last_review_at=last_review,
                )
            )

        await session.commit()

        print(f"user: {user.email} ({user.id})")
        print(f"timezone: {preference.timezone}")
        print(f"active days: {len(schedule)} / {args.days}")
        print(f"sessions: {created}")
        print(f"formal reviews: {formal}")
        print(f"submissions: {submissions}")
        print(f"skill memories: {len(ordered_skills)} (due/overdue: {due_soon})")
        print("refresh the dashboard to see the heatmap and analytics")
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
