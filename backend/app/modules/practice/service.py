from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.modules.catalog.models import Algorithm, Skill
from app.modules.judge.llm import judge_with_llm
from app.modules.judge.runner import JudgeCase, judge_cpp
from app.modules.judge.spec import (
    public_expected_output_spec,
    read_judge_config,
    read_sample_cases,
)
from app.modules.practice.models import PracticeSession, SessionHint
from app.modules.practice.schemas import (
    AiReviewRequest,
    AiReviewResponse,
    AnswerRequest,
    CompleteRequest,
    HintResponse,
    HintUsed,
    ResultResponse,
    RunTestsRequest,
    RunTestsResponse,
    SessionResponse,
    TaskView,
)
from app.modules.review.service import get_next_review_at, record_formal_review
from app.modules.task_engine.models import PracticeTask, TaskSkill


def now_utc() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


async def _task_skill_refs(
    session: AsyncSession,
    task_id: UUID,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows = (
        await session.execute(
            select(TaskSkill, Skill, Algorithm)
            .join(Skill, Skill.id == TaskSkill.skill_id)
            .join(Algorithm, Algorithm.id == Skill.algorithm_id)
            .where(TaskSkill.task_id == task_id)
            .order_by(TaskSkill.relation_type, Skill.sort_order, Skill.name)
        )
    ).all()

    target: list[dict[str, object]] = []
    related: list[dict[str, object]] = []
    for link, skill, algorithm in rows:
        item: dict[str, object] = {
            "id": str(skill.id),
            "slug": skill.slug,
            "name": skill.name,
            "skill_type": skill.skill_type,
            "algorithm_slug": algorithm.slug,
            "algorithm_name": algorithm.name,
        }
        if link.relation_type == "target":
            target.append(item)
        else:
            related.append(item)
    return target, related


def _task_snapshot(
    task: PracticeTask,
    target_skills: list[dict[str, object]],
    related_skills: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": str(task.id),
        "slug": task.slug,
        "title": task.title,
        "training_type": task.training_type,
        "evaluation_mode": task.evaluation_mode,
        "difficulty": task.difficulty,
        "statement_md": task.statement_md,
        "constraints_md": task.constraints_md,
        "input_spec": task.input_spec,
        "expected_output_spec": task.expected_output_spec,
        "code_scaffold": task.code_scaffold,
        "reference_solution_md": task.reference_solution_md,
        "language": task.language,
        "hints": task.hints,
        "max_hint_level": task.max_hint_level,
        "error_types": task.error_types,
        "target_skills": target_skills,
        "related_skills": related_skills,
    }


async def _hints_used(session: AsyncSession, session_id: UUID) -> list[HintUsed]:
    rows = (
        await session.scalars(
            select(SessionHint)
            .where(SessionHint.session_id == session_id)
            .order_by(SessionHint.level)
        )
    ).all()
    return [
        HintUsed(
            level=row.level,
            content=str(row.content_snapshot.get("content", "")),
            requested_at=row.requested_at,
        )
        for row in rows
    ]


async def _session_response(
    session: AsyncSession,
    row: PracticeSession,
) -> SessionResponse:
    task_view = TaskView.model_validate(row.task_snapshot)
    task_view.sample_cases = read_sample_cases(row.task_snapshot.get("expected_output_spec"))
    task_view.expected_output_spec = public_expected_output_spec(task_view.expected_output_spec)
    if row.training_type == "recognition" and row.status == "in_progress":
        task_view.target_skills = []
        task_view.related_skills = []
    return SessionResponse(
        id=row.id,
        task=task_view,
        training_type=row.training_type,
        mode=row.mode,
        status=row.status,
        started_at=row.started_at,
        submitted_at=row.submitted_at,
        completed_at=row.completed_at,
        time_spent_ms=row.time_spent_ms,
        max_hint_level=row.max_hint_level,
        mark_as_review=row.mark_as_review,
        hints_used=await _hints_used(session, row.id),
        self_assessment=row.self_assessment,
        auto_grade=row.auto_grade,
    )


async def _result_response(
    session: AsyncSession,
    row: PracticeSession,
    next_review_at: datetime | None = None,
) -> ResultResponse:
    base = await _session_response(session, row)
    return ResultResponse(
        **base.model_dump(),
        self_assessment_note=row.self_assessment_note,
        error_types=row.error_types,
        reference_solution_md=(
            str(row.task_snapshot.get("reference_solution_md"))
            if row.task_snapshot.get("reference_solution_md") is not None
            else None
        ),
        next_review_at=next_review_at,
    )


async def create_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    task_id: UUID,
    mode: str,
) -> SessionResponse:
    task = await session.get(PracticeTask, task_id)
    if (
        task is None
        or not task.is_active
        or (task.source_type == "user" and task.created_by_user_id != user_id)
    ):
        raise DomainError(
            code="TASK_NOT_FOUND",
            message="训练任务不存在。",
            status_code=404,
        )
    if mode not in {"review", "free"}:
        raise DomainError(
            code="INVALID_SESSION_MODE",
            message="训练模式不合法。",
            status_code=422,
        )

    target_skills, related_skills = await _task_skill_refs(session, task.id)
    row = PracticeSession(
        user_id=user_id,
        task_id=task.id,
        task_snapshot=_task_snapshot(task, target_skills, related_skills),
        training_type=task.training_type,
        mode=mode,
        status="in_progress",
        started_at=now_utc(),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return await _session_response(session, row)


async def get_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
) -> PracticeSession:
    row = await session.scalar(
        select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user_id,
        )
    )
    if row is None:
        raise DomainError(
            code="SESSION_NOT_FOUND",
            message="训练会话不存在。",
            status_code=404,
        )
    return row


async def get_session_response(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
) -> SessionResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    return await _session_response(session, row)


async def request_hint(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
    level: int,
) -> HintResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.status != "in_progress":
        raise DomainError(
            code="SESSION_STATE_CONFLICT",
            message="当前会话状态不允许申请提示。",
            status_code=409,
        )

    max_level_raw = row.task_snapshot.get("max_hint_level", 0)
    max_level = max_level_raw if isinstance(max_level_raw, int) else 0
    if level > max_level:
        raise DomainError(
            code="HINT_NOT_AVAILABLE",
            message="该提示等级不可用。",
            status_code=404,
        )

    hints = row.task_snapshot.get("hints", {})
    content = hints.get(str(level)) if isinstance(hints, dict) else None
    if not isinstance(content, str):
        raise DomainError(
            code="HINT_NOT_AVAILABLE",
            message="该提示等级不可用。",
            status_code=404,
        )

    existing = await session.scalar(
        select(SessionHint).where(
            SessionHint.session_id == row.id,
            SessionHint.level == level,
        )
    )
    if existing is not None:
        return HintResponse(
            level=level,
            content=str(existing.content_snapshot.get("content", content)),
            max_hint_level=row.max_hint_level,
        )

    session.add(
        SessionHint(
            session_id=row.id,
            level=level,
            content_snapshot={"level": level, "content": content},
        )
    )
    row.max_hint_level = max(row.max_hint_level, level)
    await session.commit()
    return HintResponse(
        level=level,
        content=content,
        max_hint_level=row.max_hint_level,
    )


def _selected_skill_ids(payload: dict[str, object]) -> set[str]:
    raw = payload.get("selected_skill_ids", [])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise DomainError(
            code="INVALID_ANSWER",
            message="识别答案格式不正确。",
            status_code=422,
        )
    return set(raw)


def _judge_cases(snapshot: dict[str, object]) -> tuple[list[JudgeCase], str | None]:
    return read_judge_config(snapshot.get("expected_output_spec"))


def _judge_program(code: str, harness_main: str | None) -> str:
    if harness_main and "int main" not in code:
        return "#include <bits/stdc++.h>\nusing namespace std;\n\n" + code + "\n\n" + harness_main
    return code


async def run_tests(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
    payload: RunTestsRequest,
) -> RunTestsResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.training_type == "recognition":
        raise DomainError(
            code="RUN_NOT_SUPPORTED",
            message="识别任务不支持代码运行测试。",
            status_code=422,
        )

    _, harness_main = _judge_cases(row.task_snapshot)
    cases = [
        JudgeCase(
            input=item.input,
            expected_output=item.expected_output if item.expected_output else None,
        )
        for item in payload.cases
    ]
    result = await judge_cpp(_judge_program(payload.code, harness_main), cases)
    return RunTestsResponse.model_validate(result)


async def ai_review(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
    payload: AiReviewRequest,
) -> AiReviewResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.training_type == "recognition":
        raise DomainError(
            code="AI_REVIEW_NOT_SUPPORTED",
            message="识别任务不使用 AI 判题。",
            status_code=422,
        )

    snapshot = row.task_snapshot
    reference = snapshot.get("reference_solution_md")
    result = await judge_with_llm(
        title=str(snapshot.get("title", "")),
        statement_md=str(snapshot.get("statement_md", "")),
        constraints_md=(
            str(snapshot["constraints_md"]) if snapshot.get("constraints_md") is not None else None
        ),
        reference_solution=reference if isinstance(reference, str) else None,
        language=str(snapshot.get("language", "cpp17")),
        code=payload.code,
    )
    return AiReviewResponse.model_validate(result)


async def submit_answer(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
    payload: AnswerRequest,
) -> SessionResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.status != "in_progress":
        raise DomainError(
            code="SESSION_STATE_CONFLICT",
            message="当前会话状态不允许提交答案。",
            status_code=409,
        )

    if row.training_type == "recognition":
        selected = _selected_skill_ids(payload.answer_payload)
        target_items = row.task_snapshot.get("target_skills", [])
        if not isinstance(target_items, list):
            target_items = []
        target = {
            str(item.get("id"))
            for item in target_items
            if isinstance(item, dict) and item.get("id") is not None
        }
        intersection = selected & target
        union = selected | target
        if selected == target and target:
            result = "correct"
            score = 1.0
        elif intersection:
            result = "partial"
            score = len(intersection) / len(union) if union else 0.0
        else:
            result = "incorrect"
            score = 0.0
        row.auto_grade = {
            "result": result,
            "overlap_score": score,
            "target_skill_ids": sorted(target),
            "selected_skill_ids": sorted(selected),
        }
    else:
        code = payload.answer_payload.get("code")
        if not isinstance(code, str) or not code.strip():
            raise DomainError(
                code="INVALID_ANSWER",
                message="代码不能为空。",
                status_code=422,
            )
        cases, harness_main = _judge_cases(row.task_snapshot)
        if cases:
            judge_code = _judge_program(code, harness_main)
            row.auto_grade = await judge_cpp(judge_code, cases)
        else:
            if payload.self_assessment is None:
                raise DomainError(
                    code="SELF_ASSESSMENT_REQUIRED",
                    message="该任务没有自动判题用例，请先完成自评。",
                    status_code=422,
                )
            row.auto_grade = None
            row.self_assessment = payload.self_assessment
            row.self_assessment_note = payload.self_assessment_note
        row.error_types = payload.error_types

    row.answer_payload = payload.answer_payload
    row.status = "submitted"
    row.submitted_at = now_utc()
    await session.commit()
    await session.refresh(row)
    return await _session_response(session, row)


async def complete_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
    payload: CompleteRequest,
) -> ResultResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.status == "completed":
        return await _result_response(
            session,
            row,
            await get_next_review_at(session, row.id),
        )
    if row.status != "submitted":
        raise DomainError(
            code="SESSION_STATE_CONFLICT",
            message="请先提交答案，再完成会话。",
            status_code=409,
        )

    completed_at = now_utc()
    row.completed_at = completed_at
    row.status = "completed"
    row.mark_as_review = payload.mark_as_review or row.mode == "review"
    if row.started_at is not None:
        row.time_spent_ms = max(
            0,
            int((completed_at - _as_utc(row.started_at)).total_seconds() * 1000),
        )

    next_review_at: datetime | None = None
    if row.mark_as_review:
        next_review_at = await record_formal_review(session, row)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        row = await get_session(session, user_id=user_id, session_id=session_id)
        next_review_at = await get_next_review_at(session, row.id)

    await session.refresh(row)
    return await _result_response(session, row, next_review_at)


async def get_result(
    session: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID,
) -> ResultResponse:
    row = await get_session(session, user_id=user_id, session_id=session_id)
    if row.status != "completed":
        raise DomainError(
            code="SESSION_NOT_COMPLETED",
            message="会话尚未完成。",
            status_code=409,
        )
    return await _result_response(
        session,
        row,
        await get_next_review_at(session, row.id),
    )
