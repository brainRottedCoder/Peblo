from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db import SessionLocal
from app.storage import get_storage

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        get_storage().healthcheck()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(503, f"Not ready: {exc}") from exc
    return {"status": "ready"}
