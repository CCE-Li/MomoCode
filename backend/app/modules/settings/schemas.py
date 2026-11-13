from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timezone: str
    daily_review_limit: int
    desired_retention: float
    theme: str
    locale: str


class PreferencesUpdate(BaseModel):
    timezone: str | None = Field(default=None, max_length=64)
    daily_review_limit: int | None = Field(default=None, ge=1, le=500)
    desired_retention: float | None = Field(default=None, ge=0.7, le=0.99)
    theme: Literal["dark", "light", "system"] | None = None
    locale: str | None = Field(default=None, max_length=16)


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None
    status: str


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
