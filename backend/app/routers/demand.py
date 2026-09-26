from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Campus, Listing, Transaction, User, WantedPost
from app.services.demand import demand_radar, price_insight

router = APIRouter(prefix="/api/demand", tags=["demand"])


def get_campus(campus_slug: str, db: Session):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug, Campus.active.is_(True)))
    if not campus:
        raise HTTPException(404, "Campus not found")
    return campus


@router.get("/radar")
def radar(campus_slug: str, db: Session = Depends(get_db)):
    campus = get_campus(campus_slug, db)
    return {"campus_slug": campus.slug, "items": demand_radar(db, campus.id)}


@router.get("/price-insight")
def price(campus_slug: str, category: str, db: Session = Depends(get_db)):
    campus = get_campus(campus_slug, db)
    return price_insight(db, campus.id, category)


@router.get("/pulse")
def pulse(campus_slug: str, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta

    campus = get_campus(campus_slug, db)
    active = db.scalar(
        select(func.count()).select_from(Listing).where(
            Listing.campus_id == campus.id,
            Listing.status == "active",
        )
    ) or 0
    wanted = db.scalar(
        select(func.count()).select_from(WantedPost).where(
            WantedPost.campus_id == campus.id,
            WantedPost.status == "open",
        )
    ) or 0
    new_listings = db.scalar(
        select(func.count()).select_from(Listing).where(
            Listing.campus_id == campus.id,
            Listing.status == "active",
            Listing.created_at >= datetime.utcnow() - timedelta(days=7),
        )
    ) or 0
    completed = db.scalar(
        select(func.count()).select_from(Transaction).join(
            Listing, Transaction.listing_id == Listing.id
        ).where(
            Listing.campus_id == campus.id,
            Transaction.status == "completed",
        )
    ) or 0
    traded = db.scalar(
        select(func.coalesce(func.sum(Transaction.agreed_price), 0)).join(
            Listing, Transaction.listing_id == Listing.id
        ).where(
            Listing.campus_id == campus.id,
            Transaction.status == "completed",
        )
    ) or 0
    return {
        "open_wanted_posts": wanted,
        "active_listings": active,
        "new_listings": new_listings,
        "students_looking": wanted,
        "completed_transactions": completed,
        "traded_value": float(traded),
    }
