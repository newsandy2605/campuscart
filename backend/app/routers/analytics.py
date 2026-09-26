
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user
from app.models import Listing, Offer, Transaction, SellerProfile, User, InteractionEvent

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/seller")
def seller_analytics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    seller = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if not seller: raise HTTPException(404, "Seller profile not found")
    listings = db.scalars(select(Listing).where(Listing.seller_id == seller.id)).all()
    offers = db.scalar(select(func.count()).select_from(Offer).where(Offer.seller_id == user.id)) or 0
    return {"estimated_sales": round(sum(float(x.price) for x in listings if x.status in {"active", "reserved", "completed"}), 2),
            "active_listings": sum(x.status == "active" for x in listings), "offers": offers,
            "views": sum(x.views for x in listings), "saves": sum(x.favorites for x in listings),
            "shares": sum(x.share_count for x in listings), "completed_orders": seller.completed_orders,
            "reputation_score": float(seller.reputation_score)}

@router.get("/campus")
def campus_analytics(campus_slug: str, db: Session = Depends(get_db)):
    from app.models import Campus, CampusMember
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug))
    if not campus: raise HTTPException(404, "Campus not found")
    return {"members": db.scalar(select(func.count()).select_from(CampusMember).where(CampusMember.campus_id == campus.id, CampusMember.verified.is_(True))) or 0,
            "active_listings": db.scalar(select(func.count()).select_from(Listing).where(Listing.campus_id == campus.id, Listing.status == "active")) or 0,
            "completed_transactions": db.scalar(select(func.count()).select_from(Transaction).join(Listing, Transaction.listing_id == Listing.id)
                                                .where(Listing.campus_id == campus.id, Transaction.status == "completed")) or 0,
            "total_traded": float(db.scalar(select(func.coalesce(func.sum(Transaction.agreed_price), 0)).join(Listing, Transaction.listing_id == Listing.id)
                                            .where(Listing.campus_id == campus.id, Transaction.status == "completed")) or 0)}
