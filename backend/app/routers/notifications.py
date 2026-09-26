from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Notification, User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

CATEGORY_KINDS = {
    "messages": {"message"},
    "offers": {"offer"},
    "transactions": {"payment", "payment_failed", "refund", "pickup", "transaction"},
    "swaps": {"swap"},
    "wanted": {"wanted_match"},
}


def out(n: Notification):
    return {
        "id": n.id,
        "kind": n.kind,
        "title": n.title,
        "body": n.body,
        "link": n.link,
        "read": n.read_at is not None,
        "created_at": n.created_at,
    }


@router.get("")
def notifications(
    category: str = Query(default="all"),
    unread_only: bool = False,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    q = select(Notification).where(Notification.user_id == user.id)
    category = category.strip().lower()
    if category != "all":
        kinds = CATEGORY_KINDS.get(category)
        if not kinds:
            raise HTTPException(400, "Unknown notification category")
        q = q.where(Notification.kind.in_(kinds))
    if unread_only:
        q = q.where(Notification.read_at.is_(None))
    rows = db.scalars(q.order_by(desc(Notification.created_at)).limit(100)).all()
    return [out(n) for n in rows]


@router.get("/unread-count")
def unread_count(user: User = Depends(current_user), db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id,
            Notification.read_at.is_(None),
        )
    ) or 0
    by_category = {}
    for category, kinds in CATEGORY_KINDS.items():
        by_category[category] = db.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user.id,
                Notification.read_at.is_(None),
                Notification.kind.in_(kinds),
            )
        ) or 0
    return {"total": total, "by_category": by_category}


@router.post("/{notification_id}/read")
def read(notification_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:
        raise HTTPException(404, "Notification not found")
    n.read_at = datetime.utcnow()
    db.commit()
    return {"ok": True}


@router.post("/read-all")
def read_all(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.read_at.is_(None),
    ).update({Notification.read_at: datetime.utcnow()}, synchronize_session=False)
    db.commit()
    return {"ok": True}
