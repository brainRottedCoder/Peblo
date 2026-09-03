from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def require_bearer(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> HTTPAuthorizationCredentials:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in to continue.")
    return creds


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(require_bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(creds.credentials)
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in to continue.")
    return user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("editor", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You need an editor account for this.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only an admin can publish the catalogue. Ask an admin, or sign in with the admin account.",
        )
    return user
