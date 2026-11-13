from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

SessionMode = Literal["review", "free"]
SelfAssessment = Literal["correct", "partial", "incorrect"]


class SessionCreateRequest(BaseModel):
    task_id: UUID
    mode: SessionMode = "free"


class HintRequest(BaseModel):
    level: int = Field(ge=1, le=5)


class HintUsed(BaseModel):
    level: int
    content: str
    requested_at: datetime


class HintResponse(BaseModel):
    level: int
    content: str
    max_hint_level: int


class AnswerRequest(BaseModel):
    answer_payload: dict[str, object]
    self_assessment: SelfAssessment | None = None
    self_assessment_note: str | None = Field(default=None, max_length=2000)
    error_types: list[str] = Field(default_factory=list)


class CompleteRequest(BaseModel):
    mark_as_review: bool = False


class RunCaseRequest(BaseModel):
    input: str = Field(default="", max_length=20000)
    expected_output: str | None = Field(default=None, max_length=20000)


class RunTestsRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200000)
    cases: list[RunCaseRequest] = Field(min_length=1, max_length=10)


class RunTestsResponse(BaseModel):
    result: str
    passed: int
    total: int
    score: float | None = None
    message: str | None = None
    compile_output: str | None = None
    cases: list[dict[str, object]] = Field(default_factory=list)


class AiReviewRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200000)


class AiReviewResponse(BaseModel):
    verdict: str
    score: int | None = None
    summary: str
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class TaskView(BaseModel):
    id: UUID
    slug: str
    title: str
    training_type: str
    evaluation_mode: str
    difficulty: int
    statement_md: str
    constraints_md: str | None
    input_spec: dict[str, object] | None
    expected_output_spec: dict[str, object] | None
    code_scaffold: str | None
    language: str
    max_hint_level: int
    error_types: list[str]
    target_skills: list[dict[str, object]]
    related_skills: list[dict[str, object]]
    sample_cases: list[dict[str, str]] = Field(default_factory=list)


class SessionResponse(BaseModel):
    id: UUID
    task: TaskView
    training_type: str
    mode: str
    status: str
    started_at: datetime | None
    submitted_at: datetime | None
    completed_at: datetime | None
    time_spent_ms: int | None
    max_hint_level: int
    mark_as_review: bool
    hints_used: list[HintUsed]
    self_assessment: str | None
    auto_grade: dict[str, object] | None


class ResultResponse(SessionResponse):
    self_assessment_note: str | None
    error_types: list[str]
    reference_solution_md: str | None
    next_review_at: datetime | None
