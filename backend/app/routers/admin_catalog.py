from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import require_admin, require_editor
from app.models import PublishRun, User
from app.schemas import PublishRunOut, ValidationReport
from app.services.catalog import publish_catalogue
from app.services.validation import build_validation_report

router = APIRouter(prefix="/admin", tags=["admin-catalog"])


@router.get("/validation-report", response_model=ValidationReport)
def validation_report(db: Session = Depends(get_db), _: User = Depends(require_editor)) -> ValidationReport:
    return build_validation_report(db)


@router.get("/catalog/publish-runs", response_model=list[PublishRunOut])
def list_runs(db: Session = Depends(get_db), _: User = Depends(require_editor)) -> list[PublishRun]:
    return list(db.scalars(select(PublishRun).order_by(PublishRun.started_at.desc()).limit(50)).all())


@router.post("/catalog/publish", response_model=PublishRunOut)
def publish(db: Session = Depends(get_db), user: User = Depends(require_admin)) -> PublishRun:
    return publish_catalogue(db, user.email)


@router.get("/reference")
def reference(_: User = Depends(require_editor)) -> dict:
    from app.reference import load_reference

    return load_reference()
