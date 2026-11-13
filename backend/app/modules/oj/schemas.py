from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OJPlatform = Literal["codeforces", "luogu", "atcoder", "other"]
OJVerdict = Literal[
    "accepted",
    "wrong_answer",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "runtime_error",
    "compilation_error",
    "partially_accepted",
    "other",
]


class OJAccountCreate(BaseModel):
    platform: OJPlatform
    handle: str = Field(min_length=1, max_length=120)
    display_name: str | None = Field(default=None, max_length=120)


class OJAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    handle: str
    display_name: str | None
    is_active: bool
    last_synced_at: datetime | None
    created_at: datetime


class SyncResult(BaseModel):
    fetched: int
    created: int
    skipped: int
    last_synced_at: datetime


class ManualSubmissionCreate(BaseModel):
    platform: OJPlatform
    external_id: str = Field(min_length=1, max_length=200)
    problem_ref: str | None = Field(default=None, max_length=200)
    problem_url: str | None = None
    verdict: OJVerdict | None = None
    verdict_raw: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=64)
    time_ms: int | None = Field(default=None, ge=0)
    memory_kb: int | None = Field(default=None, ge=0)
    submitted_at: datetime | None = None
    oj_account_id: UUID | None = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID | None
    platform: str
    external_id: str | None
    problem_ref: str | None
    problem_url: str | None
    verdict: str | None
    verdict_raw: str | None
    language: str | None
    time_ms: int | None
    memory_kb: int | None
    submitted_at: datetime | None
    source: str
    created_at: datetime


class ManualSubmissionResult(BaseModel):
    submission: SubmissionResponse
    duplicate: bool


class LinkSubmissionRequest(BaseModel):
    submission_id: UUID
