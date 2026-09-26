
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload
from app.db import get_db
from app.deps import current_user, optional_user
from app.models import Campus, Listing, User
from app.services.listings import listing_output
from app.services.recommendations import recommend

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("")
async def recommendations(campus_slug: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug))
    if not campus: raise HTTPException(404, "Campus not found")
    rows = await recommend(db, campus.id, user.id if user else None)
    items = []
    for row in rows:
        listing = db.scalar(select(Listing).options(joinedload(Listing.campus), joinedload(Listing.seller), selectinload(Listing.images))
                            .where(Listing.id == row["listing"].id))
        items.append({"listing": await listing_output(listing), "score": row["score"], "reason": row["reason"]})
    return {"items": items}

@router.get("/bundles")
async def bundles(campus_slug: str, user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug))
    if not campus: raise HTTPException(404, "Campus not found")
    listings = db.scalars(select(Listing).options(joinedload(Listing.campus), joinedload(Listing.seller), selectinload(Listing.images))
                          .where(Listing.campus_id == campus.id, Listing.status == "active").order_by(Listing.favorites.desc()).limit(30)).all()
    groups = {}
    for item in listings:
        groups.setdefault(item.category.lower(), []).append(item)
    result = []
    for cat, items in groups.items():
        if len(items) >= 2:
            selected = items[:3]
            result.append({"name": f"{cat.title()} bundle", "category": cat, "items": [await listing_output(x) for x in selected],
                           "total": round(sum(float(x.price) for x in selected), 2)})
    return result[:8]
