from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import get_db
from app.deps import current_user
from app.models import Favorite, InteractionEvent, Listing, User
from app.services.listings import listing_output

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
async def list_favorites(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .options(
            joinedload(Listing.campus),
            joinedload(Listing.seller),
            selectinload(Listing.images),
        )
        .where(Favorite.user_id == user.id)
        .order_by(desc(Favorite.created_at))
    ).all()
    return [await listing_output(item) for item in rows]


@router.get("/ids")
def favorite_ids(user: User = Depends(current_user), db: Session = Depends(get_db)):
    ids = db.scalars(select(Favorite.listing_id).where(Favorite.user_id == user.id)).all()
    return {"listing_ids": list(ids)}


@router.post("/{listing_id}")
def add_favorite(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.seller.user_id == user.id:
        raise HTTPException(400, "You cannot save your own listing")
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
    )
    if existing:
        return {"saved": True, "favorites": listing.favorites}
    db.add(Favorite(user_id=user.id, listing_id=listing_id))
    listing.favorites += 1
    db.add(
        InteractionEvent(
            user_id=user.id,
            campus_id=listing.campus_id,
            listing_id=listing.id,
            event_type="favorite",
            category=listing.category,
        )
    )
    db.commit()
    return {"saved": True, "favorites": listing.favorites}


@router.delete("/{listing_id}")
def remove_favorite(listing_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    existing = db.scalar(
        select(Favorite).where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
    )
    if not existing:
        return {"saved": False, "favorites": listing.favorites}
    db.delete(existing)
    listing.favorites = max(0, listing.favorites - 1)
    db.add(
        InteractionEvent(
            user_id=user.id,
            campus_id=listing.campus_id,
            listing_id=listing.id,
            event_type="unfavorite",
            category=listing.category,
        )
    )
    db.commit()
    return {"saved": False, "favorites": listing.favorites}
