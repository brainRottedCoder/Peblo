from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginRequest, TokenResponse
from app.security import create_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower().strip()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is wrong.")
    return TokenResponse(
        access_token=create_token(str(user.id), user.email, user.role),
        role=user.role,
        email=user.email,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"email": user.email, "role": user.role, "id": str(user.id)}
