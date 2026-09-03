from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_editor
from app.models import Artwork, Episode, Show, User
from app.reference import ARTWORK_KINDS
from app.schemas import ArtworkOut
from app.serialize import artwork_out
from app.services.artwork import ArtworkError, validate_artwork
from app.storage import get_storage

router = APIRouter(prefix="/admin", tags=["admin-artwork"])


@router.post("/shows/{show_id}/artwork", response_model=ArtworkOut)
async def upload_show_artwork(
    show_id: uuid.UUID,
    kind: str = Form(...),
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> ArtworkOut:
    show = db.get(Show, show_id)
    if show is None:
        raise HTTPException(404, "We couldn't find that show.")
    return _save(db, kind, file, show_id=show.id)


@router.post("/episodes/{episode_id}/artwork", response_model=ArtworkOut)
async def upload_episode_artwork(
    episode_id: uuid.UUID,
    kind: str = Form(...),
    file: UploadFile | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> ArtworkOut:
    ep = db.get(Episode, episode_id)
    if ep is None:
        raise HTTPException(404, "We couldn't find that episode.")
    return _save(db, kind, file, episode_id=ep.id)


def _save(
    db: Session,
    kind: str,
    file: UploadFile | None,
    show_id: uuid.UUID | None = None,
    episode_id: uuid.UUID | None = None,
) -> ArtworkOut:
    if kind not in ARTWORK_KINDS:
        raise HTTPException(422, "Picture type must be poster, banner, or thumbnail.")
    if file is None:
        raise HTTPException(422, "Please choose a picture to upload.")
    data = file.file.read()
    if not data:
        raise HTTPException(422, "That file is empty. Please pick another picture.")
    try:
        ok = validate_artwork(kind, data)
    except ArtworkError as exc:
        raise HTTPException(422, exc.message) from exc

    owner = f"shows/{show_id}" if show_id else f"episodes/{episode_id}"
    ext = "png" if ok.content_type == "image/png" else "jpg"
    key = f"artwork/{owner}/{kind}.{ext}"
    storage = get_storage()
    storage.put(key, data, ok.content_type)

    q = select(Artwork).where(Artwork.kind == kind)
    q = q.where(Artwork.show_id == show_id) if show_id else q.where(Artwork.episode_id == episode_id)
    existing = db.scalar(q)
    if existing:
        existing.storage_key = key
        existing.width = ok.width
        existing.height = ok.height
        existing.byte_size = len(data)
        existing.content_type = ok.content_type
        db.commit()
        db.refresh(existing)
        return artwork_out(existing)

    art = Artwork(
        kind=kind,
        storage_key=key,
        width=ok.width,
        height=ok.height,
        byte_size=len(data),
        content_type=ok.content_type,
        show_id=show_id,
        episode_id=episode_id,
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return artwork_out(art)
