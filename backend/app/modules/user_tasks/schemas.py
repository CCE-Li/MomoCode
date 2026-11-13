from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.modules.catalog.schemas import TaskSummary

TrainingType = Literal["recognition", "template", "variant", "correction"]
EvaluationMode = Literal["auto_recognition", "self_assessment", "auto_tests"]
OJPlatform = Literal["codeforces", "luogu", "atcoder", "other"]


class UserTaskInput(BaseModel):
    """Same import contract as the seed task format, minus slug/source_type."""

    title: str = Field(min_length=1, max_length=200)
    training_type: TrainingType = "variant"
    evaluation_mode: EvaluationMode = "self_assessment"
    difficulty: int = Field(default=3, ge=1, le=5)
    source_ref: str | None = Field(default=None, max_length=500)
    oj_platform: OJPlatform | None = None
    oj_problem_ref: str | None = Field(default=None, max_length=200)
    oj_problem_url: str | None = Field(default=None, max_length=2000)
    statement_md: str = Field(min_length=1, max_length=20000)
    constraints_md: str | None = Field(default=None, max_length=5000)
    input_spec: dict[str, object] | None = None
    expected_output_spec: dict[str, object] | None = None
    code_scaffold: str | None = Field(default=None, max_length=200000)
    reference_solution_md: str | None = Field(default=None, max_length=200000)
    language: str = Field(default="cpp17", max_length=32)
    hints: dict[str, str] = Field(default_factory=dict, max_length=5)
    max_hint_level: int = Field(default=3, ge=0, le=5)
    error_types: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=12)
    target_skills: list[str] = Field(min_length=1, max_length=10)
    related_skills: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_task(self) -> "UserTaskInput":
        allowed_hint_keys = {str(level) for level in range(1, self.max_hint_level + 1)}
        invalid_hints = set(self.hints) - allowed_hint_keys
        if invalid_hints:
            raise ValueError(
                f"hints contain levels outside 1..{self.max_hint_level}: {invalid_hints}"
            )

        if self.training_type == "recognition":
            if self.evaluation_mode != "auto_recognition":
                raise ValueError("recognition tasks must use auto_recognition")
            if self.max_hint_level > 3:
                raise ValueError("recognition tasks may only use hints 0..3")
        else:
            if self.evaluation_mode not in {"self_assessment", "auto_tests"}:
                raise ValueError("coding tasks must use self_assessment or auto_tests")
            if self.evaluation_mode == "auto_tests":
                judge = (self.expected_output_spec or {}).get("judge")
                if not isinstance(judge, dict) or not judge.get("test_cases"):
                    raise ValueError("auto_tests requires judge test_cases")

        if (self.oj_platform is None) != (self.oj_problem_ref is None):
            raise ValueError("oj_platform and oj_problem_ref must both be set or null")
        if self.oj_problem_url is not None and self.oj_platform is None:
            raise ValueError("oj_problem_url requires oj_platform")
        if self.oj_problem_url and not self.oj_problem_url.startswith(("http://", "https://")):
            raise ValueError("oj_problem_url must be http/https")

        if len(set(self.target_skills)) != len(self.target_skills):
            raise ValueError("target_skills must be unique")
        overlap = set(self.target_skills) & set(self.related_skills)
        if overlap:
            raise ValueError(f"target_skills and related_skills overlap: {overlap}")
        for slug in [*self.target_skills, *self.related_skills]:
            if not slug or len(slug) > 120:
                raise ValueError("skill slugs must be 1..120 characters")
        if self.language != "cpp17":
            raise ValueError("MVP only supports cpp17")
        return self


class UserTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    training_type: TrainingType | None = None
    evaluation_mode: EvaluationMode | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    source_ref: str | None = Field(default=None, max_length=500)
    oj_platform: OJPlatform | None = None
    oj_problem_ref: str | None = Field(default=None, max_length=200)
    oj_problem_url: str | None = Field(default=None, max_length=2000)
    statement_md: str | None = Field(default=None, min_length=1, max_length=20000)
    constraints_md: str | None = Field(default=None, max_length=5000)
    input_spec: dict[str, object] | None = None
    expected_output_spec: dict[str, object] | None = None
    code_scaffold: str | None = Field(default=None, max_length=200000)
    reference_solution_md: str | None = Field(default=None, max_length=200000)
    language: str | None = Field(default=None, max_length=32)
    hints: dict[str, str] | None = Field(default=None, max_length=5)
    max_hint_level: int | None = Field(default=None, ge=0, le=5)
    error_types: list[str] | None = Field(default=None, max_length=20)
    tags: list[str] | None = Field(default=None, max_length=12)
    target_skills: list[str] | None = Field(default=None, min_length=1, max_length=10)
    related_skills: list[str] | None = Field(default=None, max_length=10)


class UserTaskImportRequest(BaseModel):
    tasks: list[UserTaskInput] = Field(min_length=1, max_length=50)


class UserTaskImportResult(BaseModel):
    created: list[TaskSummary]
    total: int
