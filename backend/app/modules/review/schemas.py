from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DueItem(BaseModel):
    kind: Literal["skill", "custom"] = "skill"
    due_at: datetime
    overdue: bool
    skill_id: UUID | None = None
    skill_slug: str | None = None
    skill_name: str | None = None
    algorithm_slug: str | None = None
    algorithm_name: str | None = None
    task_id: UUID | None = None
    task_slug: str | None = None
    task_title: str | None = None
    max_hint_level: int = 0
    custom_item_id: UUID | None = None
    title: str | None = None
    content_preview: str | None = None


class DueQueueResponse(BaseModel):
    items: list[DueItem]
    due_count: int
    daily_limit: int
    timezone: str


class TodayReviewResponse(BaseModel):
    due_count: int
    overdue_count: int
    reviewed_today: int
    timezone: str
    next_due_at: datetime | None


class ReviewHistoryItem(BaseModel):
    kind: Literal["skill", "custom"] = "skill"
    id: UUID
    rating: int
    reviewed_at: datetime
    review_duration_ms: int | None
    skill_slug: str | None = None
    skill_name: str | None = None
    algorithm_name: str | None = None
    custom_item_id: UUID | None = None
    title: str | None = None


class CustomReviewItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content_md: str = Field(min_length=1, max_length=20000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    source_url: str | None = Field(default=None, max_length=2000)


class CustomReviewItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content_md: str | None = Field(default=None, min_length=1, max_length=20000)
    tags: list[str] | None = Field(default=None, max_length=20)
    source_url: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None


class CustomReviewItemResponse(BaseModel):
    id: UUID
    title: str
    content_md: str
    tags: list[str]
    source_url: str | None
    is_active: bool
    due_at: datetime | None
    last_review_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CustomReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=4)
    review_duration_ms: int | None = Field(default=None, ge=0)


class CustomReviewResponse(BaseModel):
    item_id: UUID
    rating: int
    reviewed_at: datetime
    next_due_at: datetime
