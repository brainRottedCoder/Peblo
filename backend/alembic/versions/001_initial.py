"""initial schema: shows, seasons, episodes, artwork, publish runs, users

Revision ID: 001_initial
Revises:
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('editor', 'admin')", name="ck_users_role"),
    )
    op.create_table(
        "shows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("synopsis", sa.Text(), nullable=False, server_default=""),
        sa.Column("section", sa.String(64), nullable=True),
        sa.Column("categories", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'published')", name="ck_shows_status"),
    )
    op.create_index("idx_shows_section", "shows", ["section"])
    op.create_index("idx_shows_status", "shows", ["status"])
    op.create_index("idx_shows_title", "shows", ["title"])

    op.create_table(
        "seasons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("show_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("show_id", "number", name="uq_season_show_number"),
    )

    op.create_table(
        "episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("season_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("show_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_id", sa.String(64), unique=True, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("content_group", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'published')", name="ck_episodes_status"),
    )
    op.create_index("idx_episodes_content_group_lang", "episodes", ["content_group", "language"])
    op.create_index("idx_episodes_status", "episodes", ["status"])
    op.create_index("idx_episodes_show_id", "episodes", ["show_id"])
    op.create_index("idx_episodes_title", "episodes", ["title"])

    op.create_table(
        "artwork",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("storage_key", sa.String(512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("show_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shows.id", ondelete="CASCADE"), nullable=True),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('poster', 'banner', 'thumbnail')", name="ck_artwork_kind"),
        sa.CheckConstraint(
            "(show_id IS NOT NULL AND episode_id IS NULL) OR (show_id IS NULL AND episode_id IS NOT NULL)",
            name="ck_artwork_one_owner",
        ),
    )
    op.create_index("idx_artwork_show", "artwork", ["show_id"])
    op.create_index("idx_artwork_episode", "artwork", ["episode_id"])

    op.create_table(
        "publish_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_email", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(32), nullable=False, server_default="started"),
        sa.Column("show_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("episode_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("catalogue_key", sa.String(512), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("notes", postgresql.JSONB(), nullable=True),
        sa.CheckConstraint("outcome IN ('started', 'success', 'failed', 'blocked')", name="ck_publish_outcome"),
    )
    op.create_index("idx_publish_runs_started", "publish_runs", ["started_at"])


def downgrade() -> None:
    op.drop_table("publish_runs")
    op.drop_table("artwork")
    op.drop_table("episodes")
    op.drop_table("seasons")
    op.drop_table("shows")
    op.drop_table("users")
