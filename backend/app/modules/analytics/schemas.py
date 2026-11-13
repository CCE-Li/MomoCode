from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TrainingTypeMetrics(BaseModel):
    training_type: str
    sessions: int
    correctness_rate: float | None
    independent_rate: float | None
    avg_hint_level: float | None


class OverviewResponse(BaseModel):
    range_days: int
    sample_size: int
    insufficient_data: bool
    sessions_completed: int
    correctness_rate: float | None
    independent_rate: float | None
    hint_dependency: float | None
    avg_normalized_time: float | None
    reviewed_count: int
    due_count: int
    training_types: list[TrainingTypeMetrics]


class TrendPoint(BaseModel):
    date: str
    sessions: int
    correctness_rate: float | None
    independent_rate: float | None


class TrendsResponse(BaseModel):
    range_days: int
    points: list[TrendPoint]


class ErrorDistributionItem(BaseModel):
    error_type: str
    count: int


class SkillStatResponse(BaseModel):
    skill_id: UUID
    skill_slug: str
    skill_name: str
    algorithm_name: str
    sample_size: int
    correctness_rate: float | None
    independence_score: float | None
    hint_dependency: float | None
    avg_normalized_time: float | None
    skill_score: float | None
    insufficient_data: bool
    score_version: str
    computed_at: datetime


class MetricDefinition(BaseModel):
    key: str
    name: str
    formula: str
    source: str
    time_range: str
    notes: str


class GalaxySkillStar(BaseModel):
    skill_id: UUID
    skill_slug: str
    skill_name: str
    algorithm_slug: str
    algorithm_name: str
    category_slug: str
    category_name: str
    skill_type: str
    retrievability: float
    mastery: float
    review_count: int
    star_state: str
    brightness: float
    star_updated_at: datetime | None


class GalaxyResponse(BaseModel):
    total_skills: int
    lit_count: int
    progress: float
    skills: list[GalaxySkillStar]
    computed_at: datetime


class ForgettingCurvePoint(BaseModel):
    day: int
    fibonacci_retention: float
    my_retention: float | None


class ForgettingCurveResponse(BaseModel):
    horizon_days: int
    sample_size: int
    insufficient_data: bool
    avg_stability_days: float | None
    fibonacci_intervals: list[int]
    fibonacci_review_days: list[int]
    points: list[ForgettingCurvePoint]
    notes: str
