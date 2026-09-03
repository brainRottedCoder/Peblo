from __future__ import annotations

from app.models import Artwork, Episode, Season, Show
from app.schemas import ArtworkOut, EpisodeOut, SeasonOut, ShowDetailOut, ShowOut
from app.storage import get_storage


def artwork_out(a: Artwork) -> ArtworkOut:
    return ArtworkOut(
        id=a.id,
        kind=a.kind,
        url=get_storage().url(a.storage_key),
        width=a.width,
        height=a.height,
        byte_size=a.byte_size,
    )


def episode_out(ep: Episode) -> EpisodeOut:
    return EpisodeOut(
        id=ep.id,
        season_id=ep.season_id,
        show_id=ep.show_id,
        external_id=ep.external_id,
        title=ep.title,
        number=ep.number,
        duration_seconds=ep.duration_seconds,
        language=ep.language,
        content_group=ep.content_group,
        status=ep.status,
        artwork=[artwork_out(a) for a in ep.artwork],
    )


def season_out(season: Season, include_episodes: bool = True) -> SeasonOut:
    return SeasonOut(
        id=season.id,
        show_id=season.show_id,
        number=season.number,
        episode_count=len(season.episodes),
        episodes=[episode_out(e) for e in season.episodes] if include_episodes else [],
    )


def show_out(show: Show) -> ShowOut:
    episode_count = sum(len(s.episodes) for s in show.seasons) if show.seasons else 0
    return ShowOut(
        id=show.id,
        title=show.title,
        slug=show.slug,
        synopsis=show.synopsis,
        section=show.section,
        categories=list(show.categories or []),
        status=show.status,
        episode_count=episode_count,
        artwork=[artwork_out(a) for a in show.artwork],
    )


def show_detail(show: Show) -> ShowDetailOut:
    base = show_out(show)
    return ShowDetailOut(
        **base.model_dump(),
        seasons=[season_out(s) for s in sorted(show.seasons, key=lambda x: x.number)],
    )
