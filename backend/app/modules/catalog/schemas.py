from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    description: str | None
    sort_order: int


class SkillRef(BaseModel):
    id: UUID
    slug: str
    name: str
    skill_type: str
    algorithm_slug: str
    algorithm_name: str


class SkillSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    skill_type: str
    algorithm_slug: str
    algorithm_name: str
    learning_objective: str | None


class SkillDetail(SkillSummary):
    description_md: str | None
    mastery_evidence_md: str | None
    common_mistakes_md: str | None
    prerequisites: list[str]


class AlgorithmSummary(BaseModel):
    id: UUID
    slug: str
    name: str
    category_slug: str
    category_name: str
    summary: str | None
    difficulty: int
    skill_count: int


class AlgorithmDetail(AlgorithmSummary):
    description_md: str | None
    prerequisites: list[str]
    skills: list[SkillSummary]


class TaskSummary(BaseModel):
    id: UUID
    slug: str
    title: str
    training_type: str
    evaluation_mode: str
    difficulty: int
    source_type: str
    language: str
    max_hint_level: int
    oj_platform: str | None
    oj_problem_url: str | None
    target_skills: list[SkillRef]
    tags: list[str] = Field(default_factory=list)


class TaskDetail(TaskSummary):
    statement_md: str
    constraints_md: str | None
    input_spec: dict[str, object] | None
    expected_output_spec: dict[str, object] | None
    code_scaffold: str | None
    error_types: list[str]
    related_skills: list[SkillRef]
    sample_cases: list[dict[str, str]] = Field(default_factory=list)


class TagSummary(BaseModel):
    tag: str
    task_count: int
