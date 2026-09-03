from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from app.models import Episode, PublishRun, Season, Show
from app.playback import video_for_episode, video_for_show
from app.reference import SECTION_LABELS, SECTIONS, TRAILER_SEASON
from app.schemas import ValidationReport
from app.services.validation import build_validation_report
from app.storage import get_storage

LIVE_KEY = "catalogues/catalogue.json"
POINTER_KEY = "catalogues/current.json"
# Session-level lock so concurrent POSTs serialize across commits.
PUBLISH_LOCK_KEY = 81422901


def _url(key: str) -> str:
    return get_storage().url(key)


def _art_urls(records) -> dict[str, str]:
    return {a.kind: _url(a.storage_key) for a in records}


def build_catalogue_payload(db: Session, run_id: uuid.UUID) -> tuple[dict, int, int]:
    shows = db.scalars(
        select(Show)
        .where(Show.status == "published")
        .options(
            selectinload(Show.artwork),
            selectinload(Show.seasons).selectinload(Season.episodes),
        )
        .order_by(Show.title)
    ).all()

    episodes = db.scalars(
        select(Episode)
        .where(Episode.status == "published")
        .options(selectinload(Episode.artwork), selectinload(Episode.season))
        .order_by(Episode.content_group, Episode.language, Episode.external_id)
    ).all()

    seen_group_lang: set[tuple[str, str]] = set()
    episodes_by_show: dict[uuid.UUID, list[Episode]] = defaultdict(list)
    for ep in episodes:
        if not ep.artwork or not ep.duration_seconds:
            continue
        key = (ep.content_group, ep.language)
        if key in seen_group_lang:
            continue
        seen_group_lang.add(key)
        episodes_by_show[ep.show_id].append(ep)

    by_section: dict[str, list[dict]] = {s: [] for s in SECTIONS}
    show_count = 0
    grouped_episode_count = 0

    for show in shows:
        if show.section not in SECTIONS:
            continue
        show_eps = episodes_by_show.get(show.id, [])
        if not show_eps:
            continue

        seasons_map: dict[int, dict[str, list[Episode]]] = defaultdict(lambda: defaultdict(list))
        for ep in show_eps:
            seasons_map[ep.season.number][ep.content_group].append(ep)

        season_payloads = []
        trailers = []
        for season_number in sorted(seasons_map):
            groups = seasons_map[season_number]
            entries = []
            for content_group in sorted(groups):
                variants = sorted(groups[content_group], key=lambda e: e.language)
                primary = variants[0]
                playback = video_for_episode(content_group)
                entry = {
                    "content_group": content_group,
                    "title": primary.title,
                    "titles_by_language": {v.language: v.title for v in variants},
                    "episode_number": primary.number,
                    "duration_seconds": primary.duration_seconds,
                    "languages": [v.language for v in variants],
                    "artwork": _merge_episode_art(variants, show),
                    "playback_url": playback,
                    "playback_by_language": {v.language: playback for v in variants},
                }
                grouped_episode_count += 1
                entries.append(entry)
            entries.sort(key=lambda e: (e["episode_number"], e["title"]))
            block = {"number": season_number, "episodes": entries}
            if season_number == TRAILER_SEASON:
                trailers = entries
            else:
                season_payloads.append(block)

        show_count += 1
        by_section[show.section].append(
            {
                "id": str(show.id),
                "slug": show.slug,
                "title": show.title,
                "synopsis": show.synopsis,
                "categories": list(show.categories or []),
                "section": show.section,
                "artwork": _art_urls(show.artwork),
                "playback_url": video_for_show(show.slug),
                "seasons": season_payloads,
                "trailers": trailers,
            }
        )

    for section in by_section:
        by_section[section].sort(key=lambda s: s["title"].lower())

    payload = {
        "published_at": datetime.now(UTC).isoformat(),
        "run_id": str(run_id),
        "sections": [
            {
                "id": section,
                "title": SECTION_LABELS[section],
                "shows": by_section[section],
            }
            for section in SECTIONS
        ],
    }
    return payload, show_count, grouped_episode_count


def _merge_episode_art(variants: list[Episode], show: Show) -> dict[str, str]:
    merged: dict[str, str] = {}
    for ep in variants:
        merged.update(_art_urls(ep.artwork))
    # Fall back to show-level art so a thumbnail-only trailer still has a poster.
    for kind, url in _art_urls(show.artwork).items():
        merged.setdefault(kind, url)
    return merged


def _content_hash(payload: dict) -> str:
    canonical = {k: payload[k] for k in payload if k not in ("published_at", "run_id")}
    blob = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def publish_catalogue(db: Session, actor_email: str) -> PublishRun:
    db.execute(text("SELECT pg_advisory_lock(:k)"), {"k": PUBLISH_LOCK_KEY})
    live_replaced = False
    try:
        report: ValidationReport = build_validation_report(db)
        run = PublishRun(actor_email=actor_email, outcome="started")
        db.add(run)
        db.commit()
        db.refresh(run)

        if not report.can_publish:
            run.outcome = "blocked"
            run.finished_at = datetime.now(UTC)
            run.error = "Publish blocked by validation. Fix the items on the validation report first."
            run.notes = {"blocking": [i.model_dump(mode="json") for i in report.blocking]}
            db.commit()
            db.refresh(run)
            return run

        storage = get_storage()
        try:
            payload, show_count, episode_count = build_catalogue_payload(db, run.id)
            digest = _content_hash(payload)
            previous = db.scalar(
                select(PublishRun)
                .where(PublishRun.outcome == "success", PublishRun.id != run.id)
                .order_by(PublishRun.started_at.desc())
            )
            if previous and (previous.notes or {}).get("content_hash") == digest and previous.catalogue_key:
                run.outcome = "success"
                run.show_count = previous.show_count
                run.episode_count = previous.episode_count
                run.catalogue_key = previous.catalogue_key
                run.finished_at = datetime.now(UTC)
                run.notes = {
                    "idempotent": True,
                    "reused_run": str(previous.id),
                    "content_hash": digest,
                    "live_key": LIVE_KEY,
                }
                db.commit()
                db.refresh(run)
                return run

            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            version_key = f"catalogues/{run.id}.json"
            # 1. Versioned object first. A crash here leaves the live file untouched.
            storage.put(version_key, body, "application/json")
            # 2. Atomic replace of the live file. Readers see the previous full file or this one.
            storage.put_atomic(LIVE_KEY, body, "application/json")
            live_replaced = True
            pointer = json.dumps({"run_id": str(run.id), "key": version_key}).encode()
            storage.put_atomic(POINTER_KEY, pointer, "application/json")

            run.outcome = "success"
            run.show_count = show_count
            run.episode_count = episode_count
            run.catalogue_key = version_key
            run.finished_at = datetime.now(UTC)
            run.notes = {"live_key": LIVE_KEY, "content_hash": digest}
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:  # noqa: BLE001 — record and re-raise as failed run
            # If the live file already flipped, kids have the new catalogue. Call it success
            # so the run history matches what readers see.
            run.outcome = "success" if live_replaced else "failed"
            run.finished_at = datetime.now(UTC)
            run.error = None if live_replaced else str(exc)
            if live_replaced:
                run.notes = {"live_key": LIVE_KEY, "pointer_write": "failed", "error": str(exc)}
            db.commit()
            db.refresh(run)
            if live_replaced:
                return run
            raise
    finally:
        db.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": PUBLISH_LOCK_KEY})
        db.commit()


def read_live_catalogue() -> dict:
    storage = get_storage()
    if not storage.exists(LIVE_KEY):
        return {"published_at": None, "run_id": None, "sections": []}
    return json.loads(storage.get(LIVE_KEY))


def search_catalogue(
    catalogue: dict,
    q: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
) -> dict:
    """In-memory filter over the published file. Filters AND together.

    q matches show title, episode title, and category (case-insensitive substring).
    """
    needle = (q or "").strip().lower()
    matches: list[dict] = []

    for sec in catalogue.get("sections", []):
        if section and sec["id"] != section:
            continue
        for show in sec.get("shows", []):
            if category and category not in (show.get("categories") or []):
                continue
            show_hit = True
            if needle:
                in_title = needle in show["title"].lower()
                in_cat = any(needle in c.lower() for c in show.get("categories") or [])
                in_ep = False
                for season in show.get("seasons", []):
                    for ep in season.get("episodes", []):
                        titles = [ep.get("title") or "", * (ep.get("titles_by_language") or {}).values()]
                        if any(needle in t.lower() for t in titles):
                            in_ep = True
                            break
                    if in_ep:
                        break
                for ep in show.get("trailers") or []:
                    titles = [ep.get("title") or "", * (ep.get("titles_by_language") or {}).values()]
                    if any(needle in t.lower() for t in titles):
                        in_ep = True
                        break
                show_hit = in_title or in_cat or in_ep
            if not show_hit:
                continue
            if language:
                langs = set()
                for season in show.get("seasons", []):
                    for ep in season.get("episodes", []):
                        langs.update(ep.get("languages") or [])
                for ep in show.get("trailers") or []:
                    langs.update(ep.get("languages") or [])
                if language not in langs:
                    continue
            matches.append(show)

    return {"q": q, "category": category, "language": language, "section": section, "results": matches}
