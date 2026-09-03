from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (CheckConstraint("role IN ('editor', 'admin')", name="ck_users_role"),)


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    synopsis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    section: Mapped[str | None] = mapped_column(String(64), nullable=True)
    categories: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    seasons: Mapped[list[Season]] = relationship(
        back_populates="show", cascade="all, delete-orphan", order_by="Season.number"
    )
    artwork: Mapped[list[Artwork]] = relationship(
        back_populates="show",
        cascade="all, delete-orphan",
        foreign_keys="Artwork.show_id",
    )

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name="ck_shows_status"),
        Index("idx_shows_section", "section"),
        Index("idx_shows_status", "status"),
        Index("idx_shows_title", "title"),
        Index("idx_shows_status_section", "status", "section"),
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    show_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    show: Mapped[Show] = relationship(back_populates="seasons")
    episodes: Mapped[list[Episode]] = relationship(
        back_populates="season",
        cascade="all, delete-orphan",
        order_by="Episode.number",
    )

    __table_args__ = (UniqueConstraint("show_id", "number", name="uq_season_show_number"),)


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    season_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    show_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    content_group: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    season: Mapped[Season] = relationship(back_populates="episodes")
    show: Mapped[Show] = relationship()
    artwork: Mapped[list[Artwork]] = relationship(
        back_populates="episode",
        cascade="all, delete-orphan",
        foreign_keys="Artwork.episode_id",
    )

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name="ck_episodes_status"),
        # Seed contains one historical duplicate. A table-wide unique index would
        # hide that row. CMS-created episodes (external_id IS NULL) are uniquely
        # indexed; the API + validation report still enforce every row.
        Index("idx_episodes_content_group_lang", "content_group", "language"),
        Index(
            "uq_episodes_content_group_lang_cms",
            "content_group",
            "language",
            unique=True,
            postgresql_where=text("external_id IS NULL"),
        ),
        Index("idx_episodes_status", "status"),
        Index("idx_episodes_show_id", "show_id"),
        Index("idx_episodes_title", "title"),
        Index("idx_episodes_status_show", "status", "show_id"),
    )


class Artwork(Base):
    __tablename__ = "artwork"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False)
    show_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shows.id", ondelete="CASCADE"), nullable=True
    )
    episode_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    show: Mapped[Show | None] = relationship(back_populates="artwork", foreign_keys=[show_id])
    episode: Mapped[Episode | None] = relationship(back_populates="artwork", foreign_keys=[episode_id])

    __table_args__ = (
        CheckConstraint("kind IN ('poster', 'banner', 'thumbnail')", name="ck_artwork_kind"),
        CheckConstraint(
            "(show_id IS NOT NULL AND episode_id IS NULL) OR (show_id IS NULL AND episode_id IS NOT NULL)",
            name="ck_artwork_one_owner",
        ),
        Index("idx_artwork_show", "show_id"),
        Index("idx_artwork_episode", "episode_id"),
        Index(
            "uq_artwork_show_kind",
            "show_id",
            "kind",
            unique=True,
            postgresql_where=text("show_id IS NOT NULL"),
        ),
        Index(
            "uq_artwork_episode_kind",
            "episode_id",
            "kind",
            unique=True,
            postgresql_where=text("episode_id IS NOT NULL"),
        ),
    )


class PublishRun(Base):
    __tablename__ = "publish_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, default="started")
    show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    episode_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    catalogue_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "outcome IN ('started', 'success', 'failed', 'blocked')",
            name="ck_publish_outcome",
        ),
        Index("idx_publish_runs_started", "started_at"),
    )
