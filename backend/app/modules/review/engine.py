from datetime import UTC, datetime
from importlib.metadata import version
from typing import Protocol

from fsrs import Card, Rating, Scheduler, State

from app.modules.practice.models import PracticeSession

SCHEDULER_VERSION = f"fsrs-{version('fsrs')}"
MAPPING_VERSION = "evidence-map-v1"
CUSTOM_MAPPING_VERSION = "custom-review-v1"


class FSRSCardState(Protocol):
    id: int
    state: int
    step: int | None
    stability: float | None
    difficulty: float | None
    due_at: datetime
    last_review_at: datetime | None


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_scheduler(desired_retention: float = 0.9) -> Scheduler:
    return Scheduler(desired_retention=desired_retention)


def card_from_memory(memory: FSRSCardState) -> Card:
    return Card(
        card_id=int(memory.id),
        state=State(memory.state),
        step=memory.step,
        stability=memory.stability,
        difficulty=memory.difficulty,
        due=ensure_utc(memory.due_at),
        last_review=(
            ensure_utc(memory.last_review_at) if memory.last_review_at is not None else None
        ),
    )


def apply_card(memory: FSRSCardState, card: Card) -> None:
    memory.state = int(card.state)
    memory.step = card.step
    memory.stability = card.stability
    memory.difficulty = card.difficulty
    memory.due_at = ensure_utc(card.due)
    memory.last_review_at = ensure_utc(card.last_review) if card.last_review else None


def evidence_to_rating(session: PracticeSession) -> Rating:
    hint_level = session.max_hint_level
    auto_grade = session.auto_grade or {}
    result = auto_grade.get("result") if isinstance(auto_grade, dict) else None

    if result == "correct":
        if hint_level <= 1:
            return Rating.Easy
        if hint_level <= 3:
            return Rating.Good
        return Rating.Hard
    if result == "partial":
        return Rating.Hard if hint_level <= 3 else Rating.Again
    if result is not None and result != "ungraded":
        return Rating.Again

    if session.self_assessment == "correct":
        if hint_level <= 1:
            return Rating.Easy
        if hint_level <= 3:
            return Rating.Good
        return Rating.Hard
    if session.self_assessment == "partial":
        return Rating.Hard
    return Rating.Again


def evidence_snapshot(session: PracticeSession) -> dict[str, object]:
    return {
        "session_id": str(session.id),
        "task_slug": session.task_snapshot.get("slug"),
        "training_type": session.training_type,
        "mode": session.mode,
        "max_hint_level": session.max_hint_level,
        "self_assessment": session.self_assessment,
        "auto_grade": session.auto_grade,
        "error_types": session.error_types,
        "time_spent_ms": session.time_spent_ms,
        "mark_as_review": session.mark_as_review,
    }
