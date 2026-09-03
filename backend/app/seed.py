from __future__ import annotations

import json
import sys
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import Artwork, Base, Episode, PublishRun, Season, Show, User
from app.reference import artwork_specs
from app.security import hash_password
from app.services.catalog import LIVE_KEY, POINTER_KEY, build_catalogue_payload
from app.storage import get_storage

COLOURS = {
    "motis-many-lives": (196, 92, 42),
    "tiny-tales-banyan-dadi": (46, 107, 72),
    "discover-india-with-moti": (36, 90, 120),
    "peblo-songs": (156, 64, 88),
    "peblo-songs-lyrical": (120, 72, 140),
    "curious-cubs": (200, 140, 40),
    "number-nest": (48, 110, 130),
    "rhyme-rangers": (80, 80, 120),
}


def _placeholder(kind: str, colour: tuple[int, int, int], label: str) -> bytes:
    w, h = artwork_specs()[kind]["target_px"]
    im = Image.new("RGB", (w, h), colour)
    draw = ImageDraw.Draw(im)
    draw.rectangle([12, 12, w - 13, h - 13], outline=(255, 255, 255), width=6)
    draw.text((24, 24), label[:40], fill=(255, 255, 255))
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=78)
    return buf.getvalue()


def _art_bytes(data_dir: Path, slug: str, kind: str, colour: tuple[int, int, int], label: str, index: int) -> bytes:
    show_file = data_dir / "show-art" / slug / f"{kind}.jpg"
    if kind == "thumbnail":
        thumbs = sorted((data_dir / "show-art" / "thumbs").glob("*.jpg"))
        if thumbs:
            return thumbs[index % len(thumbs)].read_bytes()
        thumb = data_dir / "show-art" / slug / "thumbnail.jpg"
        if thumb.exists():
            return thumb.read_bytes()
    if show_file.exists():
        return show_file.read_bytes()
    return _placeholder(kind, colour, label)


def seed(force: bool = False) -> None:
    settings = get_settings()
    Base.metadata.create_all(engine)
    storage = get_storage()
    data_path = Path(settings.data_dir) / "seed_shows.json"
    data_dir = Path(settings.data_dir)
    rows = json.loads(data_path.read_text(encoding="utf-8"))

    with SessionLocal() as db:
        existing = db.scalar(select(User).limit(1))
        if existing and not force:
            print("Already seeded. Pass --force to re-seed.")
            return
        if force:
            db.query(Artwork).delete()
            db.query(Episode).delete()
            db.query(Season).delete()
            db.query(Show).delete()
            db.query(PublishRun).delete()
            db.query(User).delete()
            db.commit()

        admin = User(
            email=settings.seed_admin_email,
            password_hash=hash_password(settings.seed_admin_password),
            role="admin",
        )
        editor = User(
            email=settings.seed_editor_email,
            password_hash=hash_password(settings.seed_editor_password),
            role="editor",
        )
        db.add_all([admin, editor])

        by_slug: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_slug[row["slug"]].append(row)

        for slug, eps in by_slug.items():
            first = eps[0]
            statuses = {e["status"] for e in eps}
            show_status = "published" if "published" in statuses else "draft"
            show = Show(
                title=first["show_title"],
                slug=slug,
                synopsis=first.get("synopsis") or "",
                section=first.get("section"),
                categories=first.get("categories") or [],
                status=show_status,
            )
            db.add(show)
            db.flush()

            seasons: dict[int, Season] = {}
            show_kinds_written: set[str] = set()
            colour = COLOURS.get(slug, (90, 90, 90))
            ep_index = 0

            for row in eps:
                num = row["season_number"]
                if num not in seasons:
                    season = Season(show_id=show.id, number=num)
                    db.add(season)
                    db.flush()
                    seasons[num] = season
                season = seasons[num]
                ep = Episode(
                    season_id=season.id,
                    show_id=show.id,
                    external_id=row["episode_id"],
                    title=row["episode_title"],
                    number=row["episode_number"],
                    duration_seconds=row.get("duration_seconds"),
                    language=row["language"],
                    content_group=row["content_group"],
                    status=row["status"],
                )
                db.add(ep)
                db.flush()

                for kind in row.get("artwork_available") or []:
                    blob = _art_bytes(data_dir, slug, kind, colour, f"{show.title}\n{ep.title}", ep_index)
                    owner = f"episodes/{ep.id}"
                    key = f"artwork/{owner}/{kind}.jpg"
                    storage.put(key, blob, "image/jpeg")
                    im = Image.open(BytesIO(blob))
                    db.add(
                        Artwork(
                            kind=kind,
                            storage_key=key,
                            width=im.size[0],
                            height=im.size[1],
                            byte_size=len(blob),
                            content_type="image/jpeg",
                            episode_id=ep.id,
                        )
                    )
                    if kind in ("poster", "banner", "thumbnail") and kind not in show_kinds_written:
                        skey = f"artwork/shows/{show.id}/{kind}.jpg"
                        show_blob = _art_bytes(data_dir, slug, kind, colour, show.title, 0)
                        storage.put(skey, show_blob, "image/jpeg")
                        sim = Image.open(BytesIO(show_blob))
                        db.add(
                            Artwork(
                                kind=kind,
                                storage_key=skey,
                                width=sim.size[0],
                                height=sim.size[1],
                                byte_size=len(show_blob),
                                content_type="image/jpeg",
                                show_id=show.id,
                            )
                        )
                        show_kinds_written.add(kind)
                ep_index += 1

        db.commit()
        print(f"Seeded {len(by_slug)} shows, {len(rows)} episodes, admin + editor users.")

        # Write a first catalogue from valid published rows so the viewer works
        # on `docker-compose up`. Admin publish stays blocked until seed defects
        # on the validation report are fixed.
        run_id = uuid.uuid4()
        payload, show_count, episode_count = build_catalogue_payload(db, run_id)
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
        version_key = f"catalogues/{run_id}.json"
        storage.put(version_key, body, "application/json")
        storage.put_atomic(LIVE_KEY, body, "application/json")
        storage.put_atomic(POINTER_KEY, json.dumps({"run_id": str(run_id), "key": version_key}).encode(), "application/json")
        db.add(
            PublishRun(
                id=run_id,
                actor_email="seed@local",
                outcome="success",
                show_count=show_count,
                episode_count=episode_count,
                catalogue_key=version_key,
                finished_at=datetime.now(UTC),
                notes={"bootstrap": True, "note": "Valid rows only. Admin publish still blocked until seed defects are fixed."},
            )
        )
        db.commit()
        print(f"Bootstrap catalogue written ({show_count} shows, {episode_count} grouped episodes).")


if __name__ == "__main__":
    seed(force="--force" in sys.argv)
