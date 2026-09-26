from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Campus, CampusMember, User
from app.security import decode_token, is_token_revoked


def _read_bearer(authorization: str) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return token


def current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    token = _read_bearer(authorization)
    payload = decode_token(token)
    if is_token_revoked(payload):
        raise HTTPException(status_code=401, detail="Session has been logged out")
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token subject") from exc
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def optional_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization.startswith("Bearer "):
        return None
    try:
        token = _read_bearer(authorization)
        payload = decode_token(token)
        if is_token_revoked(payload):
            return None
        user = db.get(User, int(payload["sub"]))
        return user if user and user.active else None
    except Exception:
        return None


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_verified_member(campus_slug: str, user: User, db: Session):
    campus = db.scalar(
        select(Campus).where(Campus.slug == campus_slug, Campus.active.is_(True))
    )
    if not campus:
        raise HTTPException(status_code=404, detail="Campus not found")
    member = db.scalar(
        select(CampusMember).where(
            CampusMember.campus_id == campus.id,
            CampusMember.user_id == user.id,
        )
    )
    if not member or not member.verified:
        raise HTTPException(
            status_code=403,
            detail="Verified campus membership is required",
        )
    return campus, member
