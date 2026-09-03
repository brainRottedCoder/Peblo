from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_editor
from app.models import Episode, Season, Show, User
from app.reference import CATEGORIES, LANGUAGES, SECTIONS, STATUSES
from app.schemas import (
    EpisodeIn,
    EpisodeOut,
    EpisodeUpdate,
    SeasonIn,
    SeasonOut,
    ShowDetailOut,
    ShowIn,
    ShowListOut,
    ShowOut,
    ShowUpdate,
)
from app.serialize import episode_out, season_out, show_detail, show_out

router = APIRouter(prefix="/admin", tags=["admin-content"])


def _load_show(db: Session, show_id: uuid.UUID) -> Show:
    show = db.scalar(
        select(Show)
        .where(Show.id == show_id)
        .options(
            selectinload(Show.artwork),
            selectinload(Show.seasons).selectinload(Season.episodes).selectinload(Episode.artwork),
        )
    )
    if show is None:
        raise HTTPException(404, "We couldn't find that show.")
    return show


def _assert_enum(value: str | None, allowed: tuple[str, ...], label: str) -> None:
    if value is None:
        return
    if value not in allowed:
        pretty = ", ".join(allowed)
        raise HTTPException(422, f"{label} must be one of: {pretty}.")


def _assert_publish_episode(ep: Episode) -> None:
    if ep.status != "published":
        return
    if ep.duration_seconds is None or ep.duration_seconds <= 0:
        raise HTTPException(
            422,
            "An episode needs a duration (in seconds) before you can publish it.",
        )
    if not ep.artwork:
        raise HTTPException(
            422,
            "An episode needs at least one picture (a thumbnail is enough) before you can publish it.",
        )


def _assert_unique_group(db: Session, content_group: str, language: str, exclude_id: uuid.UUID | None) -> None:
    q = select(Episode).where(Episode.content_group == content_group, Episode.language == language)
    if exclude_id:
        q = q.where(Episode.id != exclude_id)
    existing = db.scalar(q)
    if existing is not None:
        raise HTTPException(
            422,
            f"There’s already a {language.upper()} version in content group “{content_group}”. "
            "Use a different content group, or a different language.",
        )


@router.get("/shows", response_model=ShowListOut)
def list_shows(
    q: str | None = None,
    section: str | None = None,
    status: str | None = None,
    language: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> ShowListOut:
    stmt = select(Show).options(selectinload(Show.artwork), selectinload(Show.seasons).selectinload(Season.episodes))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Show.title.ilike(like), Show.slug.ilike(like)))
    if section:
        stmt = stmt.where(Show.section == section)
    if status:
        stmt = stmt.where(Show.status == status)
    if language:
        stmt = stmt.where(
            Show.id.in_(select(Episode.show_id).where(Episode.language == language).distinct())
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Show.title).offset((page - 1) * page_size).limit(page_size)).all()
    return ShowListOut(
        items=[show_out(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/shows", response_model=ShowOut, status_code=201)
def create_show(body: ShowIn, db: Session = Depends(get_db), _: User = Depends(require_editor)) -> ShowOut:
    _assert_enum(body.section, SECTIONS, "Section")
    _assert_enum(body.status, STATUSES, "Status")
    for cat in body.categories:
        _assert_enum(cat, CATEGORIES, "Category")
    if body.status == "published" and not body.section:
        raise HTTPException(422, "A published show needs a section (Featured, Series, Minisodes, or Songs).")
    if db.scalar(select(Show).where(Show.slug == body.slug)):
        raise HTTPException(422, f"A show with the web name “{body.slug}” already exists.")
    show = Show(
        title=body.title,
        slug=body.slug,
        synopsis=body.synopsis,
        section=body.section,
        categories=body.categories,
        status=body.status,
    )
    db.add(show)
    db.commit()
    db.refresh(show)
    return show_out(_load_show(db, show.id))


@router.get("/shows/{show_id}", response_model=ShowDetailOut)
def get_show(show_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_editor)) -> ShowDetailOut:
    return show_detail(_load_show(db, show_id))


@router.patch("/shows/{show_id}", response_model=ShowDetailOut)
def update_show(
    show_id: uuid.UUID,
    body: ShowUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> ShowDetailOut:
    show = _load_show(db, show_id)
    data = body.model_dump(exclude_unset=True)
    if "section" in data:
        _assert_enum(data["section"], SECTIONS, "Section")
    if "status" in data:
        _assert_enum(data["status"], STATUSES, "Status")
    if "categories" in data:
        for cat in data["categories"] or []:
            _assert_enum(cat, CATEGORIES, "Category")
    if "slug" in data and data["slug"] != show.slug:
        if db.scalar(select(Show).where(Show.slug == data["slug"])):
            raise HTTPException(422, f"A show with the web name “{data['slug']}” already exists.")
    for key, value in data.items():
        setattr(show, key, value)
    if show.status == "published" and not show.section:
        raise HTTPException(422, "A published show needs a section (Featured, Series, Minisodes, or Songs).")
    db.commit()
    return show_detail(_load_show(db, show.id))


@router.delete("/shows/{show_id}")
def delete_show(show_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_editor)) -> Response:
    show = db.get(Show, show_id)
    if show is None:
        raise HTTPException(404, "We couldn't find that show.")
    db.delete(show)
    db.commit()
    return Response(status_code=204)


@router.post("/shows/{show_id}/seasons", response_model=SeasonOut, status_code=201)
def create_season(
    show_id: uuid.UUID,
    body: SeasonIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> SeasonOut:
    show = db.get(Show, show_id)
    if show is None:
        raise HTTPException(404, "We couldn't find that show.")
    if db.scalar(select(Season).where(Season.show_id == show_id, Season.number == body.number)):
        raise HTTPException(422, f"Season {body.number} already exists for this show.")
    season = Season(show_id=show_id, number=body.number)
    db.add(season)
    db.commit()
    db.refresh(season)
    season.episodes = []
    return season_out(season)


@router.delete("/seasons/{season_id}")
def delete_season(season_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_editor)) -> Response:
    season = db.get(Season, season_id)
    if season is None:
        raise HTTPException(404, "We couldn't find that season.")
    db.delete(season)
    db.commit()
    return Response(status_code=204)


@router.post("/seasons/{season_id}/episodes", response_model=EpisodeOut, status_code=201)
def create_episode(
    season_id: uuid.UUID,
    body: EpisodeIn,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> EpisodeOut:
    season = db.get(Season, season_id)
    if season is None:
        raise HTTPException(404, "We couldn't find that season.")
    _assert_enum(body.language, LANGUAGES, "Language")
    _assert_enum(body.status, STATUSES, "Status")
    _assert_unique_group(db, body.content_group, body.language, None)
    ep = Episode(
        season_id=season.id,
        show_id=season.show_id,
        title=body.title,
        number=body.number,
        duration_seconds=body.duration_seconds,
        language=body.language,
        content_group=body.content_group,
        status=body.status,
    )
    db.add(ep)
    try:
        db.flush()
        _assert_publish_episode(ep)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            422,
            f"There’s already a {body.language.upper()} version in content group “{body.content_group}”. "
            "Use a different content group, or a different language.",
        ) from None
    db.refresh(ep)
    ep.artwork = []
    return episode_out(ep)


@router.patch("/episodes/{episode_id}", response_model=EpisodeOut)
def update_episode(
    episode_id: uuid.UUID,
    body: EpisodeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> EpisodeOut:
    ep = db.scalar(select(Episode).where(Episode.id == episode_id).options(selectinload(Episode.artwork)))
    if ep is None:
        raise HTTPException(404, "We couldn't find that episode.")
    data = body.model_dump(exclude_unset=True)
    if "language" in data:
        _assert_enum(data["language"], LANGUAGES, "Language")
    if "status" in data:
        _assert_enum(data["status"], STATUSES, "Status")
    next_group = data.get("content_group", ep.content_group)
    next_lang = data.get("language", ep.language)
    if next_group != ep.content_group or next_lang != ep.language:
        _assert_unique_group(db, next_group, next_lang, ep.id)
    for key, value in data.items():
        setattr(ep, key, value)
    try:
        _assert_publish_episode(ep)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            422,
            f"There’s already a {next_lang.upper()} version in content group “{next_group}”. "
            "Use a different content group, or a different language.",
        ) from None
    db.refresh(ep)
    return episode_out(ep)


@router.delete("/episodes/{episode_id}")
def delete_episode(episode_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_editor)) -> Response:
    ep = db.get(Episode, episode_id)
    if ep is None:
        raise HTTPException(404, "We couldn't find that episode.")
    db.delete(ep)
    db.commit()
    return Response(status_code=204)
