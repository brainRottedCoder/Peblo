"""Unique artwork slots, CMS content-group uniqueness, query indexes.

Revision ID: 002_uniques
Revises: 001_initial
Create Date: 2026-09-03
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002_uniques"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_shows_status_section", "shows", ["status", "section"])
    op.create_index("idx_episodes_status_show", "episodes", ["status", "show_id"])
    op.execute(
        """
        CREATE UNIQUE INDEX uq_episodes_content_group_lang_cms
        ON episodes (content_group, language)
        WHERE external_id IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_artwork_show_kind
        ON artwork (show_id, kind)
        WHERE show_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_artwork_episode_kind
        ON artwork (episode_id, kind)
        WHERE episode_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_artwork_episode_kind")
    op.execute("DROP INDEX IF EXISTS uq_artwork_show_kind")
    op.execute("DROP INDEX IF EXISTS uq_episodes_content_group_lang_cms")
    op.drop_index("idx_episodes_status_show", table_name="episodes")
    op.drop_index("idx_shows_status_section", table_name="shows")
