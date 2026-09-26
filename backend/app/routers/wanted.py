from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, optional_user, require_verified_member
from app.models import Campus, Listing, WantedMatch, WantedPost, User
from app.schemas import WantedCreateIn
from app.services.audit import record as audit_record
from app.services.matching import refresh_wanted_matches_for_post, score_wanted_post

router = APIRouter(prefix="/api/wanted", tags=["wanted"])


def out(post: WantedPost, user: User | None = None):
    return {
        "id": post.id,
        "campus_slug": post.campus.slug if post.campus else None,
        "title": post.title,
        "category": post.category,
        "description": post.description,
        "budget_min": post.budget_min,
        "budget_max": post.budget_max,
        "needed_by": post.needed_by,
        "status": post.status,
        "owner_id": post.user_id,
        "is_owner": bool(user and post.user_id == user.id),
        "created_at": post.created_at,
    }


@router.post("")
def create_wanted(data: WantedCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    campus, _ = require_verified_member(data.campus_slug, user, db)
    post = WantedPost(campus_id=campus.id, user_id=user.id, **data.model_dump(exclude={"campus_slug"}))
    db.add(post)
    db.flush()
    refresh_wanted_matches_for_post(db, post)
    db.commit()
    db.refresh(post)
    return out(post)


@router.get("")
def list_wanted(campus_slug: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug, Campus.active.is_(True)))
    if not campus:
        raise HTTPException(404, "Campus not found")
    posts = db.scalars(
        select(WantedPost)
        .where(WantedPost.campus_id == campus.id, WantedPost.status == "open")
        .order_by(desc(WantedPost.created_at))
    ).all()
    return [out(post, user) for post in posts]


@router.get("/{wanted_id}/matches")
def wanted_matches(wanted_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(WantedPost, wanted_id)
    if not post:
        raise HTTPException(404, "Wanted post not found")
    if post.user_id != user.id:
        raise HTTPException(403, "Only the author can view match alerts")

    results = refresh_wanted_matches_for_post(db, post)
    db.commit()
    return results[:30]


@router.get("/{wanted_id}")
def wanted_detail(wanted_id: int, db: Session = Depends(get_db)):
    post = db.get(WantedPost, wanted_id)
    if not post:
        raise HTTPException(404, "Wanted post not found")
    return out(post)


@router.post("/{wanted_id}/close")
def close_wanted(wanted_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    post = db.get(WantedPost, wanted_id)
    if not post or post.user_id != user.id:
        raise HTTPException(404, "Wanted post not found")
    post.status = "closed"
    audit_record(db, user.id, "wanted.closed", "wanted_post", post.id)
    db.commit()
    return {"id": post.id, "status": post.status}
