from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class ArtworkOut(BaseModel):
    id: uuid.UUID
    kind: str
    url: str
    width: int
    height: int
    byte_size: int


class EpisodeIn(BaseModel):
    title: str
    number: int
    duration_seconds: int | None = None
    language: str
    content_group: str
    status: str = "draft"


class EpisodeUpdate(BaseModel):
    title: str | None = None
    number: int | None = None
    duration_seconds: int | None = None
    language: str | None = None
    content_group: str | None = None
    status: str | None = None


class EpisodeOut(BaseModel):
    id: uuid.UUID
    season_id: uuid.UUID
    show_id: uuid.UUID
    external_id: str | None
    title: str
    number: int
    duration_seconds: int | None
    language: str
    content_group: str
    status: str
    artwork: list[ArtworkOut] = Field(default_factory=list)


class SeasonIn(BaseModel):
    number: int


class SeasonOut(BaseModel):
    id: uuid.UUID
    show_id: uuid.UUID
    number: int
    episode_count: int = 0
    episodes: list[EpisodeOut] = Field(default_factory=list)


class ShowIn(BaseModel):
    title: str
    slug: str
    synopsis: str = ""
    section: str | None = None
    categories: list[str] = Field(default_factory=list)
    status: str = "draft"


class ShowUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    synopsis: str | None = None
    section: str | None = None
    categories: list[str] | None = None
    status: str | None = None


class ShowOut(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    synopsis: str
    section: str | None
    categories: list[str]
    status: str
    episode_count: int = 0
    artwork: list[ArtworkOut] = Field(default_factory=list)


class ShowDetailOut(ShowOut):
    seasons: list[SeasonOut] = Field(default_factory=list)


class ShowListOut(BaseModel):
    items: list[ShowOut]
    total: int
    page: int
    page_size: int


class ValidationIssue(BaseModel):
    severity: str
    code: str
    message: str
    how_to_fix: str
    show_id: uuid.UUID | None = None
    show_title: str | None = None
    episode_id: uuid.UUID | None = None
    episode_title: str | None = None


class ValidationReport(BaseModel):
    can_publish: bool
    blocking: list[ValidationIssue]
    warnings: list[ValidationIssue]
    groups: dict[str, list[ValidationIssue]]


class PublishRunOut(BaseModel):
    id: uuid.UUID
    actor_email: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str
    show_count: int
    episode_count: int
    catalogue_key: str | None
    error: str | None
    notes: dict | None = None
